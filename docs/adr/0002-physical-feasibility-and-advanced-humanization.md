# 0002. Physical feasibility validation and Gaussian-based advanced humanization

> **Status**: Accepted (implemented)
> **Date**: 2026-08-21 (retroactively documented; original work dated 2026-01-24)

## Context

The composite doom/blues drummer plugin layered three drummer styles
(Roeder, Porcaro, Chambers) sequentially without validating the result,
which produced patterns no human drummer can play — most notably
simultaneous ride cymbal and hi-hat (hand) hits, exceeding the two hands
a drummer has available. Separately, the existing basic humanization
(`Pattern.humanize()`) applied a uniform random timing/velocity offset
regardless of instrument, tempo, or musical context, which reads as
mechanical rather than human — real drummers' timing errors follow a
bell curve, not a uniform distribution, and different instruments
(kick, hi-hat, ride, crash) carry different natural timing biases.

## Decision

Two additive, independently-testable systems:

1. **Physical feasibility validation** (`midi_drums/validation/physical_constraints.py`,
   `midi_drums/utils/pattern_fixer.py`) — a `PhysicalValidator` that
   assigns each beat to one of four limbs (right hand, left hand, right
   foot, left foot), flags conflicts (>2 simultaneous hand strikes, ride +
   hi-hat-hand played together), and a `pattern_fixer` that automatically
   resolves conflicts (converting a conflicting hi-hat hand hit to the
   foot pedal where musically appropriate) while preserving intent.
2. **Advanced humanization** (`midi_drums/humanization/advanced_humanization.py`)
   — an `AdvancedHumanizer` using a Gaussian (not uniform) timing
   distribution per instrument (kick leads, hi-hat is metronomic, ride/
   crash lag), section-context-aware velocity curves (chorus louder than
   verse, breakdown loudest), kick+snare micro-timing flams (1-3ms), and
   subtle fatigue modeling (slight velocity decay over long sections).
   Downbeats get tighter timing (50% less variance) than off-beats.

Both are opt-in and composable with existing drummer plugins and the
basic `humanization` parameter — no breaking changes to the generation
pipeline.

## Consequences

- Every generated pattern is now guaranteed playable by a real drummer;
  the composite drummer plugin specifically was fixed to no longer emit
  ride+hi-hat conflicts.
- Humanized output is measurably closer to professional (Toontrack-style)
  MIDI drum programming: Gaussian σ=3-5ms timing instead of uniform
  ±20ms, context-aware velocity ranges (ghost 25-45, normal 65-90, accent
  95-115).
- `numpy` becomes a required dependency for the Gaussian distribution
  calculation (already a core dependency by the time this ADR was
  written).
- Accepted limitation carried from the original design: fatigue modeling
  is a flat linear decay, not physiologically modeled; drummer-specific
  humanization *profiles* (distinct from drummer *plugins*) and an
  ML-based groove-similarity validator (e.g. against Magenta's Groove
  MIDI Dataset) were scoped as future work and were not built as part of
  this decision.

## References

- Original problem statement and research citations: [`claudedocs/archive/2026-08-21_docs-cleanup/PHYSICAL_FEASIBILITY_FIXES.md`](../../claudedocs/archive/2026-08-21_docs-cleanup/PHYSICAL_FEASIBILITY_FIXES.md)
- Original humanization analysis and proposal: [`claudedocs/archive/2026-08-21_docs-cleanup/HUMANIZATION_IMPROVEMENTS.md`](../../claudedocs/archive/2026-08-21_docs-cleanup/HUMANIZATION_IMPROVEMENTS.md)
- Original completion report: [`claudedocs/archive/2026-08-21_docs-cleanup/HUMANIZATION_SUMMARY.md`](../../claudedocs/archive/2026-08-21_docs-cleanup/HUMANIZATION_SUMMARY.md)
- Current usage guide: [`docs/VALIDATION_AND_HUMANIZATION.md`](../VALIDATION_AND_HUMANIZATION.md)
- Shipped in `midi_drums/validation/`, `midi_drums/utils/pattern_fixer.py`, `midi_drums/humanization/`
