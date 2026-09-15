# Research: EZdrummer 3's Edit Play Style — Implications for the midi_drums Step Editor

**Date**: 2026-09-14
**Depth**: standard (web search + targeted extraction, 2 rounds)
**Purpose**: Ground the "Option 1 step editor" design
(`claudedocs/design_step_editor_grid.md`) against how Toontrack's own
Edit Play Style feature actually works, since the user's original
Gemini-sourced brief named it directly (Power Hand, Amount knobs,
Velocity Scaling) as the reference point for "manual editing ability."

**Boundary**: this is a research report only — no design changes or
code were made. See "Analysis" below for what should feed back into the
design doc, left for a follow-up `/sc:design` or `/sc:implement` pass.

## Executive summary

Edit Play Style is **not** a raw step-grid editor — EZdrummer 3 has a
separate, ordinary Grid Editor for that (added in v3, matching Superior
Drummer 3's). Edit Play Style is a **higher-level, per-lane macro
control layer** that sits on top of a groove: drag-to-reassign which
instrument plays the lead rhythmic role, per-instrument articulation/
variation menus, a "resolution" hint, one or more "Amount" knobs that
add or remove hits in a musically-plausible way (with snare ghost notes
split out as their own separate Amount control in v3), and
velocity-shaping controls — a raw proportional scale plus named
"velocity style" contour presets. Toontrack markets the add/remove and
variation behavior as "smart AI-based algorithms," but no public source
found here describes the algorithm itself — every source stops at the
UI/behavior level.

This matters for the midi_drums step editor design because the
Gemini-sourced brief conflated "step grid" and "Edit Play Style" as one
ask, but they're two different tools solving different problems in the
product this was modeled on. The existing `design_step_editor_grid.md`
scoped the step-grid half correctly; this report's job is to identify
what a true Edit-Play-Style-equivalent macro layer would need on top of
that, and which parts are cheap REAPER-API operations versus which
parts need real generative logic this project's Python side already
has and Lua does not.

## Findings

### 1. Power Hand reassignment (drag-to-retarget)

The "Power Hand" is Toontrack's name for the leading rhythmic-ostinato
instrument in a groove (commonly hi-hat or ride). Dragging its on-screen
flag onto a different kit piece instantly retargets that role to the new
instrument while preserving the original rhythm/timing/velocity
contour — e.g. hi-hat becomes ride with the same pattern.

> "The key here is you just drag this around to whatever instrument on
> the drum kit you want. So let's say we want high hats instead. It's
> that easy to change your power hand without the grid editor."
> — *EZdrummer 3 Tips | Mastering the Power Hand* (Shootie School)

> "The Power Hand feature has also been expanded, making it much easier
> to switch the Power Hand from, for example, the hi‑hat to the ride
> cymbal and to add variety to the cymbal articulation."
> — Sound On Sound review

### 2. Power Hand variation/articulation menu

Independent of full reassignment, a dropdown on the Power Hand instrument
offers alternate playing-style variations for *that same instrument*
(e.g. hi-hat "open edge 2" instead of default closed) — changes feel and
accents without changing which instrument is playing.

> "In addition to simply changing the instrument articulation, the
> power hand menu now provides a selection of alternate playing styles
> suited to the instrument and chosen groove... by choosing a different
> instrument variation you can change the feel and accents of the
> hi-hat just like a real drummer would."
> — *EZdrummer 3: Edit Play Style* (official Toontrack video)

### 3. "Resolution" control

A secondary control that biases the rhythmic subdivision the Power Hand
plays at (e.g. quarter- vs eighth-note feel). Explicitly described by a
third-party demonstrator as a *hint*, not a hard constraint:

> "This resolution menu... it doesn't dictate exactly what the power
> hand does, but it does help."
> — *EZdrummer 3 Tips | Mastering the Power Hand*

### 4. Amount knob(s) — musical add/remove, split for ghost notes in v3

An "Amount" knob adds or removes hits from an instrument's part in a
way intended to sound like a real drummer's variation, not random
insertion/deletion. EZdrummer 2 had one Amount control per instrument;
EZdrummer 3 adds a **separate ghost-note Amount** specifically for the
snare, decoupled from the main-accent Amount:

> "In EZdrummer 2 the amount knob made this process simpler by letting
> a songwriter add or remove hits to a groove in the way that a real
> drummer would. Now in EZdrummer 3 we take this a step further with
> separate options for ghost notes of the snare — this way you can
> increase or decrease snare ghost notes without changing the main
> accents in the groove."
> — *EZdrummer 3: Edit Play Style* (official Toontrack video)

A confirmed implementation detail from the official 3.0.3 release notes:
notes added via Amount are **tracked separately from the groove's
original notes**, specifically so that reassigning the Power Hand
afterward only carries the added notes, not the original ones — this
was a bug prior to 3.0.3:

> "Adding hits with Amount on the Power Hand instrument and then moving
> the Power Hand sign to a different instrument would make the new
> Power Hand instrument play only the hits that were added with Amount,
> not the original hits." (listed as a fix in 3.0.3)
> — Toontrack, *Release notes for EZdrummer 3.0.3*

### 5. Velocity Scaling and velocity-style presets

Two distinct velocity tools were found, not one:

- **Proportional scaling**: raise/lower velocity for a selected
  instrument or group "as a whole," preserving the relative balance
  between hits (not just flattening everything to one value).

  > "Select an instrument or group of instruments and adjust their
  > velocity as a whole." — *Write Better Drums in EZdrummer 3*

  > "The Edit Play Style function allows you to adjust the dynamics and
  > number of hits within the pattern from each drum piece or the kit
  > as a whole." — Sound On Sound review

- **Named velocity-style contour presets**: a menu of curated velocity
  "styles"/"intensities" (e.g. "halftime regular") that reshape an
  entire groove's dynamic contour in one click — qualitatively
  different from linear scaling.

  > "You can choose the velocity style and velocity intensity. In this
  > case I'll choose halftime regular since this is a halftime groove.
  > And you can see what happens to the velocities as I click through
  > the different styles."
  > — *Write Better Drums in EZdrummer 3: Grid Editor, Humanize, Edit
  > Play Style*

### 6. "Groove Parts" menu — instrument/group scoping

A separate menu (also used elsewhere in EZD3, e.g. for MIDI-replace) is
how the user picks which instrument(s) the above controls act on —
functions as the scope selector, and can target a single instrument or
"all drums at the same time."

> "Just make sure to select the instrument that you want to change in
> the groove parts section, which was the kick in this case."
> — *Write Better Drums in EZdrummer 3*

> "I'm going to select the instrument I want to work on — you could
> actually work on all drums at the same time if you wish."
> — *The EZ Guide to EZdrummer 3*

### 7. Explicitly distinct from, and complementary to, the Grid Editor

EZdrummer 3 added a full Grid Editor (present in Superior Drummer 3
since earlier, new to the EZ line in v3) *alongside* Edit Play Style,
not as a replacement for it. Sources consistently frame Edit Play Style
as the tool you reach for specifically to **avoid** opening the grid:

> "Here you don't even have to look at a grid editor if you don't want
> to... How Edit Play Style lets you reshape a part without staring at
> the grid." — *Write Better Drums in EZdrummer 3* (video description)

> "That's how you steal groove parts with the groove parts menu... that
> will help you stay out of the grid editor if you don't like that type
> of labor." — *EZdrummer 3 Tips | Mastering the Power Hand*

## Analysis: what this changes about the step-editor design

`claudedocs/design_step_editor_grid.md` scoped a **raw step grid**:
per-cell toggle, per-cell velocity popup, direct `MIDI_InsertNote`/
`MIDI_SetNote`/`MIDI_DeleteNote` calls. That is the correct design for
*that* tool — it's the midi_drums equivalent of EZD3's Grid Editor, not
of Edit Play Style. The two products keep both tools for a reason (see
Finding 7): a grid is for precise single-hit correction, Edit Play Style
is for fast, musically-aware macro reshaping. The original brief's
"manual editing ability" ask is satisfied by the grid; Edit Play Style
is a *second*, complementary tool worth scoping separately, not a
missing piece of the grid design.

Mapping each Edit Play Style mechanism onto what's cheap vs. what needs
new generative logic:

| Mechanism | Cheap Lua/REAPER-API operation? | Needs Python-side generative logic? |
|---|---|---|
| Power Hand reassignment (Finding 1) | **Yes** — read existing notes' timing/velocity at the source lane, rewrite their pitch to the target lane's note number. Pure data move, no new musical knowledge required. | No |
| Articulation variation menu (Finding 2) | **Yes, if** the target kit-map (from `list kit-map`, already designed) exposes sibling articulation notes per instrument (e.g. `CLOSED_HH_EDGE`/`CLOSED_HH_TIP` alongside `CLOSED_HH`) — swapping pitch among siblings is the same data move as reassignment. | No |
| Resolution hint (Finding 3) | Partially — thinning/doubling existing hits to a coarser/finer grid is a mechanical resample, but doing it *musically* (which hits survive a thinning pass) edges toward the Amount problem below. | Borderline |
| **Amount knob — musical add/remove (Finding 4)** | No — this is the one Toontrack explicitly attributes to "smart AI-based algorithms," and no source here describes the actual logic. A naive random insert/delete would not reproduce what the demos show (hits that "sound like a real drummer would place them"). | **Yes** — this project already has the relevant generative primitives on the Python side: `midi_drums/modifications/drummer_mods.py`'s `GhostNoteLayer` and friends, the `complexity` parameter throughout `GenerationParameters`/pattern templates, and humanization. Reusing those (rather than inventing a second, weaker density algorithm in Lua) is the natural fit. |
| Separate ghost-note Amount (Finding 4) | No, same reasoning | **Yes** — `GhostNoteLayer` already exists specifically for this in the Python codebase; this is close to a direct reuse rather than new design. |
| Velocity proportional scaling (Finding 5) | **Yes** — multiply selected notes' velocities by a factor, clamp to 1-127. Straightforward Lua loop over `MIDI_GetNote`/`MIDI_SetNote`. | No |
| Velocity-style contour presets (Finding 5) | **Yes, if** presets are simple parametrized curves (per-position multiplier tables, e.g. accent/ghost-note ratio templates) — a small fixed preset table in Lua is fine here, unlike the drum-note-map case, because these are stylistic curves, not a data source with an existing Python-side single source of truth. | No (small hardcoded preset set is fine — this is closer to `GRID_VALUES`, a genuinely fixed set, than to genre/drummer/mapping data) |
| Groove Parts scoping (Finding 6) | **Already covered** — the step-editor design's `lanes`/`group` structure (grouped by kick/snare/hihat/toms/cymbals/ride) already provides exactly this kind of selection target; a "select all" / "select group" affordance is a small UI addition, not new architecture. | No |

The recurring theme: everything that's pure data manipulation on
*existing* notes (reassign, articulation-swap, scale velocity, apply a
canned contour) is cheap and belongs entirely in
`reaper/midi_drums/step_editor.lua`, no subprocess involved — consistent
with that design doc's existing "edit the REAPER item directly, no
Python round-trip in the editing loop" principle. The one mechanism that
genuinely needs new logic is the Amount knob's musical add/remove, and
that logic should not be reinvented in Lua — it should call back into
the same Python-side density/ghost-note machinery this project already
built and validated for generation, which also reopens the "does the
Step Editor know how this item was originally generated" question the
design doc already flagged as an open fork (mapping metadata), since an
Amount-knob round-trip would ideally know the item's original genre/
style/drummer/complexity to regenerate density changes in-context
rather than guessing from bare MIDI data alone.

## Recommendations (for human decision, not applied)

1. **Keep the raw step grid as-is** — `design_step_editor_grid.md`'s
   scope is correct for what it's building and doesn't need revision
   because of this research.
2. **Scope a second, later tier** — a "Play Style" macro panel,
   modeled on Edit Play Style, as a *follow-up* design after the step
   grid ships, not a revision to it. Likely v2 candidate pieces, in
   rough cheapest-first order:
   - Lane reassignment (Power-Hand-equivalent) — cheap, pure Lua.
   - Articulation-sibling swap — cheap, pure Lua, contingent on the
     kit-map data actually exposing sibling groupings.
   - Velocity proportional scaling per lane/group — cheap, pure Lua.
   - Velocity-style contour presets — cheap, small fixed preset table.
   - Amount knob (density/ghost-note add-remove) — the expensive one;
     recommend prototyping it as a thin Python entrypoint that operates
     on a `Pattern` (reusing `GhostNoteLayer` and the `complexity`
     machinery) rather than a Lua reimplementation, and treat it as
     dependent on resolving the mapping-metadata / generation-provenance
     fork already open in the step-editor design doc.
3. **Track added-vs-original notes if Amount-then-reassign is ever
   supported**, mirroring the exact bug Toontrack had to fix in 3.0.3
   (Finding 4) — worth calling out now so it's not rediscovered the same
   way later.

## Evidence gaps

- No official technical description of the Amount knob's or the
  variation menu's underlying algorithm was found anywhere in this
  search — Toontrack's own language stays at "smart AI-based
  algorithms" / "clever drummer-based AI" without elaborating. Any
  midi_drums analog is original design work, not a port of a documented
  method.
- The official EZdrummer 3 manual (`toontrack.com/manual/ezdrummer-3/`)
  is a JS-rendered page whose static extract returned only cookie-policy
  boilerplate, not the manual body — this report leans on release notes,
  the Sound On Sound review, and several video transcripts instead.
  Reasonable confidence on UI-level behavior (multiple independent
  sources agree); lower confidence on anything below that surface.

## Sources

- [EZdrummer 3: Edit Play Style](https://www.youtube.com/watch?v=5EZiL4YUHmE) — official Toontrack video, incl. transcript
- [Write Better Drums in EZdrummer 3: Grid Editor, Humanize, Edit Play Style](https://www.youtube.com/watch?v=rcp8VX1eKqs)
- [EZdrummer 3 Tips | Mastering the Power Hand](https://www.youtube.com/watch?v=0D1E521KatE) — Shootie School
- [The EZ Guide to EZdrummer 3](https://www.youtube.com/watch?v=ua4XUujoRT4) — Shootie School
- [#EZDrummer3 edit play style and automation trick to enhance your songs](https://www.youtube.com/watch?v=B7jG_wz5lfI) — A Sound Mind
- [Toontrack EZdrummer 3 review](https://www.soundonsound.com/reviews/toontrack-ezdrummer-3) — Sound On Sound
- [Release notes for EZdrummer 3.0.3](https://www.toontrack.com/faq/release-notes-for-ezdrummer-3-0-3) — Toontrack FAQ (primary/official source)
- [How to program drums](https://www.toontrack.com/blog/how-to-program-drums/) — Toontrack blog
- [EZdrummer 3 product page](https://www.toontrack.com/product/ezdrummer-3/) — Toontrack (manual body not retrievable, JS-rendered)

## Next step

This is a research report only. To act on it: `/sc:design` a v2 "Play
Style" panel scoped from Recommendation 2 above, or park it and proceed
straight to `/sc:implement` on the already-designed step grid.
