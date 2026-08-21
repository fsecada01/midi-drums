# Design: Riff-Driven Snare Accent Reaction

**Status**: proposed, not implemented. Companion to the shipped `riff` /
`RiffLockTransform` feature (PR #57) — extends it to answer: *"the guitar
riff is heavily accented, would the snare reflect it?"* Today: no, by
design (`RiffLockTransform` only ever touches `DrumInstrument.KICK`).

## Requirements

- Preserve current default behavior exactly: with no new flags/params set,
  output must be byte-identical to today's `riff` command. Snare reaction
  is opt-in, never a change to the default `riff-lock` pipeline.
- Must not weaken the "route through genre plugins" decision that shaped
  the original feature: the genre plugin's snare *identity* (e.g. a funk
  ghost-note pattern, a doom half-time backbeat) must still be visibly
  intact after this runs — this is additive reaction to accents, not a
  second, competing pattern generator.
- Three distinct behaviors, not one flag with unclear semantics (see
  Behavior Modes below) — they have different risk profiles and a user
  should be able to reason about which one they're turning on.
- Must not require re-deriving the riff analysis — reuses the
  `RiffAccentMap` already produced by `analyze_riff()` and already
  threaded through `GenerationParameters.riff_accents`.

## Non-goals (explicitly out of scope for this design)

- Moving the actual backbeat (e.g. snare off beats 2/4 to chase a
  syncopated accent). This is the one behavior that would erase genre
  identity, which is exactly what "route through genre plugins" protects
  against — deliberately excluded, not deferred.
- Reacting to riff accents with hi-hat/cymbal changes. Same rationale as
  the original feature's scope cut; a future design if ever needed.
- Multi-bar accent tracking. Inherits the same v1 single-representative-bar
  scope as `RiffLockTransform`.

## Architecture

### Component placement

A **new, separate** `DrummerModification` subclass —
`midi_drums/modifications/snare_accent_reaction.py`, sibling to
`riff_lock.py` — rather than a mode flag bolted onto `RiffLockTransform`.

Rationale: `RiffLockTransform` today has one job (lock kicks) and is
fully tested against that contract. Overloading it with snare logic
would mean every future kick-lock test has to also reason about snare
mode interactions, and it breaks the modifications package's existing
convention of one class = one technique (`BehindBeatTiming`,
`TripletVocabulary`, `GhostNoteLayer`, etc. in `drummer_mods.py` are all
single-purpose and compose via sequential `.apply()` calls). A separate
class keeps `RiffLockTransform`'s current test suite untouched and lets
kick-lock and snare-reaction be enabled independently.

Like `RiffLockTransform`, this is **not** registered in
`MODIFICATION_REGISTRY` (that registry requires zero-arg constructibility;
`riff_accents` has no sensible default) — constructed and called directly
from the pipeline hook, same pattern.

### Pipeline position

```
drum_generator.py: generate_pattern()
  1. plugin.generate_pattern(...)            # genre plugin builds base pattern
  2. plugin_manager.apply_drummer_style(...) # drummer styling
  3. plugin_manager.apply_riff_lock(...)     # <- existing, kicks only
  4. plugin_manager.apply_riff_snare_accents(...)  # <- NEW, runs after (3)
  5. pattern.humanize(...)
```

Step 4 runs *after* kick-lock, not in parallel with it, because "stab"
mode (below) needs to know where the kicks actually ended up — a stab is
defined as "unison with a locked kick," not "at the same accent position
independently."

### New value objects / parameters

`GenerationParameters` gains (mirroring how `riff_accents` /
`riff_lock_strength` were added — applies per `generate_pattern()` call,
not through `create_song`'s `**kwargs`, for the same one-bar-per-call
reason documented on the existing fields):

```python
# Riff-driven snare reaction (see
# midi_drums.modifications.snare_accent_reaction.SnareAccentReaction).
# "off" preserves today's behavior exactly - snare never reacts to
# riff_accents unless explicitly opted into.
riff_snare_mode: Literal["off", "reinforce", "stab"] = "off"
riff_snare_stab_threshold: float = 0.85  # stricter than kick's strong_threshold
```

`PluginManager` gains a thin pass-through, mirroring `apply_riff_lock`'s
exact shape (same try/except-log-return-None contract, same reason for
living in `plugins` rather than `generation` importing `modifications`
directly — DDD domain-boundary rule, unchanged rationale):

```python
def apply_riff_snare_accents(
    self,
    pattern: Pattern,
    riff_accents: "RiffAccentMap",
    mode: str,
    stab_threshold: float = 0.85,
    intensity: float = 1.0,
) -> Pattern | None: ...
```

### `SnareAccentReaction` — interface sketch (no method bodies; this is
the spec, not the implementation)

```python
@dataclass
class SnareAccentReaction(DrummerModification):
    """Reacts an existing snare pattern to strong riff accents.

    Two independent behaviors selected by `mode`; see module docstring
    for the full decision table. Never moves the backbone snare pattern's
    existing hit *positions* - only touches velocity (reinforce) or adds
    new unison hits alongside already-locked kicks (stab). Never invoked
    for mode == "off"; the pipeline hook skips the call entirely in that
    case (see plugin_registry.apply_riff_snare_accents), so this class's
    own default should never need to special-case "off" internally.
    """

    riff_accents: RiffAccentMap
    mode: Literal["reinforce", "stab"]

    # Shared with RiffLockTransform's own defaults for the *matching*
    # accents (reinforce should react to the same set of accents the
    # kick already locked to, not re-derive its own selection).
    strong_threshold: float = 0.6
    reinforce_tolerance_beats: float = 0.125

    # "stab" only: independent, stricter accent selection - not every
    # locked kick should double with a snare hit, only the most extreme
    # ones, or every bar would sound like a snare roll.
    stab_threshold: float = 0.85
    max_stabs_per_bar: int = 2
    min_stab_spacing_beats: float = 0.5

    # Collapse-to-reinforce dedup: a stab candidate within this tolerance
    # of an *existing* snare hit becomes a reinforce instead of an insert
    # - see Open Question resolution below.
    stab_collapse_tolerance_beats: float = 0.125

    @property
    def name(self) -> str: ...

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """
        mode == "reinforce":
          For each strong accent (>= strong_threshold): find nearest
          existing SNARE beat within reinforce_tolerance_beats (circular
          distance, reuse riff_lock._circular_distance). If found, boost
          its velocity toward the pattern's own snare accent-velocity
          ceiling (derive from existing accented snare beats the same way
          RiffLockTransform._kick_velocity_range derives from existing
          kicks - never a hardcoded MIDI value), scaled by accent.strength
          and intensity. No new beats, no position changes, no beats
          removed.

        mode == "stab":
          Select accents >= stab_threshold, budget-limited by
          max_stabs_per_bar / min_stab_spacing_beats (identical shape to
          RiffLockTransform._select_accents - same greedy
          strength-descending + circular-spacing algorithm, likely
          extracted to a shared helper rather than copy-pasted - see Open
          Questions).
          For each selected stab accent:
            - If an existing SNARE beat is within
              stab_collapse_tolerance_beats: treat as reinforce instead
              (bump velocity, no insert) - avoids a near-duplicate hit
              sitting a few ticks from the real backbeat.
            - Else if a locked KICK beat exists at this exact accent
              position (it should, by construction - this mode reads
              accents post-kick-lock): insert a new unison SNARE beat at
              that position, velocity derived from the pattern's existing
              snare accent range the same way, ghost_note=False,
              accent=True.
            - Else (accent was strong enough for a stab but weaker than
              the kick's own strong_threshold, so no kick landed there):
              skip - a stab with no kick under it isn't a stab, it's just
              an extra snare hit, which is a different (unrequested)
              feature.
        """
```

### CLI surface

New flags on the `riff` subcommand, both defaulted to preserve current
behavior:

```
--snare-mode {off,reinforce,stab}   default: off
--snare-stab-threshold FLOAT        default: 0.85 (only meaningful with --snare-mode stab)
```

No REAPER Lua dialog changes proposed in this design — `create_beat_from_riff.lua`'s
existing two-dialog flow is already fairly full; if this ships, exposing it
there is a small, separate follow-up (add one field to the "Timing" dialog),
not part of this design's surface area.

## Data flow

```
RiffAccentMap (from analyze_riff, unchanged)
      │
      ├─► RiffLockTransform.apply()          (existing, kicks only)
      │         │
      │         ▼
      │   Pattern (kicks now locked)
      │         │
      └─────────┼─► SnareAccentReaction.apply()   (new, reads the SAME
                │         │                         RiffAccentMap, plus the
                │         │                         kick-locked Pattern for
                │         │                         "stab" mode's collision
                │         │                         check against real kicks)
                │         ▼
                │   Pattern (snare velocity boosted and/or stab hits added)
                ▼
        (continues to humanize() as today)
```

## Open Questions (need a decision before implementation)

1. **Stab/reinforce collision dedup** — resolved above (collapse to
   reinforce within `stab_collapse_tolerance_beats`) per the earlier
   conversation; flagging again here as the one behavioral choice that
   most affects perceived output and is worth a second look before
   coding.
2. **Shared accent-selection helper** — `RiffLockTransform._select_accents`
   and `SnareAccentReaction`'s stab-selection do the same
   greedy-strength-descending-with-circular-spacing algorithm with
   different thresholds/budgets. Extract to a shared function (e.g.
   `midi_drums/modifications/_riff_accent_selection.py` or a
   `RiffAccentMap` method) now, or duplicate now and extract later if a
   third consumer appears? Given the codebase's demonstrated appetite for
   eliminating duplication (see CLAUDE.md's "Refactoring Achievement"
   section), leaning toward extracting immediately rather than
   duplicating-then-refactoring.
3. **Velocity range source for "stab"** — reinforce clearly derives its
   ceiling from existing *accented* snare hits. Stab inserts a wholly new
   hit — should its velocity come from (a) the same accented-snare range,
   (b) the newly-matched kick's own velocity (true unison feel), or (c)
   accent.strength mapped independently, the way `RiffLockTransform`
   already does for kick inserts? Leaning toward (b) for the most
   authentic "stab" feel, but this is a judgment call, not a technical
   constraint.
4. **`GHOST_NOTE` interaction** — should ghost-note snare beats
   (`ghost_note=True`) be eligible reinforce/collapse targets, or only
   full-velocity backbeat/accent hits? Leaning toward excluding ghost
   notes from both (a strong riff accent reinforcing a ghost note into a
   loud hit would change the pattern's character more than intended) —
   worth confirming against a real funk/pfunk pattern before deciding.

## Testing plan (mirrors `test_riff_lock.py`'s shape)

`tests/unit/modifications/test_snare_accent_reaction.py`:
- reinforce boosts velocity of an in-tolerance snare beat, leaves position
  unchanged
- reinforce with no snare beat in tolerance: pattern unchanged for that
  accent
- stab inserts unison snare only where a locked kick exists at that
  position
- stab with no kick under a stab-threshold accent: no insert (per the
  "skip" branch above)
- stab collapses to reinforce within `stab_collapse_tolerance_beats`
  (dedup case)
- wraparound at the bar boundary (reuse `_circular_distance`, same class
  of bug the kick-lock tests caught)
- `max_stabs_per_bar` / `min_stab_spacing_beats` budgets respected
- ghost notes excluded per Open Question 4's resolution
- determinism (same input twice → identical output — no randomness, same
  requirement as `RiffLockTransform`)
- `mode="off"` is never reached by the pipeline hook (assert
  `plugin_manager.apply_riff_snare_accents` is not called when
  `riff_snare_mode == "off"`, at the `drum_generator.py` call-site level)

## Summary of file-level changes (for `/sc:implement`, not done here)

| File | Change |
|---|---|
| `midi_drums/modifications/snare_accent_reaction.py` | new — `SnareAccentReaction` |
| `midi_drums/modifications/__init__.py` | export, intentionally unregistered (comment) |
| `midi_drums/modifications/_riff_accent_selection.py` (if Open Q2 → extract) | new — shared `select_accents(riff_accents, threshold, max_count, min_spacing)` |
| `midi_drums/modifications/riff_lock.py` | `_select_accents` delegates to the shared helper (if extracted) |
| `midi_drums/core/value_objects/generation_parameters.py` | `riff_snare_mode`, `riff_snare_stab_threshold` fields |
| `midi_drums/plugins/registry/plugin_registry.py` | `apply_riff_snare_accents` pass-through |
| `midi_drums/generation/engines/drum_generator.py` | pipeline hook, gated on `mode != "off"` |
| `midi_drums/api/cli.py` | `--snare-mode`, `--snare-stab-threshold` on `riff` subcommand |
| `tests/unit/modifications/test_snare_accent_reaction.py` | new |
