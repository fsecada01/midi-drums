# 0009. Unified Step Editor panel: one data model over the live REAPER MIDI item, no parallel pattern format

> **Status**: Proposed
> **Date**: 2026-09-14

## Context

Generation is one-directional: Python builds a `Pattern`, exports a
`.mid`, and `sections.lua`/`riff_lock.lua`/`additive_rhythm.lua` hand it
to `reaper.InsertMedia()`. Once it lands on the timeline it's an ordinary
REAPER MIDI item, editable only via the piano roll, with no path back to
the panel. There is no manual-editing capability for a generated pattern.

An external brief proposed two shapes for that capability: a raw step-grid
editor (Option 1), or exporting/importing REAPER note-name text files
(Option 2), and separately suggested hardcoding a GM drum-note table in
Lua to drive it. Option 1 was chosen, but the hardcoded-table suggestion
was rejected: `midi_drums/core/models/kit.py`'s `DrumKit` is already the
single source of truth for note mappings across 11 presets, each with its
own `custom_mappings`/`_GM_HIHAT_COLLAPSE`-style overrides, and a
hand-maintained second copy in Lua would drift the same way this codebase
has already ruled out for genre/style/drummer lists (`options.lua` shells
out to `python -m midi_drums list options` for exactly that reason).

A follow-up research pass (`claudedocs/research_ezdrummer3_editplaystyle_20260914.md`)
looked at EZdrummer 3's separate "Edit Play Style" feature — a
higher-level macro layer (drag-to-reassign leading instrument,
articulation variants, a "resolution" hint, Amount knobs for
musically-aware density, velocity scaling and named velocity-style
presets) that Toontrack ships *alongside* its own grid editor, not as a
replacement for it. That research initially recommended the macro layer
as a sequential v2 follow-up to the grid. On review, both operate on the
same underlying pattern data and the same REAPER MIDI item, and building
them as two separate tabs/tools would duplicate the read/write/undo
plumbing for no benefit — the full design is in
`claudedocs/design_step_editor_grid.md` (Revision 2).

## Decision

Build one new panel tab, "Step Editor," backed by one shared in-memory
data model, that reads and writes the REAPER MIDI item directly via the
ReaScript MIDI API (`MIDI_GetNote`/`MIDI_InsertNote`/`MIDI_SetNote`/
`MIDI_DeleteNote`/`MIDI_Sort`) — never a second, parallel JSON
pattern-export format.

- **Data model**: per-lane note lists (`data.lanes[key].notes`), each note
  carrying its exact `ppqpos` (source of truth) plus a derived `bar`/
  `step` display projection recomputed from `ppqpos` and the active
  `grid_resolution`. A note whose position doesn't land on a grid line
  within tolerance is flagged `off_grid` and keeps its exact timing
  through anything that isn't a direct grid click.
- **One commit path**: `M.commit(item, data)` in a new
  `reaper/midi_drums/step_editor.lua` module is the *only* function
  allowed to call REAPER's MIDI-mutating API, wrapped in one
  `Undo_BeginBlock`/`Undo_EndBlock` pair. A single grid-cell toggle and a
  whole-lane macro operation (reassign, articulation swap, velocity
  scale, velocity style) both resolve to one `commit()` call — one user
  action, one undo step, regardless of how many notes it touches.
- **Note mapping stays Python-sourced**: a new CLI verb,
  `python -m midi_drums list kit-map --mapping <preset>`, resolves
  `DrumKit.get_midi_note()`/`get_velocity_range()` into a note→label/group
  JSON table (with sibling-articulation grouping, for the macro layer's
  "swap articulation" control), fetched and cached by `options.lua` the
  same way genre/drummer/mapping lists already are.
- **Generation provenance** (which `--mapping`/`--genre`/`--style`/
  `--drummer`/`--complexity` produced a given item) is written into the
  item's own `P_NOTES` metadata at import time
  (`GetSetMediaItemInfo_String`) and read back by the Step Editor tab,
  rather than re-prompted on every load.
- **Editable scope is general-purpose**: any MIDI item on the drum
  channel, not restricted to panel-generated items — once the read/write
  path exists, restricting it buys nothing.
- **Power Hand-equivalent controls (reassign lane, swap articulation) are
  dropdown + Apply button**, not ReaImGui drag-and-drop — same net effect
  for meaningfully less code; revisit only if specifically requested
  after using the simpler version.
- **Multi-bar navigation is paginated** ("bar N of M"), not one wide
  scrollable grid — ReaImGui tables get unwieldy past ~64-128 columns, and
  riff-lock already treats "one representative bar" as its unit of
  analysis.
- A small, fixed table of named velocity-style curves (e.g. "halftime
  accent") is hardcoded in Lua. This is the one deliberate exception to
  "don't hardcode what Python can report": it's an original stylistic
  curve library with no existing Python source of truth, not
  plugin-discovered data that can drift.

Amount (musically-aware density add/remove) is the one macro control that
needs a Python-side round-trip rather than pure Lua/REAPER-API logic —
that decision, and its interaction with `job_runner.lua`'s single-job
model, is recorded separately in [ADR 0010](0010-amount-density-control-python-roundtrip.md).

## Consequences

- Editing always acts on whatever's actually on the timeline, including
  hand-tweaked items, and can never drift from `DrumKit`'s real mappings
  the way a hardcoded Lua table eventually would.
- No second pattern format to keep in sync with `.mid` exports or with
  future `DrumKit` changes.
- One undo step per user action regardless of scope (single note vs.
  whole lane), matching REAPER user expectations for the piano roll.
- Reading a pattern re-walks every `MIDI_GetNote` call on each load with
  no caching layer — acceptable at pattern-editing scale (a few hundred
  notes across a paginated bar range) but unaddressed for very large
  multi-bar selections; punted as a non-goal rather than solved
  speculatively.
- Provenance depends on every import/generate call site remembering to
  write `P_NOTES`; a call site that doesn't will degrade gracefully (the
  tab falls back to asking for the mapping only) rather than failing, but
  silently loses the richer context ADR 0010's Amount control depends on.
- General-purpose item scope means the tab can be pointed at non-generated
  or externally recorded MIDI, where `off_grid` flagging is intended for
  humanized takes but hasn't been validated against arbitrary external
  material.
- Establishes a precedent: panel features that operate on pattern data
  read/write the live REAPER MIDI item as source of truth, not a parallel
  export — extending the "don't hardcode what Python can report" rule
  from options data (genre/style/drummer/mapping) to note-mapping data.

## References

- Full design (data model, component specs, resolved and open forks):
  [`claudedocs/design_step_editor_grid.md`](../../claudedocs/design_step_editor_grid.md)
  (Revision 2)
- Research grounding this decision against EZdrummer 3's real feature:
  [`claudedocs/research_ezdrummer3_editplaystyle_20260914.md`](../../claudedocs/research_ezdrummer3_editplaystyle_20260914.md)
- `midi_drums/core/models/kit.py` — `DrumKit`, `get_midi_note`,
  `get_velocity_range`
- `midi_drums/core/value_objects/drum_instrument.py` — `DrumInstrument`
- `reaper/midi_drums/options.lua` — shell-out/cache pattern extended for
  `list kit-map`
- Related: [ADR 0001](0001-unified-reaper-panel.md) (panel architecture
  this tab extends), [ADR 0008](0008-vendor-midi-note-map-corrections.md)
  (why note-mapping accuracy is treated as load-bearing, not guessed)
- Not yet implemented; source design/research docs remain active in
  `claudedocs/` until this ships, at which point this ADR's status moves
  to Accepted and those docs are archived per `claudedocs/README.md`.
