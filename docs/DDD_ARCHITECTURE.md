# DDD Architecture

> Companion to the [Package Structure](../README.md#project-structure) section
> of the README and [`CLAUDE.md`](../CLAUDE.md). This doc explains *why* the
> package is laid out the way it is, and the dependency rules each domain is
> expected to follow.

## Background

Epic #8 re-organized `midi_drums` from a flat, historically-grown layout
(`midi_drums/models/`, `midi_drums/engines/`, `midi_drums/exporters/`,
`midi_drums/core/engine.py`, ...) into four explicit domains, each owning a
single layer of responsibility:

| Phase | Issue | Domain | What moved in |
|-------|-------|--------|----------------|
| 1 | #9  | `core/`       | `Pattern`, `Beat`, `Song`, `Section`, `Kit`, value objects (`TimeSignature`, `DrumInstrument`, `GenerationParameters`) |
| 2 | #10 | `export/`     | MIDI + Reaper engines, `ReaperExporter`, Reaper section/marker models |
| 3 | #11 | `plugins/`    | `GenrePlugin`/`DrummerPlugin` interfaces, `PluginRegistry`/`PluginManager`, auto-discovery, composite drummers |
| 4 | #12 | `generation/` | `DrumGenerator`, `PatternBuilder`, `PatternStrategy`/`FillStrategy` interfaces, `GenerationService` |

Each phase landed as its own PR with its own AST-based dependency-boundary
test (see [Enforcement](#enforcement) below) and, where an old import path
had external callers, a compatibility shim so existing code kept working
during the transition.

## The Domains

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                │
│  CLI Interface │ Python API │ Direct Module Usage │ REST (future)│
├─────────────────────────────────────────────────────────────────┤
│                    generation/                                  │
│  DrumGenerator │ PatternBuilder │ Strategies │ GenerationService │
├─────────────────────────────────────────────────────────────────┤
│                    plugins/                                     │
│  Genre Plugins │ Drummer Plugins │ Auto-Discovery │ Registry     │
├─────────────────────────────────────────────────────────────────┤
│                    export/                                      │
│  MIDIEngine │ MIDIExporter │ ReaperEngine │ ReaperExporter       │
├─────────────────────────────────────────────────────────────────┤
│                      core/                                      │
│  Pattern │ Beat │ Song │ Section │ Kit │ GenerationParameters    │
└─────────────────────────────────────────────────────────────────┘
```

### `core/` — shared kernel

Models and value objects with **no dependency on any other domain**. Every
other domain may depend on `core/`; `core/` depends on nothing in
`midi_drums` except `config` (shared constants).

### `export/` — MIDI/Reaper file generation

Turns a `Song`/`Pattern` (from `core/`) into MIDI or `.RPP` files. May depend
on `core/`. Must not depend on `plugins/` or `generation/` — export doesn't
know or care how a pattern was generated.

### `plugins/` — genre & drummer strategies

Genre plugins turn `GenerationParameters` into `Pattern`s; drummer plugins
apply style modifications. May depend on `core/`, plus the application-level
packages it consumes for pattern construction and validation
(`modifications/`, `patterns/`, `utils/`, `validation/` — see
[Dependency Rule](#dependency-rule)). Does not depend on `export/`,
`generation/engines/`, `generation/services/`, or `generation/strategies/` —
a plugin has no reason to know how its output gets exported, which engine
invoked it, or how generation is orchestrated.

**Named exception**: every genre plugin and several drummer plugins
construct patterns via `midi_drums.generation.builders.pattern_builder.PatternBuilder`
— `PatternBuilder` is a shared, dependency-free construction utility (it
only imports from `core/` and `config/` itself), not part of the
composition/orchestration surface the rest of `generation/` represents. This
makes `generation/builders/` the one specifically-allowed import out of
`generation/` from within `plugins/`; `generation/engines/`,
`generation/services/`, and `generation/strategies/` remain off-limits.

### `generation/` — composition & orchestration

The one domain allowed to depend on all three of the others: `DrumGenerator`
legitimately needs `plugins/` (to generate patterns) and `export/` (to save
MIDI). This is the top of the dependency graph, not a peer of the other
three.

## Dependency Rule

Dependencies point **downward only**, with one named exception:

```
generation/ ──▶ plugins/ ──▶ core/
      │              │          ▲
      │              └╌╌╌╌╌╌╌╌╌╌┤  (plugins/ -> generation/builders/
      │                            PatternBuilder only - see plugins/
      │                            section above)
      └────────▶ export/ ──────┘
```

No domain imports from a domain above it in this graph except for that one
named exception, and `core/` imports from nothing (other than `config/`).
Application-level packages — `ai/`, `api/`, `validation/`, `humanization/`,
`utils/`, `modifications/`, `patterns/` — sit outside this graph entirely;
they're consumers of it, not part of the layering.

## Compatibility Shims

Where a phase moved a class that had known external call sites, the old
import path was kept alive as a thin re-export rather than broken outright:

- `midi_drums.exporters` re-exports `ReaperExporter` from `export/reaper/exporter.py`.
- `midi_drums.plugins.base` re-exports `GenrePlugin`, `DrummerPlugin`,
  `PluginRegistry`, `PluginManager` from their new `interfaces/`/`registry/`
  locations.

These shims are permanent, not a temporary bridge scheduled for removal —
see [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md) if you're updating code that
uses the old paths anyway.

## Enforcement

Each domain's dependency rules are enforced by an executable test, not just
this document:

- `tests/unit/core/test_core_domain_migration.py`
- `tests/unit/export/test_export_domain_migration.py`
- `tests/unit/plugins/test_plugin_domain_migration.py`
- `tests/unit/generation/test_generation_domain_migration.py`

Each AST-scans its domain's `.py` files (via the shared
`tests/unit/_domain_migration_helpers.imported_modules` helper) for imports
matching a `FORBIDDEN_DOMAIN_PREFIXES` tuple scoped to that domain's position
in the graph above. A PR that introduces an upward or sideways dependency
fails these tests before it fails code review.

## Adding a New Domain-Owned Module

1. Decide which domain the module belongs to using the table above (what
   does it depend on, what layer is it?).
2. Add it under that domain's package.
3. If it needs something from a domain not yet in that domain's allowed set,
   that's a signal the module is misplaced — re-check which domain it
   actually belongs to rather than widening the allowed set.
