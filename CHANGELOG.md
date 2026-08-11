# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

See [`docs/RELEASING.md`](docs/RELEASING.md) for the versioning policy and
release process.

## [Unreleased]

## [0.1.0] - 2026-08-11

First tagged release. This project has been under active development for a
while (see git history for the full commit-by-commit record); this entry is
a feature-level snapshot of what's in this release, not a reconstruction of
every prior commit.

### Added

- **Multi-genre pattern generation**: Metal, Rock, Jazz, and Funk, each with
  7 styles (e.g. metal: heavy/death/power/progressive/thrash/doom/breakdown).
- **Drummer style imitation**: 7 individual drummer plugins (Bonham, Porcaro,
  Weckl, Chambers, Roeder, Dee, Hoglan) plus a composite plugin
  (`CompositeDoomBluesPlugin`) layering multiple drummers' techniques.
- **Song structure & composition**: configurable section structures (intro,
  verse, chorus, bridge, breakdown, outro, ...), pattern variations, fills,
  humanization, and complexity controls.
- **Plugin architecture**: `GenrePlugin`/`DrummerPlugin` strategy interfaces
  with auto-discovery, so new genres/drummers can be added without touching
  core code.
- **MIDI export**: EZDrummer 3-compatible output with realistic velocity and
  timing.
- **Reaper DAW integration**: generate `.RPP` project files with automatic
  section markers, genre-aware marker colors, and combined MIDI+markers
  export.
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

[Unreleased]: https://github.com/fsecada01/midi-drums/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fsecada01/midi-drums/releases/tag/v0.1.0
