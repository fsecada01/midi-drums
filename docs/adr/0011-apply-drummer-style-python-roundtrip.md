# 0011. Apply Drummer (Step Editor humanization) is a whole-pattern Python round-trip, mirroring ADR 0010's shape

> **Status**: Accepted (fully implemented)
> **Date**: 2026-09-15

## Context

The Step Editor (ADR 0009) can reassign, swap articulation, and scale
velocity — all pure Lua/REAPER-API note-list edits. It has no way to make
a programmed, quantized pattern feel like a specific drummer actually
played it. That capability already exists on the Python side:
`PluginManager.apply_drummer_style(pattern, drummer, intensity)` (used by
`generate`/`additive-rhythm`/`riff`) applies a drummer plugin's composed
modifications (`BehindBeatTiming`, `TripletVocabulary`, `GhostNoteLayer`,
etc. — see `midi_drums/modifications/drummer_mods.py`), and
`Pattern.humanize(timing_variance, velocity_variance)` independently adds
random per-note timing/velocity jitter. Neither is reachable from the
Step Editor today — they only run during initial generation.

Unlike Amount (ADR 0010), which only ever targets exact grid slots within
one lane, this operates across the whole kit at once: `GhostNoteLayer`
inserts new snare hits regardless of which lane a user has checked, and
`BehindBeatTiming`/`TripletVocabulary` reason about relationships between
instruments (e.g. snare against kick). Scoping it to selected lanes only
would silently break exactly the techniques it exists to apply. It also
produces genuinely off-grid timing by design — humanization's entire
purpose is positions that don't land on a step boundary — which ADR
0010's bar/step-only round-trip shape can't represent losslessly.

## Decision

Add a new whole-pattern Python round-trip, `apply_drummer(...)` in a new
`midi_drums/modifications/apply_drummer.py` module, invoked through a new
`apply-drummer-style` CLI verb and reached from the Step Editor tab's own
"Apply Drummer" control row (separate from the lane-scoped Macro Controls
strip, since it always acts on the whole loaded pattern).

- **Round-trip shape diverges from ADR 0010's on purpose**: notes carry an
  `instrument` field (the lane key, since this is whole-pattern not
  single-lane) and a `position_qn` float (exact quarter-notes from pattern
  start) instead of integer `bar`/`step`. `position_qn` is what survives
  humanization's continuous timing jitter; `bar`/`step` would silently
  round it back onto the grid and defeat the feature. `ppqpos` is still
  never computed in Python — the Lua-side merge resolves `position_qn` to
  a real take-local `ppqpos` via the same `ppq_per_qn`/`item_start_ppq`
  factors `step_editor.lua` already caches on `data` (a small public
  `M.qn_to_ppq(data, qn)`, factored out of the existing private
  `step_to_ppq`).
- **`apply_drummer(notes, drummer, intensity, timing_variance,
  velocity_variance, ts_num=4, ts_denom=4)`**: converts
  the flat note list to `Beat`/`Pattern` objects (`DrumInstrument[lane_key]`
  for the instrument, `position_qn` for `Beat.position`), runs
  `PluginManager.apply_drummer_style` (skipped entirely if `drummer` is
  falsy), then `Pattern.humanize(timing_variance, velocity_variance)`
  (skipped if both variances are `0.0`, matching Amount's `amount == 0.0`
  no-op convention), then converts back. A note whose `instrument` isn't a
  recognized `DrumInstrument` member (e.g. an "Unmapped (note N)" lane)
  passes through completely untouched rather than erroring the whole
  request — drummer plugins have no concept of an unmapped pitch, and
  losing that data on every unmapped hit would be worse than leaving it
  alone.
- **The Lua-side merge always replaces the whole pattern**, unlike
  Amount's per-note add/remove diff: drummer style application and
  humanization return a fundamentally new note list with no reliable
  identity mapping back to original REAPER event indices (`GhostNoteLayer`
  inserts, `BehindBeatTiming` repositions — there's nothing stable to diff
  against). `step_editor.lua` gets a new `M.replace_pattern(data,
  notes_by_lane)` that dirty-marks every existing note "remove" and every
  returned note "add," then a single `commit()` — same one-undo-step
  guarantee as every other macro operation, just applied to the entire
  loaded pattern instead of a lane's worth of cells.
- **Controls**, in a new row below the existing Macro Controls strip:
  Drummer dropdown (reuses `options.cache.drummers`, already fetched for
  other tabs), Drummer Intensity slider (0.0-1.0, matching the
  `--drummer-intensity` convention already used by Additive Rhythm/Song
  Sections/Riff-Lock), and separate Timing Variance / Velocity Variance
  sliders — mapped directly to `Pattern.humanize`'s two independent
  parameters rather than one combined "uniqueness" knob, since the two
  axes are genuinely independent (loose timing with consistent velocity
  is a different drummer feel than the reverse) and a combined knob would
  have to invent an arbitrary blend ratio between them. "Apply Drummer"
  routes through the existing `job_runner` detached-subprocess pattern
  (temp input/output JSON files, `on_complete` merges via
  `replace_pattern` + `commit()`), gated the same way every other tab's
  Generate button already is.
- Drummer is optional (blank = skip style application, humanize-only) and
  the two variance sliders default to `0.0` (no humanization) so a user
  can apply pure drummer-style repositioning without added jitter, or the
  reverse.

## Consequences

- Reuses `PluginManager.apply_drummer_style` and `Pattern.humanize`
  as-is — no new generative logic, unlike Amount which needed one
  (there's no existing "add/remove hits" operation to reuse; drummer style
  and humanization both already exist as exactly the operations wanted
  here).
- The whole-pattern-replace merge is simpler to reason about than a diff
  (no `_idx` bookkeeping across a plugin transform that doesn't preserve
  identity) but means "Apply Drummer" cannot be scoped to part of a
  pattern, and running it twice compounds humanization jitter each time
  rather than resetting from the original — a user who over-applies it
  has no built-in way back except REAPER's own undo stack (which still
  works normally, since it's still one `commit()` per click).
- `position_qn` makes this round-trip's shape incompatible with ADR
  0010's `adjust-density` shape (bar/step vs. position_qn, single-lane vs.
  whole-pattern) — they are deliberately two different CLI verbs with two
  different flat-JSON shapes rather than one unified "pattern round-trip"
  format, because forcing both into one shape would mean either Amount
  loses its simpler grid-slot semantics or Apply Drummer loses timing
  precision.
- An unmapped-pitch note (no `DrumInstrument` match) is invisible to
  drummer plugins by design — a pattern with, say, an unusual percussion
  overdub on an unmapped note will not get that instrument reconsidered
  by `BehindBeatTiming`/`GhostNoteLayer`, only passed through unchanged.
- Like Amount, this blocks every other tab's Generate button for the
  round-trip window (`job_runner`'s single-job constraint, reaffirmed in
  ADR 0010) — same accepted limitation, not re-litigated here.
- `Pattern.duration_bars()` infers bar count from the highest beat
  position present, not an explicit bar count — a pattern whose last
  bar(s) are genuinely empty will under-count them, so `GhostNoteLayer`
  (and any other bar-count-aware modification) won't consider inserting
  into a trailing all-empty bar. Accepted as a pre-existing `Pattern`
  limitation this feature inherits rather than one it introduces; fixing
  it would mean extending `Pattern`'s own API, out of scope here.

## Implementation note (2026-09-15)

The Python round-trip shipped exactly as decided above:
`midi_drums/modifications/apply_drummer.py`'s `apply_drummer(notes, drummer,
intensity, timing_variance, velocity_variance, ts_num=4, ts_denom=4,
plugin_manager=None)` and the `apply-drummer-style` CLI verb (`--input`,
`--output`, `--drummer`, `--drummer-intensity`, `--timing-variance`,
`--velocity-variance`, `--ts-num`, `--ts-denom`). `grid_resolution` was
dropped from the signature during implementation (see Decision text above,
already corrected) — it was never actually needed since `position_qn` plus
`TimeSignature` fully determine the round-trip without any grid-stepping.
25 tests across `tests/unit/modifications/test_apply_drummer.py` and
`tests/unit/api/test_cli_apply_drummer_style.py` cover validation,
passthrough of unmapped instruments, drummer styling (both a fake
`PluginManager` and two real-plugin end-to-end checks), humanization, and
the CLI's file round-trip/error paths.

**Lua-side wiring (2026-09-15)**: `step_editor.lua` gained `M.qn_to_ppq`
(factored out of the existing private `step_to_ppq`), plus three new
functions specific to this round-trip — `M.serialize_pattern_json(data)`
(flattens the whole loaded pattern into the input JSON), `M.parse_pattern_
json(content)` (parses the output JSON back into `{instrument,
position_qn, velocity}` entries), and `M.replace_pattern(data, notes)`
(dirty-marks every existing note "remove" and every returned note "add",
creating a lane on demand from `data.kit_map_by_key` when needed, e.g. a
previously note-less lane `GhostNoteLayer` just inserted into). One
deliberate shape simplification versus the Decision text above:
`replace_pattern` takes the CLI's actual flat note list directly rather
than a `notes_by_lane`-grouped table — grouping first would have been
pure indirection with no benefit, since `replace_pattern` iterates the
flat list once regardless. `midi_drums_panel.lua`'s Step Editor tab gained
an Apply Drummer row (Drummer dropdown, Intensity/Timing Variance/
Velocity Variance sliders, an Apply Drummer button gated the same way
every other tab's Generate button is) below the Macro Controls strip,
round-tripping through `job_runner` exactly as decided: write the whole
pattern to a temp input JSON, run the CLI verb, and on completion read
the output JSON, `replace_pattern` + `commit()` it back onto the item as
one undo step. `ghost_note`/`accent` are parsed out of the output JSON
but not stored — the Step Editor's note model has no field for them yet
(only velocity), the same limitation already noted above. 6 new Lua tests
in `reaper/tests/test_step_editor.lua` (22 total) cover `qn_to_ppq`, the
serialize/parse round-trip, and `replace_pattern` (whole-pattern replace,
on-demand lane creation, and silently dropping an instrument absent from
the kit map).

## References

- [ADR 0009](0009-unified-step-editor-panel.md) — the Step Editor panel
  this control lives inside
- [ADR 0010](0010-amount-density-control-python-roundtrip.md) — the
  sibling Python round-trip this decision explicitly diverges from on
  round-trip shape (position_qn vs. bar/step) and merge strategy (replace
  vs. diff), and shares (`job_runner` single-job constraint, flat-JSON
  convention)
- `midi_drums/plugins/registry/plugin_registry.py` —
  `PluginManager.apply_drummer_style`
- `midi_drums/core/models/pattern.py` — `Pattern.humanize`, `Beat`
- `midi_drums/core/value_objects/drum_instrument.py` — `DrumInstrument`
- `midi_drums/api/cli.py:handle_additive_rhythm_command` — precedent for
  a CLI handler applying drummer style outside the `generate` pipeline
- Not yet implemented; status moves to Accepted once the Python round-trip
  ships (matching ADR 0010's own status convention), independent of
  whether the Lua-side wiring lands in the same change.
