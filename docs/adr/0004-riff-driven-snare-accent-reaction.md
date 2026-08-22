# 0004. Riff-driven snare accent reaction as a separate, opt-in modification

> **Status**: Accepted (implemented, shipped via PR #57 and #61)
> **Date**: 2026-08-22 (retroactively documented; original design dated prior to `feat/riff-locked-drum-generation` merge)

## Context

`RiffLockTransform` (the riff-lock feature, see `midi_drums/modifications/riff_lock.py`)
locks kick hits to a guitar/bass riff's rhythmic accents but deliberately
only ever touches `DrumInstrument.KICK` — everything else, including the
snare, is untouched by design. The open question this ADR resolves: when a
riff is heavily accented, should the snare react to it at all, and if so,
how, without eroding the "route through genre plugins" decision that shaped
the original riff-lock feature (i.e. the genre plugin's snare identity —
funk ghost notes, a doom half-time backbeat — must stay visibly intact)?

## Decision

Add `SnareAccentReaction` (`midi_drums/modifications/snare_accent_reaction.py`)
as a **new, separate** `DrummerModification` subclass rather than a mode
flag bolted onto `RiffLockTransform` — keeps `RiffLockTransform`'s existing
test suite untouched and lets kick-lock and snare-reaction be enabled
independently. Like `RiffLockTransform`, it is constructed and called
directly from the pipeline hook rather than registered in
`MODIFICATION_REGISTRY` (that registry requires zero-arg constructibility;
`riff_accents` has no sensible default).

Runs in the pipeline strictly *after* kick-lock (`riff_snare_mode` param on
`GenerationParameters`, default `"off"` — byte-identical output to the
pre-feature pipeline unless explicitly opted into), because `"stab"` mode
needs to know where the kicks actually landed. Three modes, chosen
deliberately over one ambiguous flag since each has a different risk
profile:

- `"off"` (default) — no change.
- `"reinforce"` — boosts velocity of an existing snare hit already near a
  strong accent; never moves positions, never inserts new hits.
- `"stab"` — inserts a new unison snare hit at a strong accent where a
  riff-locked kick already landed; collapses to `"reinforce"` instead of
  inserting if an existing snare hit is already nearby (avoids a
  near-duplicate hit a few ticks off the real backbeat).

Explicitly out of scope, matching the "route through genre plugins"
guardrail: moving the backbeat itself, and hi-hat/cymbal accent reactions.
Both would erase genre identity rather than react to it.

A shared `nearest_within()`/`select_accents()` helper was extracted to
`midi_drums/modifications/_riff_accent_selection.py` (during the post-review
fix pass on PR #61) since both `RiffLockTransform` and `SnareAccentReaction`
needed the same greedy strength-descending, circular-spacing nearest-match
algorithm with per-caller exclusion sets — avoiding two independently
maintained copies of the wrap-around-sensitive distance math.

## Consequences

- Snare reaction is fully opt-in and additive; the default `riff` CLI
  command output is unaffected.
- `snare_accent_reaction.py` and `riff_lock.py` now share one
  nearest-neighbor implementation, closing a duplication gap the original
  riff-lock design doc had flagged as an open question.
- REAPER Lua panel exposure (`--snare-mode`/`--snare-stab-threshold` on the
  Riff-Lock Beat tab) is still outstanding — the CLI/Python surface shipped
  first; wiring it into the panel is a separate, smaller follow-up.
- Accepted v1 limitation, inherited from `RiffLockTransform`: single
  representative bar, tiled — no multi-bar accent tracking.

## References

- Original design doc (requirements, non-goals, architecture, open-question
  resolutions, testing plan) has been removed now that this ADR captures
  its decisions — see `claudedocs/design_riff_snare_accents.md` in git
  history prior to this ADR's introduction for the full text.
- Shipped in `midi_drums/modifications/snare_accent_reaction.py`,
  `midi_drums/modifications/_riff_accent_selection.py`
- CLI flags documented in the root `CLAUDE.md`'s "New CLI Flags" table
