# Design: Unified Step Editor + Play Style Panel for the REAPER Panel

**Status**: proposed, not yet implemented. **Revision 2** — unifies the
original raw step-grid design (Revision 1, below) with the "Edit Play
Style"-style macro layer identified in
`claudedocs/research_ezdrummer3_editplaystyle_20260914.md`. One tab, one
shared data model, two interaction modes (direct grid edits and macro
controls) — not two separate tools bolted together. This revision
supersedes Revision 1's tab structure; the rationale sections it carries
forward (why not a hardcoded Lua drum-note table, etc.) still hold.

## Context

Today the pipeline is one-directional: Python generates a `Pattern`,
exports it to a `.mid` file, and `sections.lua`/`riff_lock.lua`/
`additive_rhythm.lua`'s `on_complete` callbacks hand it to
`reaper.InsertMedia()`. Once it lands on the timeline it's a normal
REAPER MIDI item — editable only via the piano roll, with no connection
back to the panel that made it. There is no manual-editing path.

A first pass at fixing this (Revision 1) scoped a raw step-grid editor —
directly analogous to EZdrummer 3's Grid Editor. A follow-up research
pass then looked at EZdrummer 3's *other* editing tool, Edit Play
Style, which the user's original brief had actually named. That research
found Edit Play Style is not a grid tool at all — it's a higher-level
macro layer (Power Hand lane reassignment, articulation swap, velocity
scaling and contour presets, and an "Amount" knob for musically-aware
note density) that EZD3 keeps *alongside* its own Grid Editor, each
tool serving a different editing need. This revision folds both into
one panel tab rather than building them as two separate features, since
they operate on the exact same underlying pattern data and the same
REAPER MIDI item.

## Why not a hardcoded Lua drum-note table

`midi_drums/core/models/kit.py`'s `DrumKit` is already the single source
of truth for note mappings, and it is not static: 11 presets
(`ezdrummer3`, `gm_drums`, `ml_drums`, `bfd3`, ...), each resolving all 21
`DrumInstrument` enum members (`midi_drums/core/value_objects/
drum_instrument.py`) through `get_midi_note()` with per-preset
`custom_mappings` overrides (e.g. the `_GM_HIHAT_COLLAPSE` table that
folds EZDrummer 3's 8 extended hi-hat articulation notes down to GM's
plain `CLOSED_HH`/`OPEN_HH` for GM-compliant presets). A second,
hand-maintained copy of "note → label" living in Lua would drift from
this the first time a preset's mapping changes — the exact failure mode
`CLAUDE.md` already calls out for genre/style/drummer lists ("a
hardcoded Lua list would go stale the same way a hand-maintained doc
does") and solves the same way: `options.lua` shells out to
`python -m midi_drums list options` rather than hand-copying the plugin
registry into Lua. The note map — and, as it turns out, the sibling-
articulation groupings the macro layer needs (see below) — should get
the same treatment.

## Decision overview

1. New CLI verb, `list kit-map --mapping <preset>`, exposing a given
   `DrumKit` preset's resolved note→label table (grouped by
   kick/snare/hihat/toms/cymbals/ride, with sibling articulations tagged
   so the macro layer's "swap articulation" control has something to
   offer) as JSON — Python stays the single source of truth.
2. One new Lua module, `reaper/midi_drums/step_editor.lua`, holding
   **both** the raw grid operations and the macro operations, all
   mutating one shared in-memory data structure before a single commit
   step writes changes to the REAPER MIDI item.
3. One new panel tab, "Step Editor," with two visually distinct regions
   — a macro control strip and the grid itself — that both read and
   write the same tab-local state.
4. The grid is a **quantized projection over exact-PPQ data**, not the
   source of truth itself (see Data Model below) — this matters more
   now than in Revision 1, because macro operations like velocity
   scaling or lane reassignment must preserve a note's exact humanized
   timing, not just its snapped step position.

## Unified data model

Revision 1 sketched `grid[lane][bar][step]` as if it were the source of
truth. Revision 2 makes the **per-lane note list** the source of truth,
with the step/bar grid as a derived view:

```
data
├─ bars              int
├─ grid_resolution   "8th" | "16th" | "32nd" | "8th_triplet" | "16th_triplet"
│                     (one of step_editor.GRID_RESOLUTIONS)
├─ lanes             map: lane_key -> Lane        e.g. "kick", "snare", "hihat", ...
│    Lane
│    ├─ label         string     e.g. "Kick"
│    ├─ note          int        resolved MIDI note, from the kit-map
│    ├─ group         string     "kick" | "snare" | "hihat" | "toms" | "cymbals" | "ride"
│    └─ notes         list of Note
│         Note
│         ├─ bar        int    ┐ display projection: nearest grid line,
│         ├─ step       int    ┘ recomputed from ppqpos whenever grid_resolution changes
│         ├─ ppqpos     int    exact REAPER position — the real source of truth
│         ├─ velocity   int    1-127
│         └─ off_grid   bool   true when ppqpos doesn't land on a grid line, within tolerance
└─ dirty             list of {note reference, action: "add" | "remove" | "move"}
                      touched since the last commit() — see M.commit below
```

- `bar`/`step` are the *display* projection (nearest grid line) used for
  rendering and for direct-click editing; `ppqpos` is the note's real
  position and is what every macro operation (reassign, scale, style)
  actually reads and writes. A note flagged `off_grid` keeps its exact
  `ppqpos` through any macro operation that doesn't touch its timing —
  only a direct grid click (which by definition targets a specific
  step) snaps a note onto the grid.
- `M.commit(item, data)` is the **only** function that calls REAPER's
  `MIDI_InsertNote`/`MIDI_SetNote`/`MIDI_DeleteNote`/`MIDI_Sort`, applied
  to whatever's tracked in `data.dirty`, wrapped in one
  `Undo_BeginBlock`/`Undo_EndBlock` pair. Both a single grid-cell toggle
  and a whole-lane macro operation go through this same function — a
  click commits a one-note diff, a "reassign lane" click commits every
  note in that lane at once, but it's the same code path either way,
  and each commit is exactly one undo step regardless of how many notes
  it touched.

## Interaction model — two regions, one state

### 1. Grid (direct manipulation) — unchanged from Revision 1

Rows are lanes (grouped kick / snare / hi-hat / toms / cymbals / ride,
extended hi-hat articulations collapsed into a sub-section by default);
columns are `bars * steps_per_bar` with separators at step and bar
boundaries. A cell click toggles a note at that lane/bar/step at the
lane's default velocity (from the kit-map's `default_velocity`); a
modifier-click opens a velocity popup. Each click calls `commit`
immediately — same as Revision 1.

### 2. Macro Controls strip (the "Play Style" layer) — new in Revision 2

Sits above the grid. Every control here acts on the **currently
selected lane(s)** — a checkbox per grid row plus "select group"/
"select all" quick buttons is the single, shared selection mechanism
for every macro control below (this is the Groove-Parts-menu
equivalent from the research report, generalized to one place instead
of a per-control question):

- **Reassign** — dropdown listing every other lane present in the
  current kit-map, plus an Apply button. Moves every note in the
  selected lane(s) to the target instrument's note number; `ppqpos` and
  `velocity` are untouched. This is the Power Hand equivalent; EZD3's
  literal drag gesture is deliberately replaced with dropdown+button
  here (see Fork 3 below) rather than built with ReaImGui's
  drag-and-drop API.
- **Swap articulation** — dropdown scoped to *sibling* notes sharing
  the selected lane's `group` (e.g. the closed-hi-hat family), plus
  Apply. Same mutation shape as Reassign, just constrained to siblings.
- **Velocity scale** — a slider (e.g. 0.5x-2.0x). Live-previews in the
  grid while dragging (visual only, no REAPER writes yet); commits once
  on release (`ImGui_IsItemDeactivatedAfterEdit`) so a drag produces one
  undo step, not one per frame.
- **Velocity style** — dropdown of a small, fixed set of named
  per-step-position multiplier curves (e.g. "flat," "crescendo,"
  "halftime accent," "backbeat emphasis") plus an Apply button. Unlike
  the drum-note map, this genuinely is a fixed set worth hardcoding in
  Lua — it's a stylistic curve library, not plugin-discovered data with
  a Python-side source of truth.
- **Amount** — a signed slider (roughly -1.0..+1.0: remove ↔ add) per
  selected lane. When the lane's `group` is `"snare"`, a second toggle
  switches the knob's target between main hits and ghost notes only,
  mirroring EZD3's split. This is the one control that leaves the pure
  Lua/REAPER-API world — see below.

## Amount's Python-side requirement (correcting the research report)

The research report's mapping table said reusing `GhostNoteLayer` for
the ghost-note Amount case was "close to a direct reuse." On a closer
look at `midi_drums/modifications/drummer_mods.py`, that overstates it:
`GhostNoteLayer` (and the other modifications there) only *add* notes
at a fixed intensity — there is no existing signed, continuous,
bidirectional "add or remove hits" operation anywhere in the codebase.
The Amount knob is genuinely new Python work, not a port:

- New module, sketch: `midi_drums/modifications/density_control.py`,
  `adjust_density(notes, amount, kind, grid_resolution, context=None)`.
  Positive `amount` biases toward inserting additional plausible hits
  (the ghost-note case can lean on `GhostNoteLayer`'s existing insertion
  logic); negative `amount` removes existing hits, weighted toward the
  lowest-velocity/least-accented ones first — a simple, defensible
  heuristic, explicitly *not* claimed to reproduce Toontrack's
  undisclosed algorithm (see the research report's evidence-gap note).
- New headless entrypoint following this project's existing "flat JSON
  in, flat JSON out" convention for every Lua↔Python bridge:
  `python -m midi_drums adjust-density --input notes.json --instrument
  kick --amount 0.3 --kind main --grid 16th --output result.json`.
- On the Lua side: on slider release, serialize the selected lane's
  current notes plus bar count/grid resolution (and, when available,
  the item's persisted original generation context — see Fork 1) to a
  temp JSON file, kick an async `job_runner` job running the entrypoint
  above, and on completion merge the returned note-list diff into
  `data` and `commit` it in one undo block — the same async
  fire-and-forget shape every other tab already uses for generation,
  just aimed at one lane's worth of notes instead of a whole pattern.
- Should degrade gracefully (ignore genre/style/drummer context and
  fall back to a context-free heuristic) when no generation-provenance
  metadata is available for the item, rather than refusing to run.

## Resolved forks (the unification answers these)

- **Groove Parts / lane-selection scope.** Revision 1 didn't have this
  question yet since it had no macro layer. Resolved: one shared
  multi-select mechanism (checkboxes + quick buttons) drives every
  macro control, not a per-control ad hoc selector.
- **"Which tool is this."** Resolved: one tab, one `data` structure.
  Grid clicks and macro controls are two ways of mutating the same
  state, not two competing tools — matching how EZD3 itself treats Edit
  Play Style and the Grid Editor as complementary views over one
  groove, not alternatives to choose between.

## Open forks (need a decision before implementation starts)

1. **Mapping-metadata / generation-provenance.** Carried forward from
   Revision 1, now load-bearing for Amount too rather than a
   nice-to-have: the panel doesn't currently persist per-item generation
   metadata (which `--mapping`, `--genre`, `--style`, `--drummer`,
   `--complexity` produced a given item) anywhere.
   - *(a)* v1: ask again in the Step Editor tab (mapping only); Amount
     runs context-free. Simplest, and safe — a wrong/missing mapping
     just yields "Unmapped note" rows or a context-free density
     heuristic, not a crash.
   - *(b)* Write the full generation context into the item's own
     `P_NOTES` metadata (`GetSetMediaItemInfo_String`) at import time in
     every `import_midi`-equivalent call site, then read it back here.
   - **Recommendation: (b)**, more strongly than in Revision 1 — Amount
     genuinely benefits from knowing the original context, not just the
     note map.
2. **job_runner concurrency (new in Revision 2).** `job_runner.lua` was
   built around one global running job — every tab's Generate button is
   gated on nothing else running. Routing Amount through it means
   turning an Amount knob blocks every *other* tab's Generate button for
   the round-trip (likely ~1-2s).
   - *(a)* Accept it. Amount calls are short and infrequent; a "one
     thing running at a time" gate is arguably fine for a personal tool.
   - *(b)* Generalize `job_runner` to support multiple named concurrent
     jobs — a real refactor every other tab depends on.
   - **Recommendation: (a)** for v1; revisit only if Amount turns out to
     be used often enough for the global gate to actually bother anyone.
3. **ReaImGui drag substitution.** EZD3's Power Hand/articulation
   controls are literal drag gestures. ReaImGui supports drag-and-drop
   (`ImGui_BeginDragDropSource`/`Target`), but it's meaningfully more
   code than a dropdown+button for the identical net effect.
   **Recommendation:** dropdown+button for v1; revisit drag-and-drop
   only if specifically requested after using the simpler version.
4. **Velocity-style preset content.** The mechanism is specified above;
   the actual curve library (which named presets ship, and their exact
   multiplier tables) is a content decision for implementation time, not
   an architecture one.
5. **Editable-item scope**, carried forward unchanged: only
   panel-generated items, or any MIDI item on any track?
   **Recommendation: general-purpose** — once `commit`/the read path
   exist, restricting them buys nothing.
6. **Multi-bar navigation**, carried forward unchanged: one wide
   scrollable grid vs. paginated "bar N of M." **Recommendation:
   paginated** — ReaImGui tables get unwieldy past ~64-128 columns, and
   riff-lock already treats "one representative bar" as the unit of
   analysis.

## Non-goals (v1)

- Audio preview on click (stretch — `reaper.StuffMIDIMessage` could
  give immediate note-on/off audition; not required for "manual editing
  ability").
- Reproducing Toontrack's actual Amount/variation algorithm — the
  density heuristic above is original and explicitly simpler; see the
  research report's evidence-gap note on why a faithful port isn't
  possible (no public technical description exists).
- Editing non-drum-channel notes, or non-percussion items generally.
- Pattern-level operations beyond what's listed above (fill generation,
  copy/paste between bars) — this is a step/macro editor for
  hand-correcting a generated result, not a replacement for
  `DrumGenerator`.
- New vendor-specific note research (ML Drums, BFD3, Studio Drummer 3,
  MODO Drums, Addictive Drums 2 are all still on the GM-collapsed
  baseline per `kit.py`'s own docstrings).

## Component design reference (Lua module surface)

Function-level spec (interfaces, not full implementation) for
`reaper/midi_drums/step_editor.lua`:

- `M.GRID_RESOLUTIONS` — reuse the fixed set already defined for
  riff-lock's `--grid` (`8th`, `16th`, `32nd`, `8th_triplet`,
  `16th_triplet`).
- `M.steps_per_bar(grid_resolution, ts_num, ts_denom)` — pure helper.
- `M.read_pattern_from_item(item, kit_map, grid_resolution) ->
  data, err` — builds the data model above from `MIDI_GetNote` output,
  filtered to the drum channel, bucketing each note to its nearest
  bar/step (flagging `off_grid` past a small tolerance) while retaining
  exact `ppqpos`. Unmapped pitches become an `"Unmapped (note N)"` lane
  rather than being dropped from view.
- `M.toggle_step(data, lane, bar, step, velocity)` — direct-grid
  mutation; marks the affected note dirty.
- `M.reassign_lane(data, from_lanes, to_lane)` — macro mutation; changes
  `note`/lane membership for every note in the given lane(s), preserving
  `ppqpos`/`velocity`; marks all affected notes dirty.
- `M.swap_articulation(data, lanes, sibling_note)` — same shape as
  `reassign_lane`, constrained to siblings by the caller (UI only offers
  siblings in the dropdown).
- `M.scale_velocity(data, lanes, factor)` — macro mutation, clamps
  results to 1-127.
- `M.apply_velocity_style(data, lanes, preset_name)` — macro mutation
  using the fixed preset table (Fork 4).
- `M.request_amount_adjustment(data, lane, amount, kind, on_result)` —
  serializes the async Python round-trip described above; `on_result`
  merges the returned diff into `data` (does not commit).
- `M.commit(item, data)` — the single REAPER-mutating function described
  in the Data Model section; the only place `MIDI_InsertNote`/
  `MIDI_SetNote`/`MIDI_DeleteNote`/`MIDI_Sort`/`Undo_BeginBlock`/
  `Undo_EndBlock` are called.
- `M.render(ctx, data)` — pure-ish render call invoked from the panel;
  writes user interaction into `data`'s dirty set (for grid clicks) or
  returns a pending macro action (for macro controls) rather than
  calling `commit` itself — the panel tab decides when to commit, same
  separation `sections.lua`/`riff_lock.lua` already keep between
  *building* a command and the panel deciding *when* to run it.

## Data flow

```
Generate (existing)              Step Editor (new)
──────────────────               ─────────────────────────────────────
Python: pattern → .mid            "Load Selected Item" clicked
        │                          │
        ▼                          ▼
sections.import_midi()            selected item + take + kit-map
        │                          │
        ▼                          ▼
REAPER MIDI item  ◄────────── read_pattern_from_item() → data
   (source of truth)               │
        │                          ├─ grid click ──────► toggle_step(data)
        │                          ├─ Reassign/Swap ───► reassign_lane / swap_articulation(data)
        │                          ├─ Velocity/Style ──► scale_velocity / apply_velocity_style(data)
        │                          └─ Amount (async) ──► request_amount_adjustment(data) [job_runner]
        │                                                    │
        │                                                    ▼
        │                                             merges diff into data
        │                                                    │
        └───────────────────────────────────────────── commit(item, data)
                                                          (MIDI_Insert/Set/DeleteNote,
                                                           MIDI_Sort, one Undo block)
```

Only the Amount path touches `job_runner`/a Python subprocess; every
other edit — grid click or macro control — is pure in-process REAPER
API calls with no async round-trip.

## Python-side CLI verb (`list kit-map`)

```
python -m midi_drums list kit-map --mapping ezdrummer3
```

- `kit = DrumKit.from_preset(args.mapping)`; for each `DrumInstrument`,
  resolve `note = kit.get_midi_note(instrument)` and `group` via a
  shared constant lifted out of `get_velocity_range()`'s existing
  category-map body (so the CLI verb and the existing velocity lookup
  read one table, not two).
- **Dedupe by resolved note**, preferring the canonical GM-standard
  member (`CLOSED_HH`/`OPEN_HH`) over a vendor-specific alias when two
  `DrumInstrument` members land on the same note (this happens for
  every GM-collapsed preset).
- Output also carries enough to drive "swap articulation" — group
  siblings sharing a `group` and a common "base" note family:

```json
{
  "mapping": "ezdrummer3",
  "notes": [
    {"note": 36, "instrument": "KICK", "label": "Kick", "group": "kick", "default_velocity": 110},
    {"note": 38, "instrument": "SNARE", "label": "Snare", "group": "snare", "default_velocity": 115},
    {"note": 42, "instrument": "CLOSED_HH", "label": "Closed Hi-Hat", "group": "hihat", "default_velocity": 80},
    {"note": 61, "instrument": "CLOSED_HH_TIP", "label": "Closed Hi-Hat (Tip)", "group": "hihat", "default_velocity": 80}
  ]
}
```

`options.lua` gets a matching cache extension: `options.build_kit_map_cmd`,
`options.parse_kit_map`, `options.cache.kit_maps[mapping]` — same
lazy-fetch-and-cache shape as the existing `genres`/`drummers`/
`mappings` cache.

## References

- `claudedocs/research_ezdrummer3_editplaystyle_20260914.md` — source
  of the Play Style mechanisms unified into this revision
- `midi_drums/core/models/kit.py` — `DrumKit`, `from_preset`,
  `get_midi_note`, `get_velocity_range`'s category map
- `midi_drums/core/value_objects/drum_instrument.py` — `DrumInstrument`
  enum (21 members, incl. EZDrummer-3-specific extended hi-hat notes)
- `midi_drums/modifications/drummer_mods.py` — `GhostNoteLayer` and the
  existing modification shape `density_control.py` should follow
- `midi_drums/api/cli.py` — existing `list` subcommand family
- `reaper/midi_drums/options.lua` — cache-and-shell-out pattern to
  extend for kit-maps
- `reaper/midi_drums/job_runner.lua` — single-global-job model relevant
  to Fork 2
- `reaper/midi_drums/sections.lua`, `riff_lock.lua` — existing
  `import_midi`/bar-alignment logic to reuse
- `reaper/midi_drums_panel.lua` — tab structure, `combo_from_list`,
  `draw_help_button`, `job_runner` integration conventions
- REAPER ReaScript API: `MIDI_CountEvts`, `MIDI_GetNote`,
  `MIDI_InsertNote`, `MIDI_SetNote`, `MIDI_DeleteNote`, `MIDI_Sort`,
  `MIDI_GetProjQNFromPPQPos`, `GetSetMediaItemInfo_String`,
  `ImGui_BeginDragDropSource`/`Target`, `ImGui_IsItemDeactivatedAfterEdit`
