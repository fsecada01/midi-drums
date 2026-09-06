# Design: Song-Research Grounding for AI Pattern Generation

**Status**: spike / proposed, opt-in only, built up past the initial spike
with a CLI flag, on-disk caching, and a reliability fix (see "Built up
past the spike" below). Implements `research_song` as an opt-in tool on
`PatternCompositionAgent` (`midi_drums/ai/agents/pattern_agent.py`) backed
by `midi_drums/ai/song_research.py`. Off by default — no existing caller
(CLI, REAPER panel, tests) changes behavior or starts making network
calls unless explicitly enabled via `--research-song` or the
`MIDI_DRUMS_ENABLE_SONG_RESEARCH` env var. Not yet an ADR: this is a
working spike to validate the approach before committing to it as a
supported feature.

## Context

Today, `PydanticPatternGenerator` and `PatternCompositionAgent` map a
natural-language description to genre/style/drummer purely from whatever
the underlying LLM backend already knows from pretraining — see the
"trained knowledge" discussion this spike followed up on. If a user names
a real song ("drums like Metallica's One"), the app has no way to verify
or supplement the model's recollection of that song's actual tempo,
genre, or drummer, and no visibility into whether the model's guess is
accurate or a plausible-sounding hallucination.

## Research summary

Full findings (with source links) are in this session's research pass;
condensed here as the basis for the design below.

1. **Metadata APIs**: no single free API returns
   `{tempo, key, genre, era, drummer}` in one call. Spotify's
   audio-features/audio-analysis endpoints were deprecated for new apps
   in Nov 2024 and Spotify has said they won't return, citing AI-training
   concerns. The realistic free combination is **MusicBrainz** (personnel
   credits, genre tags, release dates — no API key required, 1 req/sec
   courtesy limit) + **AcousticBrainz** (tempo/key by MusicBrainz ID —
   dataset frozen since 2022, so recent/less-common recordings will often
   miss). GetSongBPM is a viable paid-free-tier fallback for tempo not
   wired into this spike.
2. **Agentic grounding best practice**: retrieval should return a small
   **structured object**, not raw scraped text dumped into the agent's
   context — and for objective fields (tempo, date, genre) the retrieved
   fact should be preferred over the model's own recollection, while
   subjective/stylistic judgment stays with the model.
3. **Prompt injection**: OWASP's LLM Top 10 keeps prompt injection (esp.
   *indirect* injection via fetched documents) at #1. Fetched content
   must be parsed by non-instruction-following code into a fixed schema
   before it ever reaches a tool-calling agent's context — never
   concatenated as free text.
4. **Copyright posture**: facts (tempo, key, date, personnel) are not
   independently copyrightable (*Feist v. Rural Telephone*); transcribing
   or reproducing the actual recorded performance is a different, actively
   litigated category (Suno/Udio suits, mixed settlements and a July 2026
   Munich ruling against Suno). The safe product line is metadata-only —
   never fetch/transcribe audio, lyrics, or drum notation.
5. **Prior art**: neither Suno nor Udio performs live retrieval for style
   conditioning — Suno blocks real artist names outright; Udio allows
   naming artists in free text but conditions on user-uploaded audio, not
   web lookup. A metadata-grounding tool is a differentiator, not
   something to copy from an existing implementation.

## Decision (spike scope)

- New module `midi_drums/ai/song_research.py`: `research_song(title,
  artist=None) -> SongFacts`, combining a MusicBrainz recording search +
  detail fetch (personnel/genre/date) with a best-effort AcousticBrainz
  lookup (tempo/key) by the resulting MBID. Never raises; a total lookup
  miss returns a `SongFacts` with only `title`/`artist` set.
- `SongFacts.as_prompt_fact_sheet()` renders a small, clearly-labeled
  `VERIFIED SONG FACTS` text block with inline source URLs — this is the
  *only* thing that reaches the agent's context. All JSON parsing and
  field extraction happens in plain Python before that point, so no
  fetched web content can inject instructions into the agent (point 3
  above).
- Wired as a new `@tool research_song` on `PatternCompositionAgent`, but
  only appended to the tool list when
  `os.environ["MIDI_DRUMS_ENABLE_SONG_RESEARCH"] == "1"`. The system
  prompt gets a matching addendum (`_build_system_prompt`) only when the
  tool is present, so an agent whose tools don't include `research_song`
  never sees instructions referencing it.
- `PydanticPatternGenerator` (the non-agentic, structured-output-only
  path) is **not** touched — it has no tool-calling loop to attach a
  retrieval step to; wiring it in would require a separate pre-analysis
  call, deferred as a follow-up if this spike is accepted.

## Validated against a real song

Live-tested against Black Sabbath's "Headless Cross" (1989, Tony Martin/
Cozy Powell era) — a good stress case since MusicBrainz indexes several
bootleg live recordings of it alongside the studio track. This surfaced
and fixed two real bugs before the spike could be called working:

- **Timeout too short**: the `inc=artist-credits+releases+tags+genres+
  artist-rels` detail query took >8s and timed out. Bumped the default
  timeout to 20s.
- **Naive top-1 match picked the wrong recording**: the search returned
  several score-100 candidates, and the literal first one was a
  fan-recorded 2018 live bootleg ("Definitive Chicago 1995"), not the
  1989 studio track — exactly the fuzzy-match risk called out below.
  Fixed by `_pick_best_candidate`/`_best_release_date`: prefer whichever
  candidate has an Official/Promotion-status release with the earliest
  date, falling back to MusicBrainz's own top-1 ranking only when no
  candidate has one. Locked in with regression tests
  (`TestPickBestCandidate`) using the real response shape that exposed
  the bug.
- Also fixed: genre tags turned out to live on the *artist* object nested
  under each release's `artist-credit`, not on the recording itself
  (which had empty `genres`/`tags`) — added a fallback that walks the
  nested artist genres when the recording-level fields are empty.

After these fixes, `research_song("Headless Cross", "Black Sabbath")`
correctly returns: release date 1989, genres
`hard rock, heavy metal, metal, rock`, drummer credit **Cozy Powell**
(correct — he played on that album), tempo ~88 BPM, key A minor, with
both MusicBrainz and AcousticBrainz source links. This is a genuine,
non-trivial confirmation the approach works, not just that the code
runs.

**Second round of live testing** (after the "build up" pass below)
surfaced two further observations, not full bugs:

- The 20s timeout on the heavy `inc=` detail query still timed out on
  2 of 3 live runs against the same song. Fixed with a one-shot retry
  on a bare `TimeoutError` (never on a definite 4xx/5xx/malformed-JSON
  error, where a retry can't help) — see `_rate_limited_get(retries=1)`
  and `TestRateLimitedGetRetry`.
- MusicBrainz's own tied-score search ordering is not perfectly stable
  across separate calls — 3 live runs of the same title+artist query
  returned 3 different top-ranked candidates. `_pick_best_candidate`'s
  official-release preference still resolves this correctly in
  practice (the studio release consistently wins over bootlegs
  regardless of search-result order), but it's an accepted external-
  service limitation worth knowing about, not something further
  client-side code can fully eliminate.

## Built up past the spike

Once the spike was validated against a real song, it was promoted from
an env-var-only prototype to a properly parameterized feature:

- **CLI flag**: `python -m midi_drums prompt --song --research-song ...`
  (`midi_drums/api/cli.py`). Warns to stderr and is ignored if `--song`
  isn't also set, since the tool only attaches to the agent path.
- **Constructor param, env var preserved for compat**:
  `DrumGeneratorAI(enable_song_research=...)` →
  `PatternCompositionAgent(enable_song_research=...)`. `None` (the
  default) falls back to reading `MIDI_DRUMS_ENABLE_SONG_RESEARCH`, so
  existing env-var-based usage is unaffected; an explicit `True`/`False`
  always takes precedence.
- **On-disk caching**: `research_song()` is now a caching wrapper around
  the original lookup logic (renamed `_research_song_live`). Cache file
  at `~/.midi_drums_cache/song_research_cache.json` (overridable via
  `MIDI_DRUMS_CACHE_DIR` for tests), keyed on lowercased
  `title|artist`. A successful match (`mbid` set) is cached for 30
  days; a total lookup miss is cached for only 24 hours, so a
  transiently-unavailable song isn't permanently remembered as
  unfindable.
- **Retry-on-timeout**: see "Second round of live testing" above.

## Non-goals (still out of scope)

- Tempo/key fallback via GetSongBPM or any paid API — AcousticBrainz-only
  for now, which will miss most post-2022 or lesser-known tracks. Known
  gap, not a blocker for validating the approach.
- Any change to `PydanticPatternGenerator` — it has no tool-calling loop
  to attach a retrieval step to; wiring it in would need a separate
  pre-analysis call.
- Reproducing or fetching the actual drum performance, lyrics, or any
  audio of the referenced song — deliberately unsupported, see Research
  point 4.

## Consequences

- Enabling the flag makes the agent's tool-use path perform live HTTP
  calls to two third-party services with no auth — acceptable for a
  personal/local tool, but this should not be default-on for any shared
  deployment without adding rate-limit/backoff hardening beyond the
  simple 1-req/sec sleep implemented here.
- MusicBrainz's search-by-title-string matching is fuzzy; a common song
  title with no artist given can still match the wrong recording even
  with the official-release preference above (e.g. a song with only
  bootlegs indexed, or a title shared by multiple real songs). The tool
  always attributes its source MBID/URL so a wrong match is at least
  traceable, but there's no confidence score surfaced to the agent yet.
- AcousticBrainz being frozen since 2022 means tempo/key will be `None`
  for a large fraction of real-world requests — the fact sheet is
  designed to degrade gracefully ("no verified facts found... use your
  own musical judgment"), so this is a silent quality gap, not a crash.

## Follow-ups if this graduates past spike

- ~~Local on-disk cache~~ — done, see "Built up past the spike" above.
- ~~Promote to a first-class CLI flag~~ — done (`--research-song`).
- Add GetSongBPM as a tempo/key fallback when AcousticBrainz misses.
  Deferred: requires the user to obtain and configure a free API key,
  not something to add without checking with them first.
- Surface a match-confidence signal so the agent can ask for
  disambiguation ("Which 'Renegade'?") instead of silently trusting a
  fuzzy top-1 match.
- If accepted as a permanent feature, write a proper ADR referencing this
  design doc and the research findings above.

## References

- New module: `midi_drums/ai/song_research.py`
- Tool wiring: `midi_drums/ai/agents/pattern_agent.py`
  (`research_song` tool, `_build_system_prompt`,
  `_SONG_RESEARCH_ENV_FLAG`)
- Tests: `tests/unit/ai/test_song_research.py`
- MusicBrainz Web Service docs: <https://musicbrainz.org/doc/MusicBrainz_API>
- AcousticBrainz API docs: <https://acousticbrainz.org/api>
- OWASP LLM Top 10 (prompt injection / excessive agency):
  <https://www.promptfoo.dev/docs/red-team/owasp-llm-top-10>
