# Design: Additive Rhythmic Grouping → Time Signature

**Status**: spike / proposed, standalone prototype not wired into any
genre plugin or AI agent tool yet. New modules only; nothing existing is
modified except `MIDIEngine` gaining one new, additive method
(`bars_to_midi`/`save_bars_midi`) alongside its existing ones.

## Context

While designing how to tell the LLM pattern-generation agent about a
specific rhythmic subdivision (e.g. "16th notes grouped 3-3-3-3-2-2"),
the natural notation to reach for is additive box notation / **TUBS**
(Time Unit Box System) — the standard ethnomusicology convention for
irregular/compound meters (e.g. "3+3+2" = 8/8 Bulgarian rhythm, "2+2+3" =
7/8). The open question was how to convert a flat run of additive groups
into one or more properly-labeled `TimeSignature`s and an actual
beat-accented `Pattern`, since nothing in the codebase does this today —
every genre plugin hardcodes `TimeSignature(4, 4)`.

Worked example that anchored this design (confirmed with the user):
`3-3-3-3-2-2` at a 16th-note grid sums to 16 sixteenths — exactly one
4/4 bar's duration — and should resolve to **two** bars: 6/8 (the four
groups of 3) followed by 2/8 (the two groups of 2), not one bar
mislabeled 16/16 or fully reduced to 4/4 (which would erase the
compound/triple-grouping signal entirely).

## Two distinct notational intents, disambiguated by syntax

A flat list of additive groups is genuinely ambiguous between two
real, different musical intents, and no purely arithmetic rule can
recover the author's intent from the numbers alone:

1. **Repeated-pulse runs** (this spike's primary case): a run of
   *identical* group sizes represents one bar of that many repeated
   pulses — e.g. four groups of 3, then two groups of 2, is naturally
   two separate bars (6/8, then 2/8), because the pulse itself changed.
2. **One heterogeneous additive bar** (classic Balkan/TUBS notation):
   `2+2+3` is a *single* 7/8 bar, not three bars — the groups don't
   repeat, and combining them is the entire point of the notation.

This spike resolves the ambiguity with syntax rather than guessing:

- **No `|` in the input** → auto-detect mode: split the flat group
  sequence into maximal runs of identical consecutive values; each run
  is one bar (case 1 above).
- **`|` present** → explicit-bar mode: each `|`-delimited segment is
  taken as one bar exactly as written, however heterogeneous (case 2).
  `3+3+3+3|2+2` forces the same 6/8-then-2/8 split as the auto-detected
  case, spelled out explicitly. A single heterogeneous bar like `2+2+3`
  needs a trailing `|` (`2+2+3|`) to select explicit-bar mode at all — an
  empty trailing segment is silently dropped — since without any `|` the
  same digits would auto-split by run instead (`2-2` then `3`).

## Canonicalization rule (auto-detect mode only)

For a run of `count` identical groups of size `group_size` at grid
denominator `grid_denominator` (implemented as `_canonicalize_run` in
`midi_drums/core/value_objects/rhythmic_grouping.py`):

- **If `group_size` is itself a power of two** (simple/duple grouping —
  each group already *is* a beat, e.g. four groups of 4 sixteenths is
  four quarter-note beats): divide it straight out —
  `TimeSignature(count, grid_denominator // group_size)`. Four groups of
  4 sixteenths → `4/4`, not the un-reduced `16/16`. Two groups of 2
  sixteenths → `2/8` (this is how the confirmed example's tail group
  resolves — see below).
- **Otherwise** (compound grouping — e.g. groups of 3, which have no
  power-of-two group size to divide out cleanly): halve numerator and
  denominator **once**, only if both are even and the halved denominator
  stays ≥ 8. Four groups of 3 sixteenths → `12/16` → halve once → `6/8`.
  This is deliberately a single halving, not a full reduction to lowest
  terms — fully reducing `12/16` to `3/4` would destroy the
  compound-meter signal implied by grouping in 3s (three eighth notes
  per beat, not one quarter-note beat with no internal accent).

Explicit-bar mode applies the same canonicalization when a `|`-delimited
segment happens to be uniform (every group identical, e.g. `3+3+3+3`) —
there's no reason to treat it differently just because the bar boundary
was spelled out rather than auto-detected. Only a genuinely
*heterogeneous* segment (e.g. `2+2+3`, no repeated pulse to canonicalize
against) skips reduction entirely: `TimeSignature(sum(groups),
grid_denominator)` directly, exactly as classic TUBS notation intends
(`2+2+3` @ 8th-note grid → `7/8`, unchanged).

This is a heuristic, not exhaustive music theory — validated against the
one confirmed worked example plus a handful of sanity cases (see Tests
below), not against the full space of possible additive groupings. Group
sizes other than 2, 3, and 4 are untested in practice.

## Position mapping (grid units → beats)

`Beat.position` is expressed in quarter-note beats regardless of a
pattern's own denominator (same convention every existing genre plugin
already uses). One grid unit is therefore `4.0 / grid_denominator` beats
— e.g. a sixteenth note is `0.25` beats. A group's accent lands at the
cumulative grid-unit offset of all groups before it in the bar, converted
through that factor. This keeps positions consistent with
`TimeSignature.beats_per_bar` (e.g. `6/8` → `3.0` beats, `2/8` → `1.0`
beat), so nothing downstream needs to know the grid was ever involved.

## Pattern construction

`midi_drums/generation/builders/additive_rhythm_builder.py`:
`build_additive_rhythm_bars(spec, grid_denominator) -> list[Pattern]`.
For each resolved bar: a kick at every group's start position
(`VELOCITY.KICK_ACCENT`), plus a closed hi-hat on every grid unit
(`VELOCITY.HIHAT_LIGHT`) as a plain timekeeping layer so the result is
audible/legible on its own, not just a skeleton of kicks. Deliberately
minimal — no snare, no genre character, no drummer styling. This is a
standalone builder, not a genre-plugin method, since no genre plugin
supports non-4/4 generation today (see Non-goals).

## MIDI export: a new standalone path, not `Song`/`Section` reuse

The obvious reuse candidate was `Song`/`Section`/`SongSegment` +
`MIDIEngine.save_song_midi`, since `Section.segments` already models
"per-bar tempo/meter overrides within a section" and
`_add_section_to_midi` already emits `addTempo`/`addTimeSignature`
markers reacting to `effective_time_signature` per bar. Investigating
`export/midi/engine.py` surfaced why this doesn't actually work here:

```python
# Pattern content isn't segment-aware yet (per-segment pattern
# generation is out of scope - see issue #53 Group 5's follow-up
# note), so multi-bar pattern tiling keeps using the song's global
# meter; only the tempo/time-signature *markers* below react to
# segment overrides.
pattern_slice_beats_per_bar = song.time_signature.beats_per_bar
...
position_scale = beats_per_bar / pattern_slice_beats_per_bar
```

`_add_section_to_midi` renders one `Section.pattern`, authored against
the **Song's single global time signature**, and proportionally
stretches/compresses its positions to fit whatever the segment's
effective meter is for that bar. That's correct for its actual use case
(one pattern loosely retimed to fit an occasional odd bar inserted into
an otherwise-4/4 section) but wrong for this feature: each bar here is
already an independently, correctly-authored `Pattern` in its *own*
meter (6/8 bar built to span exactly 3.0 beats, 2/8 bar to span exactly
1.0 beat). Reusing the segment path would require picking one
`song.time_signature` to scale everything against, which cannot be
correct for more than one of the bars simultaneously — a real
architectural mismatch, not a missing parameter.

Instead: `MIDIEngine.bars_to_midi`/`save_bars_midi` (new methods,
additive to the existing class) take a plain `list[Pattern]`, each
carrying its own `time_signature`, and render them back-to-back at their
own authored positions with **no scaling** — advancing the time cursor
by each pattern's own `beats_per_bar` and emitting a new
`addTimeSignature` marker only when the meter actually changes between
consecutive bars. This sidesteps the issue #53 Group 5 gap entirely
rather than working around it, at the cost of not integrating with
`Song`/`Section`/regions/fills — acceptable for a spike whose whole point
is validating the grouping→meter conversion, not song structure.

## CLI entry point

`python -m midi_drums additive-rhythm "3-3-3-3-2-2" --grid 16 --output out.mid`
— standalone subcommand (`handle_additive_rhythm_command` in
`midi_drums/api/cli.py`), dispatched before `DrumGenerator()`
initialization like `prompt`/`riff`, since it doesn't touch the
plugin/genre system at all. Prints the resolved per-bar time signatures
before writing the MIDI file, so the conversion is visible without
opening a DAW.

## Non-goals (explicitly out of scope for this spike)

- **LLM agent tool integration.** The LLM's role should be limited to
  *extracting* a grouping string and grid from prose (e.g. "16th notes,
  3-3-3-3-2-2") — it should not be asked to do the run-splitting/
  canonicalization arithmetic itself, since that's exactly the kind of
  small deterministic transformation an LLM is unreliable at and this
  code already does correctly. Wiring a `parse_additive_rhythm` tool onto
  `PatternCompositionAgent` is a natural follow-up, not part of this
  spike.
- **Genre-plugin / drummer-style integration.** The generated pattern is
  a bare kick+hihat skeleton, not a genre-styled groove. Every genre
  plugin hardcodes `TimeSignature(4, 4)`; teaching even one to accept an
  externally-supplied per-bar meter sequence is a larger, separate
  change.
- **`Song`/`Section`/region support** (fills, variations, REAPER export,
  sidecar JSON). This spike only proves the grouping→meter→MIDI path in
  isolation.
- **Fixing the issue #53 Group 5 gap itself** (making `Section` pattern
  content genuinely segment-aware). Noted as a real, pre-existing,
  documented limitation encountered along the way — not something this
  spike attempts to fix.
- **Group sizes beyond 2, 3, and 4**, and nested/irrational subdivisions
  (e.g. quintuplets). The canonicalization rule is only validated against
  the confirmed worked example plus a few hand-checked sanity cases.

## Tests

`tests/unit/core/test_rhythmic_grouping.py`:
- The confirmed worked example: `3-3-3-3-2-2` @ 16th grid →
  `[6/8, 2/8]` with correct group tuples.
- A plain run reduces to the expected simple meter (four groups of 4 →
  `4/4`, not `16/16` or `8/8`).
- Explicit-bar syntax reproduces classic Balkan additive notation
  unmodified (`2+2+3` @ 8th grid → single bar `7/8`, no halving), and
  distinguishes it from the auto-split reading of the same digits
  without `|`.
- `3+3+3+3|2+2` (explicit bars) matches the auto-detected split of
  `3-3-3-3-2-2` (same two `TimeSignature`s).

`tests/unit/generation/test_additive_rhythm_builder.py`:
- Built patterns' beat positions land inside `[0, beats_per_bar)` for
  each bar.
- Kick count per bar equals the number of groups in that bar; hi-hat
  count equals the bar's total grid-unit count.

`tests/unit/export/midi/test_bars_to_midi.py`:
- `bars_to_midi` on a `[6/8-pattern, 2/8-pattern]` sequence emits exactly
  two `addTimeSignature` events (initial 6/8, then the change to 2/8) and
  places the second bar's notes starting at `time_cursor == 3.0`.

## References

- New module: `midi_drums/core/value_objects/rhythmic_grouping.py`
- New module: `midi_drums/generation/builders/additive_rhythm_builder.py`
- New methods: `MIDIEngine.bars_to_midi`/`save_bars_midi`
  (`midi_drums/export/midi/engine.py`)
- CLI: `additive-rhythm` subcommand, `handle_additive_rhythm_command`
  (`midi_drums/api/cli.py`)
- Prior art in this codebase: `RiffAccentMap`/`RiffAccent`
  (`midi_drums/core/value_objects/riff_accent.py`) — the closest existing
  genre-agnostic accent abstraction, not reused directly here since
  `RiffLockTransform` is v1-scoped to tiling one accent map uniformly
  across N bars of a *single* meter, not a sequence of different accent
  maps/meters per bar.
- TUBS / additive rhythm notation:
  <https://en.wikipedia.org/wiki/Box_notation>
