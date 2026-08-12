# Research: Vendor default MIDI note maps (EZDrummer 3, Superior Drummer 3, BFD3, Addictive Drums 2)

**Date:** 2026-08-12
**Trigger:** Issue #47, AC Group 1 — "Research and populate real `custom_mappings` note tables"
**Depth:** Standard (targeted web search + primary-source fetch, no fabrication)

## Executive summary

Only one product's divergence from GM is confirmed with high confidence and a concrete, implementable note table: **EZDrummer 3**, and that confidence comes from *this repo's own source*, not external research — `midi_drums/core/value_objects/drum_instrument.py` already marks 8 enum members `# EZDrummer specific` with their real note numbers. For **Superior Drummer 3**, **BFD3**, and **Addictive Drums 2**, reliable vendor-documented note numbers were not obtainable in this pass — see per-vendor findings below. Implementation in issue #47 is scoped accordingly: ship the EZDrummer-vs-GM fix now, leave the other three presets as explicit GM-equivalent placeholders with the "not yet researched" caveat surfaced in code comments and the README, rather than fabricate numbers.

## Findings by vendor

### EZDrummer 3 (Toontrack) — confirmed, in-repo

`DrumInstrument` (drum_instrument.py:9-29) already carries EZDrummer-specific note numbers for 8 extended hi-hat articulations that don't exist in GM at all:

| Instrument | Note | Comment in source |
|---|---|---|
| CLOSED_HH_EDGE | 22 | EZDrummer specific |
| CLOSED_HH_TIP | 61 | EZDrummer specific |
| TIGHT_HH_EDGE | 62 | EZDrummer specific |
| TIGHT_HH_TIP | 63 | EZDrummer specific |
| OPEN_HH_1 | 24 | EZDrummer specific |
| OPEN_HH_2 | 25 | EZDrummer specific |
| OPEN_HH_3 | 26 | EZDrummer specific |
| OPEN_HH_MAX | 60 | EZDrummer specific |

These are **not** GM Level 1 percussion notes — GM's percussion range starts at 27, and GM notes 60-63 mean something else entirely in strict GM (Hi/Low Bongo, Mute/Open Hi Conga). Since the enum's baseline values already target EZDrummer 3, `create_ezdrummer3_kit()`'s empty `custom_mappings` is *already correct* — no fix needed there. The bug is on the GM side (below).

**Source confidence:** High. This is the repo's own code, not an external claim — no citation needed beyond the file itself.

### GM Standard preset — confirmed bug, in-repo reasoning

`create_gm_drums_kit()` claims "GM standard mappings (matches DrumInstrument enum values)" (kit.py:173) but this is false for the 8 EZDrummer-specific instruments above — a strict GM-compliant sampler receiving note 60 would trigger "Hi Bongo," not an open hi-hat. **Fix:** give the GM preset real `custom_mappings` that collapse the 8 non-GM articulations down to the nearest real GM note (closed-hat family → `CLOSED_HH` note 42, open-hat family → `OPEN_HH` note 46). This requires no external research — it's a direct consequence of the GM Level 1 percussion spec (a stable, decades-old standard) plus the repo's own enum.

### Superior Drummer 3 (Toontrack)

- Toontrack's own forum/FAQ content (via search) states SD3's default map is "GM Extended" and that it is "almost GM MIDI compatible, except for the open Hi-Hat and the Tom Rims" — this is a real, sourced claim about *which* articulations diverge.
- **Could not obtain** the actual divergent note numbers. The SD3.1.1 release notes page (https://www.toontrack.com/faq/release-notes-for-superior-drummer-3-1-1/) contains no note-number data. A "Superior Drummer 3 MIDI Mapping Guide" PDF exists on Scribd (https://www.scribd.com/document/849367233/MidiRemap-toontrack-superior-drummer-3) but was not fetched (third-party reupload, not a primary vendor source — a citation from it would not meet the "vendor manual" bar this research was scoped to).
- **Verdict:** insufficient to implement without risking wrong data shipped as fact.

### BFD3 (FXpansion / inMusic)

- Fetched https://www.fxpansion.com/webmanuals/bfd3/operationmanual/bfd3_key_map_reference.htm. The returned summary was **internally self-contradictory** — e.g. note 36 assigned to both "Kick: Hit" and "Floor Tom: Hit," note 60 to both "Snare: Hit" and "High Tom 2: Hit," note 52 to both a hi-hat articulation and "Crash 2: Hit." This is a strong signal the fetch tool's summarization hallucinated or conflated multiple key-map variants shown on that page (BFD3 ships several alternate key maps, not one canonical GM table) rather than faithfully extracting one real table.
- **Verdict:** unusable. Do not implement from this data — a self-contradictory source is worse than no source.

### Addictive Drums 2 (XLN Audio)

- The specific keymap page (https://support.xlnaudio.com/hc/en-us/articles/16925247222045-Addictive-Drums-2-Keymap) returned **HTTP 403** — XLN's support portal blocks the fetch.
- Search snippets confirm AD2 ships a "GM Map Preset" for e-drum compatibility but gave no note numbers.
- **Verdict:** no data obtained.

## Recommendation

1. **Ship now:** the EZDrummer-3-is-already-correct / GM-preset-is-actually-wrong fix — grounded entirely in this repo's own code plus the stable, decades-old GM Level 1 spec. No external citation risk.
2. **Don't ship:** fabricated or unreliably-sourced note tables for Superior Drummer 3, BFD3, or Addictive Drums 2. Leave those three presets as explicit GM-equivalent placeholders, with an inline comment noting real vendor research is still needed, and call this out plainly in the PR description as a deliberately deferred follow-up (matches the issue's own "as time allows" hedge on this item).
3. **Future follow-up** (not this phase): the Scribd SD3 mapping guide and BFD3's in-app Key Map panel (referenced by FXpansion's own docs as the authoritative live reference) are the two most promising next leads if someone picks this back up — both require a human with the actual product installed to verify, which this research pass didn't have access to.
