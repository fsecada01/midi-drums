# 0011. Apply Drummer (Step Editor humanization) is a whole-pattern Python round-trip, mirroring ADR 0010's shape

> **Status**: Proposed
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
  velocity_variance, grid_resolution, ts_num=4, ts_denom=4)`**: converts
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
