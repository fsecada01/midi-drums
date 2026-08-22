# 0008. GM preset note-map correction; other vendor kits left unresearched rather than guessed

> **Status**: Accepted (implemented; scope deliberately partial)
> **Date**: 2026-08-22 (retroactively documented; original research dated 2026-08-12)

## Context

Issue #47 asked for real vendor `custom_mappings` note tables across
EZDrummer 3, Superior Drummer 3, BFD3, and Addictive Drums 2. Research found
that `DrumInstrument`'s baseline note values already target EZDrummer 3
directly (8 enum members are commented `# EZDrummer specific`, including
articulations like `CLOSED_HH_EDGE`/`OPEN_HH_MAX` that don't exist in GM
Level 1 percussion at all) — meaning `create_ezdrummer3_kit()`'s empty
`custom_mappings` was already correct, but `create_gm_drums_kit()`'s claim
of "GM standard mappings (matches DrumInstrument enum values)" was actually
**false** for those same 8 articulations: a strict GM-compliant sampler
receiving the enum's raw note value for e.g. `OPEN_HH_MAX` would trigger
"Hi Bongo," not an open hi-hat.

For the other three vendor kits, the research pass could not obtain
reliable note numbers: Superior Drummer 3's only available detail was a
third-party (non-vendor) PDF reupload; BFD3's official manual page returned
an internally self-contradictory extraction (the same MIDI note assigned to
two different drums); Addictive Drums 2's vendor keymap page returned
HTTP 403.

## Decision

Fix only the confirmed bug: give `create_gm_drums_kit()` real
`custom_mappings` (`_GM_HIHAT_COLLAPSE`) that collapse the 8 non-GM
articulations down to their nearest real GM Level 1 note (closed-hat family
→ `CLOSED_HH`, open-hat family → `OPEN_HH`) — grounded in the repo's own
enum plus the stable, decades-old GM spec, no external citation risk.
Explicitly **do not** fabricate or ship unreliably-sourced note tables for
Superior Drummer 3, BFD3, or Addictive Drums 2 — those three kit presets
remain GM-equivalent placeholders. A source that is internally
self-contradictory (BFD3) or third-party-only (SD3) was judged worse than
no source at all for data that ships as fact in a music tool.

## Consequences

- The GM preset kit is now actually GM-compliant for every articulation,
  closing a real correctness bug that predates this research.
- Superior Drummer 3, BFD3, and Addictive Drums 2 presets remain
  GM-equivalent rather than vendor-accurate — users of those three DAW
  sample libraries get GM note numbers, not the sampler's actual
  articulation map, until someone with the product installed verifies real
  values (the two most promising next leads: BFD3's in-app Key Map panel,
  and independently re-deriving SD3's map rather than trusting the Scribd
  reupload).
- Establishes a precedent for this codebase: an uncertain or
  self-contradictory external source blocks shipping data-as-fact, even
  under "ship something" pressure from an open issue.

## References

- Full research report (per-vendor findings, source-confidence notes):
  [`claudedocs/archive/2026-08-21_docs-cleanup/research_vendor_drum_midi_maps_20260812.md`](../../claudedocs/archive/2026-08-21_docs-cleanup/research_vendor_drum_midi_maps_20260812.md)
- Shipped in `midi_drums/core/models/kit.py` (`_GM_HIHAT_COLLAPSE`,
  `create_gm_drums_kit()`)
- Source enum: `midi_drums/core/value_objects/drum_instrument.py`
