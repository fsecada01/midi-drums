# Documentation Index

This is the single indexed home for this repo's internal developer
documentation. It exists so decision history and living reference don't
scatter across `claudedocs/`, `docs/`, and ad-hoc dated files — see
[ADR-driven cleanup, issue #59](https://github.com/fsecada01/midi-drums/issues/59)
for why this index was introduced. This repo is solo-maintained and
already uses PR review for everything, so a plain indexed directory
(reviewable, versioned, diffable) was chosen over GitHub's built-in Wiki.

Public-facing docs (the GitHub Pages site) live separately in
[`docs/site-pages/`](site-pages/) and are out of scope for this index —
different audience, published via `.github/workflows/docs.yml`.

## Decision records

[`docs/adr/`](adr/) — *why* a significant decision was made, not just what
the code does. Start here when you want the reasoning behind an existing
design before changing it.

## Living reference

| Doc | Covers |
|---|---|
| [`DDD_ARCHITECTURE.md`](DDD_ARCHITECTURE.md) | Domain-boundary import rules between packages |
| [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md) | Pre-DDD-migration import path → current path map |
| [`AI_INTEGRATION.md`](AI_INTEGRATION.md) | AI module architecture, examples, Pydantic schemas, API reference |
| [`VALIDATION_AND_HUMANIZATION.md`](VALIDATION_AND_HUMANIZATION.md) | Physical feasibility validation + advanced humanization usage guide |
| [`midi_drums_prompt.md`](midi_drums_prompt.md) | AI module prompt templates |
| [`CI_CD.md`](CI_CD.md) | CI/CD pipeline reference |
| [`RELEASING.md`](RELEASING.md) | Release cutting procedure |

## Historical / archived

Superseded design docs, completed implementation plans, and closed
research live in [`claudedocs/archive/`](../claudedocs/archive/), indexed
by topic in that directory's own `README.md`. `claudedocs/` itself is
scratch-and-archive only — see its `README.md` for the current convention.
