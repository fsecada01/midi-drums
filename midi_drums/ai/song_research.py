"""Spike: factual song-metadata lookup grounding for AI pattern generation.

**Status: experimental spike, opt-in only** — see
``claudedocs/design_song_research_grounding.md`` for the research this is
based on and the design rationale. Not wired into the default agent tool
list; enabled only when ``MIDI_DRUMS_ENABLE_SONG_RESEARCH=1`` is set (see
``midi_drums/ai/agents/pattern_agent.py``).

Deliberately **metadata-only**: this module fetches factual data (tempo,
genre tags, recording personnel, release date) about a named song from
MusicBrainz + AcousticBrainz. It never fetches, scrapes, or transcribes the
copyrighted recording's audio, lyrics, or drum notation — see the design
doc's "Copyright posture" section for why that line is drawn here (facts
are not independently copyrightable; a transcription of the performance
would be).

Fetched network content is parsed by this module's own fixed-schema code
only — it is never concatenated into an LLM's context or allowed to
influence tool calls. This follows OWASP LLM Top 10 guidance on treating
retrieved web content as untrusted data rather than instructions (design
doc section 3): the only thing that reaches the agent is the rendered
``SongFacts.as_prompt_fact_sheet()`` string, a fixed template over
already-validated fields.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

from loguru import logger

_USER_AGENT = "midi-drums/0.4 (+https://github.com/fsecada01/midi-drums)"
_MUSICBRAINZ_BASE = "https://musicbrainz.org/ws/2"
_ACOUSTICBRAINZ_BASE = "https://acousticbrainz.org"
# MusicBrainz's documented courtesy limit for unauthenticated clients.
_MIN_REQUEST_INTERVAL_SECONDS = 1.0

_last_request_at = 0.0


def _rate_limited_get(url: str, timeout: float = 20.0) -> dict | None:
    """GET a JSON endpoint, honoring MusicBrainz's 1-req/sec courtesy limit.

    Returns None (never raises) on any network/parse failure — a lookup
    miss must never break pattern generation, only leave facts unfilled.
    """
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < _MIN_REQUEST_INTERVAL_SECONDS:
        time.sleep(_MIN_REQUEST_INTERVAL_SECONDS - elapsed)

    request = urllib.request.Request(
        url,
        headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        ValueError,
    ) as exc:
        logger.warning(f"song_research: lookup failed for {url}: {exc}")
        return None
    finally:
        _last_request_at = time.monotonic()
    return data


@dataclass
class SongFacts:
    """Factual, source-attributed metadata about a real recording.

    Every field is best-effort and may be None/empty — callers must treat
    this as "whatever could be verified", never assume completeness.
    Deliberately holds no audio, lyrics, or notation fields — see module
    docstring.
    """

    title: str
    artist: str | None = None
    mbid: str | None = None
    first_release_date: str | None = None
    genres: list[str] = field(default_factory=list)
    drummer_personnel: list[str] = field(default_factory=list)
    tempo_bpm: float | None = None
    musical_key: str | None = None
    sources: list[str] = field(default_factory=list)

    def as_prompt_fact_sheet(self) -> str:
        """Render as a short, clearly-labeled fact block for the agent.

        Labeled VERIFIED so the model can prefer these fields over its own
        recollection for objective values (tempo/genre/date) while still
        using its own judgment for anything not covered here — see design
        doc section 2 (grounding vs. model judgment).
        """
        header = f"VERIFIED SONG FACTS for '{self.title}'"
        if self.artist:
            header += f" by {self.artist}"
        lines = [header + ":"]

        if self.first_release_date:
            lines.append(f"- Release date: {self.first_release_date}")
        if self.genres:
            lines.append(f"- Genre tags: {', '.join(self.genres)}")
        if self.drummer_personnel:
            lines.append(
                "- Drummer/percussion credits: "
                + ", ".join(self.drummer_personnel)
            )
        if self.tempo_bpm:
            lines.append(f"- Tempo: {self.tempo_bpm:.0f} BPM")
        if self.musical_key:
            lines.append(f"- Key: {self.musical_key}")

        if len(lines) == 1:
            lines.append(
                "- (no verified facts found — use your own musical "
                "judgment for genre/style/tempo)"
            )
        if self.sources:
            lines.append(f"Sources: {', '.join(self.sources)}")
        return "\n".join(lines)


def _best_release_date(
    releases: list[dict], prefer_official: bool
) -> str | None:
    """Earliest release date among ``releases``, optionally official-only.

    A search result's embedded ``releases`` list mixes studio releases
    with fan-made bootleg entries for a *different underlying recording*
    of the same song (a live bootleg is its own MusicBrainz recording,
    not an alternate release of the studio one) — bootleg-status releases
    tend to carry the bootleg compilation's date, not the song's original
    date, so they're excluded first when any non-bootleg date exists.
    """
    dates = [
        r["date"]
        for r in releases
        if r.get("date")
        and (not prefer_official or r.get("status") != "Bootleg")
    ]
    return min(dates) if dates else None


def _pick_best_candidate(recordings: list[dict]) -> dict:
    """Pick the recording candidate least likely to be a bootleg/live take.

    MusicBrainz's title+artist search often returns several recordings
    tied on relevance score — separate audio takes (studio, live bootleg,
    remaster) that all match the query text equally well. Live testing
    against a real song ("Headless Cross" by Black Sabbath) showed the
    naive top-1 result can be a fan-recorded 2018 bootleg rather than the
    1989 studio track, even though the correct candidate was present a
    few entries down with a "Promotion"/"Official" release attached.
    Prefer whichever candidate has an official-or-promotion release with
    the earliest date; fall back to MusicBrainz's own top-1 ranking when
    no candidate has one (e.g. an obscure song with only bootlegs
    indexed).
    """
    scored = []
    for recording in recordings:
        date = _best_release_date(
            recording.get("releases") or [], prefer_official=True
        )
        if date:
            scored.append((date, recording))
    if scored:
        return min(scored, key=lambda pair: pair[0])[1]
    return recordings[0]


def _search_recording_mbid(title: str, artist: str | None) -> dict | None:
    query_parts = [f'recording:"{title}"']
    if artist:
        query_parts.append(f'artist:"{artist}"')
    query = urllib.parse.quote(" AND ".join(query_parts))
    url = f"{_MUSICBRAINZ_BASE}/recording/?query={query}&fmt=json&limit=15"
    data = _rate_limited_get(url)
    if not data or not data.get("recordings"):
        return None
    return _pick_best_candidate(data["recordings"])


def _fetch_recording_detail(mbid: str) -> dict | None:
    url = (
        f"{_MUSICBRAINZ_BASE}/recording/{mbid}"
        "?inc=artist-credits+releases+tags+genres+artist-rels&fmt=json"
    )
    return _rate_limited_get(url)


def _fetch_acousticbrainz_lowlevel(mbid: str) -> dict | None:
    url = f"{_ACOUSTICBRAINZ_BASE}/api/v1/{mbid}/low-level"
    return _rate_limited_get(url)


def research_song(title: str, artist: str | None = None) -> SongFacts:
    """Look up verifiable metadata for a real, named song.

    Metadata-only by design (see module docstring): never returns lyrics,
    drum notation, or any transcription of the copyrighted recording
    itself — only facts (tempo, genre tags, personnel, release date) that
    are not independently copyrightable (Feist Publications v. Rural
    Telephone).

    Never raises — a total lookup failure returns a SongFacts with only
    ``title``/``artist`` populated, so callers always get a usable object
    and a fact sheet that says as much.
    """
    facts = SongFacts(title=title, artist=artist)

    summary = _search_recording_mbid(title, artist)
    if summary is None:
        logger.info(f"song_research: no MusicBrainz match for '{title}'")
        return facts

    mbid = summary.get("id")
    facts.mbid = mbid
    if mbid:
        facts.sources.append(f"https://musicbrainz.org/recording/{mbid}")

    detail = _fetch_recording_detail(mbid) if mbid else None
    if detail:
        releases = detail.get("releases") or []

        artist_credit = (
            detail.get("artist-credit")
            or (releases[0].get("artist-credit") if releases else None)
            or []
        )
        if artist_credit and not facts.artist:
            facts.artist = artist_credit[0].get("name")

        # MusicBrainz exposes a convenience "first-release-date" on the
        # recording itself, but for a bootleg-heavy candidate (see
        # _pick_best_candidate) that field reflects *this* release, not
        # the song's earliest one - re-derive from the official/promo
        # releases when any exist, same rule used to pick the candidate.
        facts.first_release_date = _best_release_date(
            releases, prefer_official=True
        ) or detail.get("first-release-date")

        # Genre folksonomy tags live on the *artist* object nested inside
        # each release's artist-credit, not on the recording itself -
        # recording-level genres/tags are frequently empty even when the
        # artist has well-populated genre tags (observed live for
        # Black Sabbath's "Headless Cross").
        genre_entries = list(detail.get("genres") or detail.get("tags") or [])
        if not genre_entries:
            for release in releases:
                for credit in release.get("artist-credit") or []:
                    artist_obj = credit.get("artist") or {}
                    genre_entries.extend(artist_obj.get("genres") or [])
        facts.genres = sorted(
            {g["name"] for g in genre_entries if g.get("name")}
        )[:8]

        for relation in detail.get("relations") or []:
            role = (relation.get("type") or "").lower()
            attributes = " ".join(relation.get("attributes") or []).lower()
            if (
                "drum" in role
                or "drum" in attributes
                or ("percussion" in attributes)
            ):
                artist_name = (relation.get("artist") or {}).get("name")
                if artist_name:
                    facts.drummer_personnel.append(artist_name)

    if mbid:
        low_level = _fetch_acousticbrainz_lowlevel(mbid)
        if low_level:
            rhythm = low_level.get("rhythm") or {}
            tonal = low_level.get("tonal") or {}
            if rhythm.get("bpm"):
                facts.tempo_bpm = rhythm["bpm"]
            key = tonal.get("key_key")
            scale = tonal.get("key_scale")
            if key:
                facts.musical_key = f"{key} {scale}".strip() if scale else key
            facts.sources.append(f"https://acousticbrainz.org/{mbid}")

    return facts
