"""Tests for the song_research spike (see midi_drums/ai/song_research.py).

All network access is mocked via monkeypatch on the module's internal
``_rate_limited_get`` — these tests must never hit the real MusicBrainz/
AcousticBrainz APIs, matching this repo's convention of deterministic,
offline unit tests.

The on-disk lookup cache is redirected to a per-test tmp_path via the
autouse ``_isolate_cache`` fixture below, so tests never read/write a
real user's home directory and never leak cached state between tests.
"""

import json
import time

import pytest

from midi_drums.ai import song_research


@pytest.fixture(autouse=True)
def _isolate_cache(tmp_path, monkeypatch):
    cache_path = tmp_path / "song_research_cache.json"
    monkeypatch.setattr(song_research, "_cache_file_path", lambda: cache_path)


class TestResearchSongFullMatch:
    def test_combines_musicbrainz_and_acousticbrainz_facts(self, monkeypatch):
        responses = {
            "recording/?query=": {"recordings": [{"id": "mbid-123"}]},
            "recording/mbid-123?": {
                "artist-credit": [{"name": "Black Sabbath"}],
                "releases": [{"date": "1970-02-13"}, {"date": "1970-06-01"}],
                "genres": [{"name": "heavy metal"}, {"name": "doom metal"}],
                "relations": [
                    {
                        "type": "instrument",
                        "attributes": ["drums"],
                        "artist": {"name": "Bill Ward"},
                    },
                    {
                        "type": "vocal",
                        "attributes": ["lead vocals"],
                        "artist": {"name": "Ozzy Osbourne"},
                    },
                ],
            },
            "acousticbrainz.org/api/v1/mbid-123/low-level": {
                "rhythm": {"bpm": 79.3},
                "tonal": {"key_key": "E", "key_scale": "minor"},
            },
        }

        def fake_get(url, timeout=8.0):
            for fragment, payload in responses.items():
                if fragment in url:
                    return payload
            raise AssertionError(f"unexpected URL in test: {url}")

        monkeypatch.setattr(song_research, "_rate_limited_get", fake_get)

        facts = song_research.research_song("Black Sabbath", "Black Sabbath")

        assert facts.mbid == "mbid-123"
        assert facts.artist == "Black Sabbath"
        assert facts.first_release_date == "1970-02-13"
        assert facts.genres == ["doom metal", "heavy metal"]
        assert facts.drummer_personnel == ["Bill Ward"]
        assert facts.tempo_bpm == 79.3
        assert facts.musical_key == "E minor"
        assert "musicbrainz.org/recording/mbid-123" in facts.sources[0]
        assert any("acousticbrainz.org" in s for s in facts.sources)

    def test_fact_sheet_renders_verified_facts(self, monkeypatch):
        monkeypatch.setattr(
            song_research,
            "_rate_limited_get",
            lambda url, timeout=8.0: (
                {"recordings": [{"id": "mbid-1"}]}
                if "query=" in url
                else (
                    {
                        "artist-credit": [{"name": "Rush"}],
                        "releases": [{"date": "1981-02-12"}],
                        "genres": [{"name": "progressive rock"}],
                        "relations": [],
                    }
                    if "recording/mbid-1?" in url
                    else {"rhythm": {"bpm": 155.0}, "tonal": {}}
                )
            ),
        )

        facts = song_research.research_song("Tom Sawyer", "Rush")
        sheet = facts.as_prompt_fact_sheet()

        assert "VERIFIED SONG FACTS for 'Tom Sawyer' by Rush" in sheet
        assert "Release date: 1981-02-12" in sheet
        assert "Genre tags: progressive rock" in sheet
        assert "Tempo: 155 BPM" in sheet
        assert "Sources:" in sheet


class TestCaching:
    def test_second_call_uses_cache_without_network(self, monkeypatch):
        call_count = {"n": 0}

        def fake_get(url, timeout=8.0):
            call_count["n"] += 1
            if "query=" in url:
                return {"recordings": [{"id": "mbid-cached"}]}
            if "recording/mbid-cached?" in url:
                return {
                    "artist-credit": [{"name": "Rush"}],
                    "releases": [{"date": "1981-02-12"}],
                    "genres": [{"name": "progressive rock"}],
                    "relations": [],
                }
            return {"rhythm": {"bpm": 155.0}, "tonal": {}}

        monkeypatch.setattr(song_research, "_rate_limited_get", fake_get)

        first = song_research.research_song("Tom Sawyer", "Rush")
        calls_after_first = call_count["n"]
        assert calls_after_first > 0

        second = song_research.research_song("Tom Sawyer", "Rush")

        assert call_count["n"] == calls_after_first  # no new network calls
        assert second == first

    def test_different_song_is_not_a_cache_hit(self, monkeypatch):
        monkeypatch.setattr(
            song_research, "_rate_limited_get", lambda url, timeout=8.0: None
        )
        song_research.research_song("Song A")

        call_count = {"n": 0}

        def fake_get(url, timeout=8.0):
            call_count["n"] += 1
            return None

        monkeypatch.setattr(song_research, "_rate_limited_get", fake_get)
        song_research.research_song("Song B")

        assert call_count["n"] > 0  # different cache key, still fetched

    def test_expired_hit_entry_triggers_refetch(self, monkeypatch):
        cache_path = song_research._cache_file_path()
        key = song_research._cache_key("Headless Cross", "Black Sabbath")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    key: {
                        "cached_at": (
                            time.time()
                            - song_research._CACHE_TTL_HIT_SECONDS
                            - 1
                        ),
                        "data": {
                            "title": "Headless Cross",
                            "artist": "Black Sabbath",
                            "mbid": "stale-mbid",
                            "first_release_date": None,
                            "genres": [],
                            "drummer_personnel": [],
                            "tempo_bpm": None,
                            "musical_key": None,
                            "sources": [],
                        },
                    }
                }
            ),
            encoding="utf-8",
        )

        monkeypatch.setattr(
            song_research, "_rate_limited_get", lambda url, timeout=8.0: None
        )

        facts = song_research.research_song("Headless Cross", "Black Sabbath")

        # Refetched (network mocked to miss) rather than returning the
        # stale cached mbid — proves the expired entry was not reused.
        assert facts.mbid is None

    def test_fresh_miss_entry_is_reused_without_refetch(self, monkeypatch):
        cache_path = song_research._cache_file_path()
        key = song_research._cache_key("Some Obscure Song", None)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    key: {
                        "cached_at": time.time(),
                        "data": {
                            "title": "Some Obscure Song",
                            "artist": None,
                            "mbid": None,
                            "first_release_date": None,
                            "genres": [],
                            "drummer_personnel": [],
                            "tempo_bpm": None,
                            "musical_key": None,
                            "sources": [],
                        },
                    }
                }
            ),
            encoding="utf-8",
        )

        def fail_if_called(url, timeout=8.0):
            raise AssertionError("should have used the cached miss entry")

        monkeypatch.setattr(song_research, "_rate_limited_get", fail_if_called)

        facts = song_research.research_song("Some Obscure Song")
        assert facts.mbid is None


class TestPickBestCandidate:
    """Regression coverage for a bug found via live testing: MusicBrainz's
    title+artist search for a real song ("Headless Cross" by Black
    Sabbath) returned several tied-score candidates, and the naive top-1
    result was a 2018 fan-recorded live bootleg rather than the 1989
    studio track — even though a candidate with an "Official"/"Promotion"
    release was present a few entries down.
    """

    def test_prefers_candidate_with_earliest_official_release(self):
        bootleg_2018 = {
            "id": "bootleg-mbid",
            "releases": [{"date": "2018", "status": "Bootleg"}],
        }
        bootleg_2015 = {
            "id": "bootleg-2015-mbid",
            "releases": [{"date": "2015", "status": "Bootleg"}],
        }
        studio_1989 = {
            "id": "studio-mbid",
            "releases": [
                {"date": "1989", "status": "Promotion"},
                {"date": "2001-04-02", "status": "Official"},
            ],
        }

        winner = song_research._pick_best_candidate(
            [bootleg_2018, bootleg_2015, studio_1989]
        )

        assert winner["id"] == "studio-mbid"

    def test_falls_back_to_top1_when_only_bootlegs_indexed(self):
        only_bootleg = {
            "id": "only-bootleg-mbid",
            "releases": [{"date": "2020", "status": "Bootleg"}],
        }
        no_releases = {"id": "no-releases-mbid", "releases": []}

        winner = song_research._pick_best_candidate([only_bootleg, no_releases])

        assert winner["id"] == "only-bootleg-mbid"


class TestRateLimitedGetRetry:
    """Regression coverage for a second real bug found via live testing:
    the heavy `inc=` detail query timed out repeatedly against the real
    MusicBrainz API (observed in 2 of 3 live "Headless Cross" runs) —
    _rate_limited_get now retries once on a bare timeout before giving up.
    """

    def test_retries_once_on_timeout_then_succeeds(self, monkeypatch):
        attempts = {"n": 0}

        def fake_urlopen(request, timeout):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise TimeoutError("The read operation timed out")

            class _Resp:
                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    return False

                def read(self):
                    return b'{"ok": true}'

            return _Resp()

        monkeypatch.setattr(
            song_research.urllib.request, "urlopen", fake_urlopen
        )

        result = song_research._rate_limited_get("https://example.test/x")

        assert attempts["n"] == 2
        assert result == {"ok": True}

    def test_gives_up_after_exhausting_retries(self, monkeypatch):
        attempts = {"n": 0}

        def fake_urlopen(request, timeout):
            attempts["n"] += 1
            raise TimeoutError("The read operation timed out")

        monkeypatch.setattr(
            song_research.urllib.request, "urlopen", fake_urlopen
        )

        result = song_research._rate_limited_get(
            "https://example.test/x", retries=1
        )

        assert attempts["n"] == 2  # initial attempt + 1 retry, then give up
        assert result is None

    def test_does_not_retry_on_non_timeout_error(self, monkeypatch):
        attempts = {"n": 0}

        def fake_urlopen(request, timeout):
            attempts["n"] += 1
            raise song_research.urllib.error.HTTPError(
                "https://example.test/x", 404, "Not Found", {}, None
            )

        monkeypatch.setattr(
            song_research.urllib.request, "urlopen", fake_urlopen
        )

        result = song_research._rate_limited_get(
            "https://example.test/x", retries=1
        )

        assert attempts["n"] == 1  # no retry for a definite error
        assert result is None


class TestResearchSongLookupMiss:
    def test_no_musicbrainz_match_returns_minimal_facts(self, monkeypatch):
        monkeypatch.setattr(
            song_research, "_rate_limited_get", lambda url, timeout=8.0: None
        )

        facts = song_research.research_song("Some Obscure Song", "Nobody")

        assert facts.title == "Some Obscure Song"
        assert facts.artist == "Nobody"
        assert facts.mbid is None
        assert facts.genres == []
        assert facts.sources == []

    def test_lookup_miss_fact_sheet_says_so(self, monkeypatch):
        monkeypatch.setattr(
            song_research, "_rate_limited_get", lambda url, timeout=8.0: None
        )

        facts = song_research.research_song("Some Obscure Song")
        sheet = facts.as_prompt_fact_sheet()

        assert "no verified facts found" in sheet
        assert "Sources:" not in sheet

    def test_network_error_never_raises(self, monkeypatch):
        # Exercise the real _rate_limited_get (not a monkeypatched stand-in)
        # to prove it actually catches urllib errors rather than propagating.
        def fake_urlopen(*args, **kwargs):
            raise song_research.urllib.error.URLError("network down")

        monkeypatch.setattr(
            song_research.urllib.request, "urlopen", fake_urlopen
        )

        facts = song_research.research_song("Anything")
        assert facts.mbid is None
