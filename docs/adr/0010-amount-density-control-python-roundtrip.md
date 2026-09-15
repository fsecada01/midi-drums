# 0010. Amount/density control is new Python-side generative logic, routed through job_runner's single-job model

> **Status**: Accepted (Python side implemented; Lua-side wiring still pending)
> **Date**: 2026-09-14

## Context

Research into EZdrummer 3's "Edit Play Style" feature
(`claudedocs/research_ezdrummer3_editplaystyle_20260914.md`) found its
Amount knob — musically-aware note add/remove, with a separate control
for snare ghost notes as of EZD3 3.0.3 — is the one mechanism that isn't a
cheap, pure Lua/REAPER-API operation: reassignment, articulation swap, and
velocity scaling/presets are all direct note-list edits, but deciding
*where* to plausibly add or remove a hit requires generative judgment.

The research report's own mapping table described this as "close to a
direct reuse" of `GhostNoteLayer` in
`midi_drums/modifications/drummer_mods.py`. On closer inspection while
writing the Step Editor design
(`claudedocs/design_step_editor_grid.md`, Revision 2), that overstates
it: `GhostNoteLayer` only *inserts* notes at a fixed intensity. There is
no existing signed, continuous, bidirectional "add or remove hits"
operation anywhere in the codebase — Amount is net-new Python work, not a
port of existing modification code.

Separately, `reaper/midi_drums/job_runner.lua` — the panel's only
subprocess-execution mechanism (ADR 0001) — is built around a single
global running job; every tab's Generate button already gates on "nothing
else running." Routing Amount through it means an Amount adjustment
blocks every other tab's Generate button for the round-trip.

## Decision

Implement Amount as a new Python module and CLI verb, invoked through the
existing `job_runner` async path exactly like every other generation
feature, and explicitly accept job_runner's single-job constraint for v1
rather than generalizing it.

- New module `midi_drums/modifications/density_control.py`:
  `adjust_density(notes, amount, kind, grid_resolution, context=None)`.
  Positive `amount` biases toward inserting additional plausible hits
  (reusing `GhostNoteLayer`'s insertion logic for the `kind="ghost"`
  case); negative `amount` removes existing hits, weighted toward the
  lowest-velocity/least-accented ones first. This is an original,
  deliberately simple heuristic — **not** a reproduction of Toontrack's
  undisclosed algorithm (no public technical description of it exists;
  see the research report's evidence-gap note). `context` (genre/style/
  drummer/complexity, when available via ADR 0009's provenance metadata)
  lets the heuristic bias its choices, but the function must degrade to a
  context-free heuristic rather than fail when it's absent.
- New headless CLI entrypoint following the project's established flat
  JSON-in/JSON-out convention for every Lua↔Python bridge:
  `python -m midi_drums adjust-density --input notes.json --instrument
  <lane> --amount <-1.0..1.0> --kind main|ghost --grid <resolution>
  [--genre --style --drummer --complexity] --output result.json`.
- The Step Editor tab's Amount slider commits only on release
  (`ImGui_IsItemDeactivatedAfterEdit`, so a drag produces one round-trip,
  not one per frame), serializes the selected lane's current notes plus
  context to a temp file, runs the CLI verb through the existing
  `job_runner` detached-subprocess + log-tail pattern, and merges the
  returned note-list diff into the in-memory data model before a single
  `step_editor.commit()` — the same shape every other tab already uses
  for generation, aimed at one lane instead of a whole pattern.
- Accept, for v1, that this blocks every other tab's Generate button for
  the round-trip (~1-2s expected). Do **not** generalize `job_runner` to
  support multiple named concurrent jobs as part of this feature — that's
  a real refactor every other tab depends on, unqualified by any evidence
  yet that the single-job gate is actually a problem in practice for a
  personal tool.

## Consequences

- Amount reuses established patterns end to end (job_runner async
  execution, the flat-JSON bridge convention, `GhostNoteLayer` for
  ghost-note insertion) instead of inventing a new IPC mechanism, and is
  testable as ordinary Python like every other modification.
- Amount is the only Step Editor control with round-trip latency and a
  subprocess failure mode that grid clicks and the other macro controls
  (pure in-process Lua) don't have.
- Turning an Amount knob visibly blocks other tabs' Generate buttons for
  the round-trip window — a real, known UX limitation accepted rather
  than solved, which could surprise a user running Amount adjustments
  back-to-back across several lanes.
- The lowest-velocity-first removal heuristic is a deliberate
  simplification with no claim of fidelity to Toontrack's behavior; it
  will need revisiting once real usage surfaces cases where it picks
  poorly (e.g. removing a musically load-bearing accent because it
  happens to be quiet).
- `job_runner`'s single-global-job constraint is reaffirmed as an
  acceptable, load-bearing limitation for this tool rather than something
  every new async feature must design around — revisit only if usage
  demonstrates it's actually a nuisance, not preemptively.

## Implementation note (2026-09-15)

The Python side is implemented as designed above:
`midi_drums/modifications/density_control.py`'s `adjust_density(notes,
amount, kind, grid_resolution, ts_num=4, ts_denom=4, bars=1,
context=None)` and the `adjust-density` CLI verb in `midi_drums/api/cli.py`
(`--input`/`--output` JSON files, `--instrument`, `--amount`, `--kind`,
`--grid`, `--ts-num`/`--ts-denom`, `--bars`, optional
`--genre`/`--style`/`--drummer`/`--complexity`). Two deliberate deviations
from the decision text above, both load-bearing rather than incidental:

- `ts_num`/`ts_denom`/`bars` were added as explicit parameters (not just
  `grid_resolution`) because `steps_per_bar` needs a full time signature,
  and the insertion pass needs to know how many bars to walk — the
  original signature undercounted what the function actually needs.
- Notes round-trip **without `ppqpos`** — only `bar`/`step`/`velocity`/
  `off_grid`/`_idx` (mirroring `reaper/midi_drums/step_editor.lua`'s
  `lane.notes` shape minus the REAPER-only fields). This module has no way
  to compute a real take-local tick position, so it stays in the abstract
  bar/step grid; resolving new notes' `ppqpos` (via `step_to_ppq`) is the
  Lua-side merge's job, not Python's.

Tests: `tests/unit/modifications/test_density_control.py` (unit-level,
100% coverage) and `tests/unit/api/test_cli_adjust_density.py`
(arg-parsing + file round-trip).

**Not yet done**: the Lua-side half described in the Decision section —
wiring the Step Editor's Amount slider to serialize a lane, shell out
through `job_runner`, and merge the result back via `step_editor.commit()`.
The panel's Amount slider (`reaper/midi_drums_panel.lua`) is still the
disabled placeholder added in ADR 0009; its help text was updated to
reflect that the Python side now exists but the control itself doesn't
call it yet. Status stays "Accepted" rather than fully "Shipped" until
that wiring lands.

## References

- [`claudedocs/design_step_editor_grid.md`](../../claudedocs/design_step_editor_grid.md)
  (Revision 2), "Amount's Python-side requirement" section
- [`claudedocs/research_ezdrummer3_editplaystyle_20260914.md`](../../claudedocs/research_ezdrummer3_editplaystyle_20260914.md)
- `midi_drums/modifications/drummer_mods.py` — `GhostNoteLayer`
- `reaper/midi_drums/job_runner.lua` — single-global-job execution model
- [ADR 0009](0009-unified-step-editor-panel.md) — the Step Editor panel
  this control lives inside, and the provenance metadata this decision
  depends on
- Not yet implemented; source design/research docs remain active in
  `claudedocs/` until this ships, at which point this ADR's status moves
  to Accepted and those docs are archived per `claudedocs/README.md`.
