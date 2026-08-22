# Design: Unified REAPER Panel

**Status**: proposed, not implemented. Replaces the three separate
REAPER Lua scripts (`create_song_sections.lua`, `create_beat_from_riff.lua`,
`midi_drums_help.lua`) with one dockable ReaImGui panel. Brainstormed and
approved via Socratic dialogue; the approved UI direction is captured in an
interactive mockup published as a Claude Artifact:
https://claude.ai/code/artifact/4846cac4-b5ca-4ac6-8e51-00e6b919645b

## Motivation

The current REAPER integration is three independent scripts, each its own
REAPER action, each gathering input through a sequence of modal
`GetUserInputs` dialogs (a Yes/No mode picker, then a chain of text-field
prompts) and printing progress to the separate REAPER console window.
Individually each script works; together they read as three disconnected
tools bolted onto REAPER rather than one coherent instrument, and the
modal-dialog UX doesn't hold up against a proper settings surface with
dropdowns, sliders, and live feedback. The two pains driving this design,
in the user's own words: **clunky input UX** and **fragmented surface
area**. Iteration latency (the ~1-2s / ~20-45s subprocess-startup cost)
was explicitly *not* the primary complaint and stays as-is for v1 (see
Non-goals).

## Requirements

- One coherent panel, not three disconnected actions — a single REAPER
  action opens it.
- Real widgets (dropdowns, sliders, segmented controls) replacing every
  `GetUserInputs` call.
- Scattered configuration (the `python_exe` ExtState prompt, hardcoded Lua
  constants for default genre/style/mapping/AI tempo, the sidecar path)
  consolidated into one editable, persisted Settings surface.
- Job progress/output visible in-panel (a Log tab), not only in the
  separate REAPER console.
- The panel must stay responsive for the AI generation path's ~20-45s
  wait — no frozen window during that time.
- Must work for other users who clone this public repo, not just the
  author's own REAPER setup — dependency requirements need to be
  documented and detected, not assumed.

## Non-goals (explicitly out of scope for v1)

- **Live/iterative regeneration without a fresh subprocess call.** The
  user chose to keep subprocess-per-click for v1 — a slider tweak still
  triggers a full `python -m midi_drums ...` invocation, not a
  long-lived Python process. Revisit only if this later proves to be the
  actual bottleneck once the UX/fragmentation pain is fixed.
- **A persistent job registry surviving REAPER restarts or crashes.** See
  Error Handling's accepted v1 limitation below.
- **A REAPER-version-specific ReaImGui compatibility matrix.** The
  install story is "install ReaImGui via ReaPack" (documented in
  `reaper/README.md`'s new Prerequisites section); no attempt is made
  here to enumerate which REAPER builds support which ReaImGui version.
- **A fallback, non-ReaImGui UI path.** ReaImGui is a hard prerequisite;
  the three existing scripts are fully retired, not kept as a parallel
  option for users who won't install it.

## Architecture

### Component placement

One new entry-point script, `reaper/midi_drums_panel.lua`, registered as
a single REAPER action ("MIDI Drums: Open Panel"). It opens a dockable
ReaImGui window with four tabs — **Song Sections**, **Riff-Lock Beat**,
**Settings**, **Log** — and owns the `defer()` loop REAPER calls every
frame to keep the window alive.

The business logic currently embedded in the three scripts is extracted
into a small `reaper/midi_drums/` module directory, so the panel's tab
handlers stay thin and the underlying logic is unit-of-work-testable in
isolation from ReaImGui's rendering calls:

| Module | Owns |
|---|---|
| `reaper/midi_drums_panel.lua` | Entry point / registered action. Opens the window, owns the `defer()` loop, wires up the four tabs, renders the contextual-help ("?") popovers. |
| `reaper/midi_drums/job_runner.lua` | Async subprocess execution (see Data Flow). One code path for every mode — template, sidecar, AI, song-map, and riff-lock all go through the same `start()`/`poll()` pair. Enforces a single in-flight job system-wide. |
| `reaper/midi_drums/sections.lua` | Logic lifted from `create_song_sections.lua`: sidecar/song-map JSON construction, resolving REAPER's own section table, and placing markers/regions/tempo points once a job completes. Called by the Song Sections tab. |
| `reaper/midi_drums/riff_lock.lua` | Logic lifted from `create_beat_from_riff.lua`: resolving the selected item's audio source or rendering a bar-aligned time selection, bar-alignment offset math, importing the resulting MIDI. Called by the Riff-Lock Beat tab. |
| `reaper/midi_drums/settings.lua` | Thin wrapper over REAPER `ExtState` (section `"midi_drums"`) holding every currently-scattered default: `python_exe`, default genre/style/mapping/AI tempo, sidecar path override. Read/written by the Settings tab; read as defaults by the other two tabs. |

`reaper/midi_drums_help.lua` is retired. Its content splits between the
in-panel contextual-help popovers (mode-specific, shown where the
confusion actually happens) and a static "About" block in the Settings
tab (for information that isn't tied to any one control).

### ReaImGui as a hard prerequisite

The panel checks for ReaImGui on load (its API surface, e.g.
`reaper.ImGui_GetVersion`) and — if missing — shows a `ShowMessageBox`
pointing at `reaper/README.md`'s new "Prerequisites for the upcoming
unified panel" section, then exits without opening a broken window. No
in-panel install flow is attempted; ReaPack's own package browser is the
install path.

## UI Design

Already approved via the interactive mockup linked above; described here
for the record, not re-derived.

**Song Sections tab** — a Mode segmented control (REAPER / Sidecar / AI /
Song Map) with a "?" contextual-help popover explaining who decides the
song structure in each: REAPER's own hardcoded section table; an
already-existing sidecar JSON file; the AI agent drafting from a text
description; or a song-map JSON with per-segment tempo/meter changes.
Selecting AI mode reveals a description textarea. Below that: genre,
style, drummer, tempo, time signature, and mapping fields. A Generate
button and a status pill (Idle / Running / Done / Error) sit at the
bottom.

**Riff-Lock Beat tab** — genre/style/grid fields, a Lock Strength slider,
and a Snare Reaction segmented control (Off / Reinforce / Stab) with its
own "?" popover explaining each mode's effect on the snare. Selecting
Stab reveals a Stab Threshold slider that's otherwise hidden. Same
Generate button / status pill pattern as Song Sections.

**Settings tab** — `python_exe` path, default genre/style/mapping,
default AI tempo, sidecar path override. Auto-saved on change (to
`ExtState`, via `settings.lua`) — no explicit Save button, consistent
with how REAPER itself persists most per-project/per-install settings.

**Log tab** — a scrolling monospace log area fed by `job_runner`'s
`poll()` loop, with a header showing the running job's name, elapsed
time (tabular-nums), and status pill. Whichever tab launched the current
job, the Log tab's own tab button shows a pulsing "live" dot badge while
it's running, visible even when another tab is focused — this is what
makes the async design (see Data Flow) legible to the user rather than
just internally correct.

**Visual identity** — reuses this project's existing dark DAW palette and
type tokens verbatim from `docs/site-pages/site.css` (`--bg: #0a0f17`,
`--violet: #a78bfa`, `--amber: #fbbf24`, `--sky: #38bdf8`,
`--green: #4ade80`, IBM Plex Mono for monospace/log content, Inter for
UI labels), so the panel reads as the same product as the docs site
rather than a visually disconnected tool.

## Data Flow

1. User configures a tab (Song Sections or Riff-Lock Beat) and clicks
   Generate.
2. The tab handler builds the same CLI argument list the retired scripts
   already build today (`generate --sidecar ...`, `riff --audio ...`,
   etc.) and calls `job_runner.start(cmd, on_complete)`.
3. `job_runner.start()` launches Python **detached** — output redirected
   to a temp log file, with a trailing `DONE <exitcode>` marker line
   appended once the process exits. It stores job state (log file path,
   start time, `on_complete` callback, launching tab) in memory, flips
   status to "Running," and disables both tabs' Generate buttons — only
   one job runs at a time, system-wide, so there's no race between two
   subprocess writes or two REAPER-project mutations landing
   concurrently.
4. The panel's `defer()` loop calls `job_runner.poll()` every frame:
   it tails any new bytes appended to the log file since the last read
   and appends them to the Log tab's buffer, and watches for the `DONE`
   marker.
5. On `DONE 0`: the job's `on_complete` callback — owned by
   `sections.lua` or `riff_lock.lua`, whichever tab launched it — performs
   the actual REAPER-side mutation: importing the generated MIDI,
   placing markers/regions/tempo points. **This is the only point in the
   whole flow that touches REAPER project state**, deliberately deferred
   until the subprocess is confirmed to have finished cleanly, so a
   failed or partial run never leaves the project half-mutated.
6. On `DONE <nonzero>`: status moves to an "Error" pill instead, and the
   last several log lines remain visible in the Log tab rather than being
   discarded.

This single execution path is used uniformly for every mode — the fast
template/sidecar/song-map paths (~1-2s) resolve within a frame or two of
polling; the slow AI path (~20-45s) streams progressively over the same
mechanism. There is no separate blocking code path to maintain.

## Error Handling

**Principle: instructions propagate to the point of failure.** Every row
below shows the actual remediation text inline, in the panel, at the
moment the failure is visible — never just a pointer telling the user to
go read a doc elsewhere. Pointing at `reaper/README.md` is fine as
*supplementary* detail for a user who wants the full picture, but the
UI itself must never be the one making them leave REAPER to find out
what to do next.

| Condition | Behavior |
|---|---|
| ReaImGui not installed | `ShowMessageBox` shows the install steps themselves inline — the ReaPack URL and the "Browse packages → search ReaImGui → Install → Synchronize" steps from `reaper/README.md`'s Prerequisites section — not just a pointer to that file. Panel does not open. To avoid the two copies drifting apart, the message-box string lives as one Lua constant in `midi_drums_panel.lua` (e.g. `REAIMGUI_INSTALL_STEPS`), and the README's Prerequisites section is written to quote that same text verbatim, with a comment on each side noting it must stay in sync with the other. |
| Missing or stale `python_exe` | Already inline by construction: the `ExtState`-backed `GetUserInputs` prompt fires right where the failure would otherwise occur, pre-filled with the old value, and the same field is always visible/editable on the Settings tab afterward — no separate doc reference needed here at all. |
| Subprocess or analysis failure (bad path, missing `librosa`, invalid time signature, etc.) | Nonzero exit code from the `DONE` marker surfaces directly in the Log tab, and critically the **log content itself carries the fix**, not just "job failed": the Python CLI's existing import guards already print actionable remediation text as part of their error output (e.g. the `riff` command's `librosa` guard prints `uv sync --group audio` directly, per this repo's established convention — see `CLAUDE.md`'s Riff-Locked Drums section) rather than a bare traceback. The panel does no filtering or summarizing of this output, so whatever remediation text the CLI already prints reaches the Log tab verbatim. No Lua-side duplication of these messages is needed or wanted — Python remains the single source of truth for its own dependency/validation errors. |
| Concurrent Generate clicks | Prevented by the single-job-at-a-time lock in Data Flow step 3; both tabs' Generate buttons are disabled while any job is running. |
| REAPER crash or panel closed mid-job (**accepted v1 limitation**) | Because the process is detached, it keeps running independently and still writes its log/marker file to disk, but the panel's in-memory job state (the `on_complete` callback binding) is lost. Reopening the panel does not resume tracking that job. This is explicitly accepted, not silently ignored: it is no worse than today's blocking `io.popen` call also dying with REAPER on a crash — not a regression, just not solved by this design. A persistent job registry is a possible future follow-up, out of scope here (see Non-goals). |

## Testing

This repo has no existing Lua test runner — none of the three scripts
being replaced have automated tests today, so this design doesn't
introduce a gap relative to current practice. Verification is a manual
REAPER pass covering:

- ReaImGui-missing message box (verify by temporarily disabling the
  ReaImGui package via ReaPack).
- Settings tab values persist across a REAPER restart (`ExtState`
  round-trip).
- All four Song Sections modes end-to-end (REAPER, Sidecar, AI, Song
  Map), each producing correct markers/regions/tempo points.
- Both Riff-Lock Beat source paths: an audio-take item, and a MIDI/VSTi
  take requiring a bar-aligned render.
- A deliberately broken `python_exe` path, confirming the failure
  surfaces in the Log tab rather than failing silently or only in the
  REAPER console.
- Rapid double-clicking Generate, confirming the concurrency guard
  prevents a second job from starting.

Logic with no REAPER API dependency — bar-alignment offset math, sidecar/
song-map JSON construction, log-line and `DONE`-marker parsing — is
written as plain Lua functions with no `reaper.*` calls, so it *could*
gain automated tests if a Lua test runner is ever added to this repo.
That's a nice-to-have, not a v1 blocker.

No changes are needed on the Python side: the panel invokes the same
documented `midi-drums` CLI commands and flags the retired scripts
already used, so the existing 645-test pytest suite is unaffected by
this design.

## Summary of file-level changes

| File | Change |
|---|---|
| `reaper/midi_drums_panel.lua` | New — entry point, ReaImGui window, tab wiring, help popovers. |
| `reaper/midi_drums/job_runner.lua` | New — async subprocess execution engine. |
| `reaper/midi_drums/sections.lua` | New — logic extracted from `create_song_sections.lua`. |
| `reaper/midi_drums/riff_lock.lua` | New — logic extracted from `create_beat_from_riff.lua`. |
| `reaper/midi_drums/settings.lua` | New — `ExtState` settings wrapper. |
| `reaper/create_song_sections.lua` | Removed — superseded by `sections.lua` + the panel. |
| `reaper/create_beat_from_riff.lua` | Removed — superseded by `riff_lock.lua` + the panel. |
| `reaper/midi_drums_help.lua` | Removed — superseded by in-panel contextual help + Settings "About" block. |
| `reaper/README.md` | Updated (Prerequisites section already added this session; Scripts/Install sections need updating once the panel ships to describe the panel instead of the three retired scripts). |
| `CLAUDE.md` | "REAPER Lua Script Integration" section needs rewriting once implemented — the four-mode table and IPC description still apply conceptually but need reframing around the panel rather than three separate script invocations. |

No Python-side files change as part of this design.
