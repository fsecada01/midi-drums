# 0001. Unified REAPER panel replaces three standalone Lua scripts

> **Status**: Accepted (implemented, shipped in v0.4.0-alpha.1)
> **Date**: 2026-08-21

## Context

REAPER integration originally shipped as three independent Lua scripts
(`create_song_sections.lua`, `create_beat_from_riff.lua`,
`midi_drums_help.lua`), each maintained separately with its own dialog
flow, its own `ExtState` handling for the Python interpreter path, and no
shared code between them. Every generation call used `io.popen` and
blocked REAPER's UI thread until the Python subprocess finished — fine for
template generation (1-2s) but unacceptable for AI-backed generation
(20-45s), during which the entire DAW appeared frozen. Adding new modes
(sidecar, AI, song-map) meant growing that duplication further across
scripts that already didn't share logic.

## Decision

Replace all three scripts with a single dockable ReaImGui panel
(`reaper/midi_drums_panel.lua`) with four tabs — Song Sections, Riff-Lock
Beat, Settings, Log — backed by shared Lua modules under
`reaper/midi_drums/`: `job_runner.lua` (detached-subprocess execution,
log-tail + `DONE <exitcode>` marker instead of a blocking `io.popen`
read), `sections.lua` and `riff_lock.lua` (business logic lifted from the
two retired scripts), and `settings.lua` (consolidated `ExtState`
configuration, including `resolve_python_exe()` so no tracked file ever
hardcodes a machine-local Python path). ReaImGui is a hard prerequisite —
no fallback UI path; a missing install shows the ReaPack setup steps
inline rather than failing with a raw Lua error. Only the job runner's
`on_complete` callback (fired after a successful `DONE 0`) is allowed to
mutate REAPER project state, so a failed or partial subprocess run never
leaves the project half-mutated.

## Consequences

- One panel, one settings surface, one log view — adding a fifth mode (as
  song-map mode already did) extends existing tabs instead of writing a
  fourth standalone script.
- The panel's UI thread is never blocked, including during 20-45s AI
  generation calls, at the cost of a slightly more complex execution
  model (temp `.bat` launcher + log-file tailing per job) than a direct
  blocking call would have needed.
- v1 scope accepted: no automated Lua test runner exists in this repo, so
  every task in the implementation plan was verified by manual, exact
  REAPER steps rather than an automated suite. ReaImGui's exact function
  signatures could only be spot-checked against a live installed version,
  not verified in CI.
- The three retired scripts (including the still-present but
  intentionally unvendored `drum_midi_generator.lua`, which predates the
  sidecar bridge entirely) are documented as superseded in
  `reaper/README.md` rather than deleted from users' local REAPER
  installs by this change — REAPER only loads scripts from its own
  `Scripts/` directory, which this repo doesn't control.

## References

- Full design doc (motivation, requirements, non-goals, architecture,
  UI mockup, data flow, error-handling table): [`claudedocs/archive/2026-08-21_docs-cleanup/design_reaper_panel.md`](../../claudedocs/archive/2026-08-21_docs-cleanup/design_reaper_panel.md)
- Full task-by-task implementation plan: [`claudedocs/archive/2026-08-21_docs-cleanup/2026-08-21-unified-reaper-panel-plan.md`](../../claudedocs/archive/2026-08-21_docs-cleanup/2026-08-21-unified-reaper-panel-plan.md)
- Shipped in `reaper/midi_drums_panel.lua` + `reaper/midi_drums/`, released in v0.4.0-alpha.1
- User-facing docs: [`reaper/README.md`](../../reaper/README.md)
