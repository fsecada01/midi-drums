# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

See [`docs/RELEASING.md`](docs/RELEASING.md) for the versioning policy and
release process.

## [Unreleased]

## [0.3.0] - 2026-08-21

### Added

- **Riff-locked drum generation**: a new `riff` CLI subcommand and
  `DrumGeneratorAPI.analyze_riff()` analyze a recorded guitar/bass riff's
  rhythmic accents via onset detection (librosa) and lock a genre plugin's
  kick pattern onto them, while snare, hi-hat, cymbals, fills, and drummer
  styling still come from the normal generation pipeline untouched (#57).
  V1 scope: the riff is analyzed as one representative bar and tiled to
  fill `--bars`.
- **`RiffLockTransform` modification**, applied via
  `PluginManager.apply_riff_lock()` (routed through the `plugins` domain
  rather than `generation` importing `modifications` directly, per this
  project's existing DDD domain-boundary rules).
- **Snare-accent-reaction**: `SnareAccentReaction` reacts the snare to the
  same riff accents, in either `reinforce` mode (velocity-boosts existing
  snare hits near a strong accent) or `stab` mode (inserts a unison snare
  hit at very strong accents where riff-lock placed a kick but no snare was
  nearby, deterministically collapsing to reinforce instead of stacking a
  second hit when an existing snare is already close by). New
  `--snare-mode`/`--snare-stab-threshold` CLI flags and
  `GenerationParameters.riff_snare_mode`/`riff_snare_stab_threshold` fields;
  defaults to `"off"` (no behavior change unless explicitly enabled).
- **New `midi_drums.analysis` package** (a sibling of `midi_drums.ai`, not
  nested in it, so importing onset-detection code doesn't drag in the
  LangChain/pydantic-ai stack) and a new `audio` extras group
  (`uv sync --group audio`: librosa, soundfile, numpy).
- **New REAPER `create_beat_from_riff.lua` action**: select a riff item and
  run it to get a kick-locked drum pattern back. Uses the take's own audio
  source directly when available, or a bar-aligned time-selection render
  for MIDI/VSTi takes; corrects for riffs that don't start on a bar line
  via `--offset-beats`.

### Fixed

- REAPER's `io.popen` command construction is now routed through
  `cmd /S /C`, avoiding a Windows quote-stripping bug that corrupted
  commands built from multiple quoted segments (surfaced as `'...' is not
  recognized` in AI-agent mode).
- CLI stdout/stderr are reconfigured to UTF-8 on Windows, avoiding a
  `UnicodeEncodeError` crash when AI-generated text containing non-ASCII
  characters is piped through REAPER's `io.popen`.
- `GetUserInputs` dialogs in `create_song_sections.lua` are now wide enough
  to comfortably read and edit free-text fields, especially the AI
  description prompt.
- The AI agent's system prompt now requires a complete song structure (6-8+
  sections, including a chorus/hook and an outro) instead of allowing it to
  infer a bare 2-section song from a partial description.
- Release-notes generation (`release.yml`) no longer emits a spurious
  leading/trailing blank line around each version's changelog section.

No breaking changes - `riff_snare_mode` defaults to `"off"` (identical to
pre-feature behavior) and every other addition is a new optional
field/method/CLI flag; see [`docs/RELEASING.md`](docs/RELEASING.md) for what
counts as this project's public API surface.

## [0.2.0] - 2026-08-13

### Added

- **Per-section tempo/meter segments**: a `Section` can now hold internal
  tempo/time-signature changes via `SongSegment` (e.g. a 7/8 insert inside
  an otherwise 4/4 verse), instead of one tempo/meter per section (#53).
  `MIDIEngine` emits per-segment tempo/time-signature events for segmented
  sections; non-segmented sections remain byte-identical to prior output.
- **song_creator JSON bridge**: `DrumGeneratorAPI.create_song_from_song_map()`
  / `export_song_map_json()` read/write the song_creator "song map" JSON
  shape (regions -> segments) directly into/out of a `Song`.
- **Timeline export**: `DrumGeneratorAPI.export_song_timeline_json()` and
  the `generate --write-timeline` CLI flag resolve a `Song` (segmented or
  not) to a flat tempo/region timeline JSON, consumed by REAPER's Lua-side
  "song map" mode.
- **`generate --song-map` CLI flag**, taking precedence over `--sidecar`
  when both are given.
- **REAPER `create_song_sections.lua` "songmap" mode**: reads a song-map
  JSON, calls the CLI with `--song-map`/`--write-timeline`, and places one
  tempo/meter marker per resolved change point plus one colored region per
  song-map region.
- **Docs site**: an end-to-end Use Cases page, Funk and Electronic recipe
  cards on the Recipes page (both genres were already fully supported but
  had no walkthrough), and a shared `docs/site-pages/site.css` stylesheet
  consolidating the design tokens/nav/layout CSS that was previously
  duplicated across all 5 site pages.

### Changed

- **Docs site accessibility**: WCAG 2.1 AA color-contrast fixes (`--muted`
  and other low-contrast tokens), a skip-to-content link, ARIA landmarks
  with working keyboard-focus targets, visible `:focus-visible` states, and
  corrected heading hierarchy (TOC sidebar labels demoted from `<h3>` to
  non-heading elements so each page has one correct `<h1>`-first outline)
  across all docs pages (#44).
- `docs/make.py` now copies static assets (e.g. `site.css`) alongside the
  HTML pages it already copied, via an explicit suffix allowlist.

No breaking changes - every addition above is backwards compatible (new
optional fields, new methods, new CLI flags); see
[`docs/RELEASING.md`](docs/RELEASING.md) for what counts as this project's
public API surface.

## [0.1.0] - 2026-08-12

First tagged release. This project has been under active development for a
while (see git history for the full commit-by-commit record); this entry is
a feature-level snapshot of what's in this release, not a reconstruction of
every prior commit.

### Added

- **Multi-genre pattern generation**: Metal, Rock, Jazz, Funk, and
  Electronic, each with 4-7 styles (e.g. metal:
  heavy/death/power/progressive/thrash/doom/breakdown; electronic:
  house/techno/drum'n'bass/dubstep).
- **Drummer style imitation**: 10 individual drummer plugins (Bonham,
  Porcaro, Weckl, Chambers, Roeder, Dee, Hoglan, Peart, Rich, Copeland) plus
  a composite plugin (`CompositeDoomBluesPlugin`) layering multiple
  drummers' techniques.
- **Song structure & composition**: configurable section structures (intro,
  verse, chorus, bridge, breakdown, outro, ...), pattern variations, fills,
  humanization, and complexity controls.
- **Plugin architecture**: `GenrePlugin`/`DrummerPlugin` strategy interfaces
  with auto-discovery, so new genres/drummers can be added without touching
  core code.
- **MIDI export with per-preset note mappings**: `ezdrummer3` (primary
  target, extended hi-hat articulations) and GM-compliant presets
  (`gm_drums`, `studio_drummer3`, `addictive_drums`, `bfd3`, `modo_drums`,
  `ml_drums`) that correctly collapse to true General MIDI notes, plus
  custom mapping support via `--mapping-file` / `DrumKit.from_json()` /
  `DrumKit.from_dict()`.
- **Reaper DAW integration**: generate `.RPP` project files with automatic
  section markers, genre-aware marker colors, and combined MIDI+markers
  export, plus vendored `reaper/create_song_sections.lua` and
  `reaper/midi_drums_help.lua` ReaScripts bridging REAPER and this module
  via a JSON sidecar file (three modes: REAPER-driven, Python-driven,
  AI-agent-driven).
- **AI-assisted generation** (optional, `ai` extra): natural-language pattern
  and song generation via Pydantic AI / Langchain, with multi-provider
  backend support (Anthropic, OpenAI, and others).
- **Physical feasibility validation**: checks generated patterns against
  drummer-physically-playable constraints (limb independence, reach, etc.).
- **Advanced humanization**: context-aware timing/velocity humanization
  distinct from the base pattern-generation humanization controls.
- **Interfaces**: Python API (`DrumGeneratorAPI`), CLI (`midi-drums`), and
  direct module usage.
- **DDD re-architecture** (epic #8): the package is organized into four
  bounded domains - `core/` (models & value objects), `export/` (MIDI &
  Reaper), `plugins/` (genre & drummer strategies), `generation/`
  (composition & orchestration) - each with dependency boundaries enforced
  by executable tests. See `docs/DDD_ARCHITECTURE.md` and
  `docs/MIGRATION_GUIDE.md`.
- **CI**: automated test suite and auto-deployed API docs (GitHub Pages) on
  every push to `main`.

### Fixed

- Intelligent ride/hi-hat switching in genre plugins based on section energy
  (#1).
- Composite drummer plugin conflict resolution when layering multiple
  drummer styles (#4).
- `DrumGeneratorAPI.batch_generate()` no longer raises `TypeError` when a
  spec dict includes an explicit `name` key (the pattern shown in the
  method's own docstring example).
- `DrumGeneratorAPI.create_song()` now honors a caller-supplied `drum_kit`
  over the `mapping` preset name, and treats an explicit `drum_kit=None` as
  "no explicit kit" rather than leaving a stale kit in place (#24).
- Genre-aware high-energy timekeeper selection and drummer-modification
  ordering, so drummer style passes apply in a consistent, predictable
  sequence (#18).
- Drummer signature fills are now actually wired into fill generation
  instead of being defined but unused (#32).
- Beat provenance tracking and a shared timekeeper-cymbal registry, closing
  a conflict where multiple modifications could clobber each other's
  cymbal choices (#36).
- GM-baseline kit presets (`gm_drums` and the other GM-compliant presets
  listed above) previously matched EZDrummer 3's extended-articulation note
  numbers 1:1 instead of collapsing to true GM notes; they now actually
  produce GM-compliant output (#47).

[Unreleased]: https://github.com/fsecada01/midi-drums/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/fsecada01/midi-drums/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/fsecada01/midi-drums/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/fsecada01/midi-drums/releases/tag/v0.1.0
