# REAPER Integration Scripts

This directory is the source of truth for the REAPER-side half of the
`midi_drums` sidecar bridge (see `CLAUDE.md`'s "REAPER Lua Script
Integration" section for the full contract). Previously these scripts only
existed locally at `C:/REAPER/Scripts/`, outside version control, so
changes to the shared `midi_drums_sections.json` sidecar contract couldn't
be reviewed or diffed alongside the Python side that shares it.

## Scripts

- **`create_song_sections.lua`** — the main bridge script. Three modes
  (REAPER-defined sections, Python sidecar, AI agent) create matching
  REAPER timeline regions and optionally generate/import MIDI drums.
- **`midi_drums_help.lua`** — an in-REAPER help screen. Run it as a REAPER
  action any time for a refresher on setup and usage.

## Install

REAPER only loads ReaScripts from paths it knows about (typically
`REAPER_RESOURCE_PATH/Scripts/`), so the files here need a copy or symlink
into that directory — REAPER's own copy is a deployed instance, this
directory is the source of truth:

```bash
# Windows (from an elevated shell, one-time):
mklink "C:\REAPER\Scripts\create_song_sections.lua" "C:\path\to\midi_drums\reaper\create_song_sections.lua"
mklink "C:\REAPER\Scripts\midi_drums_help.lua" "C:\path\to\midi_drums\reaper\midi_drums_help.lua"

# Or, if you'd rather not symlink, just copy the files after every edit:
copy reaper\create_song_sections.lua "C:\REAPER\Scripts\"
copy reaper\midi_drums_help.lua "C:\REAPER\Scripts\"
```

Then in REAPER: **Actions → Load ReaScript** → select `create_song_sections.lua`
→ assign a shortcut. Repeat for `midi_drums_help.lua` if you want a
dedicated help shortcut too.

Before first use, open `create_song_sections.lua` and set `PYTHON_EXE` to
your own `midi_drums` virtualenv's `pythonw.exe` path — the checked-in
value is a placeholder (`C:/path/to/midi_drums/.venv/Scripts/pythonw.exe`).

## `drum_midi_generator.lua` — not vendored

An older standalone script by that name also exists in some local
`REAPER/Scripts/` setups. It predates the sidecar bridge: it has its own
hardcoded GM note table, generates a fixed 4/4 pattern with no fills logic
beyond a single descending-tom fill, and has no awareness of
`midi_drums_sections.json` or the Python side of this project at all. It
is superseded by `create_song_sections.lua` + the Python template/AI
engines and is intentionally left out of this directory.

## Keeping both sides in sync

Per `.claude/system-prompt.md`'s sub-agent policy, sidecar-contract changes
(anything touching the `midi_drums_sections.json` shape, or the Python
`export_sections_json` / `create_song_from_sections_json` /
`save_as_midi_with_sidecar` methods) must be made to this directory and the
Python side **in the same PR**, sequentially rather than in parallel — the
two halves have no shared type system to catch drift for you.
