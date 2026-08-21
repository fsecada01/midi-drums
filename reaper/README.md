# REAPER Integration Scripts

This directory is the source of truth for the REAPER-side half of the
`midi_drums` sidecar bridge (see `CLAUDE.md`'s "REAPER Lua Script
Integration" section for the full contract). Previously these scripts only
existed locally at `C:/REAPER/Scripts/`, outside version control, so
changes to the shared `midi_drums_sections.json` sidecar contract couldn't
be reviewed or diffed alongside the Python side that shares it.

## Prerequisites

The panel is built on ReaImGui, so it needs a couple of installs beyond
the Python venv setup already documented in the main project `CLAUDE.md`:

- **REAPER** — https://www.reaper.fm/ — any reasonably current 6.x/7.x
  install.
- **ReaPack** — https://reapack.com/ — REAPER's package-manager
  extension. Download the installer for your OS from that site and run
  it with REAPER closed; ReaPack's default "ReaTeam Extensions"
  repository index (which carries ReaImGui) is enabled automatically,
  no separate "Import a repository" step needed.
- **ReaImGui** (https://github.com/cfillion/reaimgui) — the Dear ImGui
  binding the panel is built on. Once ReaPack is installed: in REAPER,
  **Extensions → ReaPack → Browse packages...**, search "ReaImGui",
  right-click the result → **Install**, then **Extensions → ReaPack →
  Synchronize packages** and restart REAPER.
- **Python via `uv`** — https://docs.astral.sh/uv/ — same venv the panel
  already needs for every tab. The Riff-Lock Beat tab specifically needs
  `uv sync --group audio` (librosa) run once inside that venv.

The panel checks for ReaImGui on load and shows a message pointing back
to this section if it's missing, rather than failing with a raw Lua
error.

## The panel

`midi_drums_panel.lua` is the single entry point — one REAPER action
("MIDI Drums: Open Panel") opens a dockable ReaImGui window with four
tabs:

- **Song Sections** — four modes (REAPER-defined sections, Python
  sidecar, AI agent, song-map) create matching REAPER timeline regions
  and optionally generate/import MIDI drums. A "?" popover next to the
  mode selector explains each mode.
- **Riff-Lock Beat** — select a recorded/rendered guitar or bass riff
  item, and it generates a drum pattern whose kick hits lock to the
  riff's rhythmic accents (everything else — snare, hi-hat, cymbals,
  drummer styling — still comes from the normal genre-plugin pipeline).
  v1 scope: the riff is analyzed as one representative bar and tiled to
  fill the requested bar count. Requires `uv sync --group audio`
  (librosa) inside the `midi_drums` venv — a separate extras group from
  `--group ai`.
- **Settings** — Python interpreter path and per-tab defaults, backed by
  REAPER `ExtState` and auto-saved as you type.
- **Log** — a live-streaming log of the currently (or most recently) run
  job, with a pulsing `*` badge on the tab title while a job is running.

Generation runs as a detached subprocess (`reaper/midi_drums/job_runner.lua`)
so the panel's UI thread is never blocked; `reaper/midi_drums/sections.lua`
and `reaper/midi_drums/riff_lock.lua` hold the business logic for the
Song Sections and Riff-Lock Beat tabs respectively, and
`reaper/midi_drums/settings.lua` wraps the shared `ExtState` config.

## Install

REAPER only loads ReaScripts from paths it knows about (typically
`REAPER_RESOURCE_PATH/Scripts/`), so the files here need a copy or symlink
into that directory — REAPER's own copy is a deployed instance, this
directory is the source of truth. The panel's supporting modules live in
a `midi_drums/` subdirectory that must be carried over alongside the
entry-point script:

```bash
# Windows (from an elevated shell, one-time):
mklink "C:\REAPER\Scripts\midi_drums_panel.lua" "C:\path\to\midi_drums\reaper\midi_drums_panel.lua"
mklink /D "C:\REAPER\Scripts\midi_drums" "C:\path\to\midi_drums\reaper\midi_drums"

# Or, if you'd rather not symlink, just copy after every edit:
copy reaper\midi_drums_panel.lua "C:\REAPER\Scripts\"
xcopy /E /I /Y reaper\midi_drums "C:\REAPER\Scripts\midi_drums\"
```

Then in REAPER: **Actions → Load ReaScript** → select `midi_drums_panel.lua`
→ assign a shortcut (e.g. "MIDI Drums: Open Panel").

The panel doesn't hardcode a Python path in tracked source — the first
time you click Generate, it prompts for your `midi_drums` virtualenv's
`pythonw.exe` path and remembers it in REAPER's persistent `ExtState`
(`reaper.ini`-backed, scoped to this REAPER install, section `midi_drums`,
key `python_exe`), not in a file. If the configured path stops resolving
(moved venv, new machine, a fresh REAPER install), the same prompt
reappears, pre-filled with the old value so re-confirming is one click.
The Riff-Lock Beat tab additionally needs `uv sync --group audio` run
once inside that virtualenv (librosa for onset detection) — this is a
separate extras group from `--group ai`.

## `drum_midi_generator.lua` — not vendored

An older standalone script by that name also exists in some local
`REAPER/Scripts/` setups. It predates the sidecar bridge: it has its own
hardcoded GM note table, generates a fixed 4/4 pattern with no fills logic
beyond a single descending-tom fill, and has no awareness of
`midi_drums_sections.json` or the Python side of this project at all. It
is superseded by the panel's Song Sections tab + the Python template/AI
engines and is intentionally left out of this directory.

## Keeping both sides in sync

Per `.claude/system-prompt.md`'s sub-agent policy, sidecar-contract changes
(anything touching the `midi_drums_sections.json` shape, or the Python
`export_sections_json` / `create_song_from_sections_json` /
`save_as_midi_with_sidecar` methods) must be made to this directory and the
Python side **in the same PR**, sequentially rather than in parallel — the
two halves have no shared type system to catch drift for you.
