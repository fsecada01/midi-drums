# 0005. Genre-context blending via per-genre intensity profiles

> **Status**: Accepted (implemented)
> **Date**: 2026-08-22 (retroactively documented; original decision dated 2025-09-30)

## Context

In a multi-genre song (e.g. a death metal song with a progressive bridge),
each section's pattern reflected its own genre's pure characteristics with
no awareness of the overall song context — a progressive section in a metal
song sounded like a separate song spliced in, rather than metal-flavored
progressive drumming. The goal was to let a section's genre plugin adapt
toward the song's primary genre's feel while keeping the section's own
defining characteristic (e.g. progressive's complexity) intact.

## Decision

Add a 6-dimension `intensity_profile` (aggression, speed, density, power,
complexity, darkness; each 0.0-1.0) as a property genre plugins can
override, plus two new `GenerationParameters` fields — `song_genre_context`
(the overall song's genre) and `context_blend` (0.0-1.0 blend amount,
default `0.0` — opt-in, no behavior change when unset). A three-stage
blending algorithm (power → velocity boost, aggression → timing
quantization, density → ghost-note insertion) linearly interpolates the
pattern's own profile toward the context genre's profile:
`blended = base + (context - base) * blend_amount`. Applied after base
pattern generation, before drummer styling and humanization — the same
pipeline position later reused by `RiffLockTransform` (see
[[0004-riff-driven-snare-accent-reaction]]'s sibling feature) for the same
reason: downstream steps (styling, humanization) should operate on the
final intended pattern, not a pre-blend one.

Like `riff_accents`, these parameters apply per `generate_pattern()` call
rather than through `create_song`'s `**kwargs` — a song-wide blend would
need per-section values, which `**kwargs` can't express without every
section sharing the same blend amount.

## Consequences

- Multi-genre songs can now sound cohesive without losing each section's
  identifying complexity — e.g. a progressive bridge in a metal song gets
  heavier hits and tighter timing while keeping its complex phrasing.
- Every existing genre plugin (metal, rock, jazz, funk, electronic) now
  defines its own `intensity_profile`; a plugin that doesn't override it
  gets a neutral (all-0.5) default, so third-party/future genre plugins
  aren't required to define one to remain functional.
- Backward compatible: `context_blend` defaults to `0.0`, so unset callers
  see no behavior change.
- Explicitly deferred at the time (not built as part of this decision):
  section-aware blending strategies (different blend per intro/chorus),
  per-instrument blend customization, multi-context blending (blending
  toward more than one genre at once), and any ML-based or config-file-driven
  custom profile system.

## References

- Original design doc and completion report (`GENRE_CONTEXT_ADAPTATION_DESIGN.md`,
  `GENRE_CONTEXT_ADAPTATION_COMPLETE.md`) have been removed now that this
  ADR captures their decisions — see git history under
  `claudedocs/archive/2025-09-september/` prior to this ADR's introduction
  for the full text.
- Shipped in `midi_drums/plugins/interfaces/genre_plugin.py` (intensity
  profiles + blending), `midi_drums/core/value_objects/generation_parameters.py`
  (`song_genre_context`, `context_blend`), and every genre plugin under
  `midi_drums/plugins/genres/`
