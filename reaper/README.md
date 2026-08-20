# REAPER Integration Scripts

This directory is the source of truth for the REAPER-side half of the
`midi_drums` sidecar bridge (see `CLAUDE.md`'s "REAPER Lua Script
Integration" section for the full contract). Previously these scripts only
existed locally at `C:/REAPER/Scripts/`, outside version control, so
changes to the shared `midi_drums_sections.json` sidecar contract couldn't
be reviewed or diffed alongside the Python side that shares it.

## Scripts

- **`create_song_sections.lua`** — the main bridge script. Four modes
  (REAPER-defined sections, Python sidecar, AI agent, song-map) create
  matching REAPER timeline regions and optionally generate/import MIDI
  drums.
- **`create_beat_from_riff.lua`** — riff-locked drum generation. Select a
  recorded/rendered guitar or bass riff item, and it generates a drum
  pattern whose kick hits lock to the riff's rhythmic accents (everything
  else - snare, hi-hat, cymbals, drummer styling - still comes from the
  normal genre-plugin pipeline). v1 scope: the riff is analyzed as one
  representative bar and tiled to fill `--bars`. Requires
  `uv sync --group audio` (librosa) inside the `midi_drums` venv — a
  separate extras group from `--group ai`.
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
mklink "C:\REAPER\Scripts\create_beat_from_riff.lua" "C:\path\to\midi_drums\reaper\create_beat_from_riff.lua"
mklink "C:\REAPER\Scripts\midi_drums_help.lua" "C:\path\to\midi_drums\reaper\midi_drums_help.lua"

# Or, if you'd rather not symlink, just copy the files after every edit:
copy reaper\create_song_sections.lua "C:\REAPER\Scripts\"
copy reaper\create_beat_from_riff.lua "C:\REAPER\Scripts\"
copy reaper\midi_drums_help.lua "C:\REAPER\Scripts\"
```

Then in REAPER: **Actions → Load ReaScript** → select `create_song_sections.lua`
→ assign a shortcut. Repeat for `create_beat_from_riff.lua` and
`midi_drums_help.lua` if you want dedicated shortcuts for those too.

Neither script hardcodes a Python path in tracked source — the first time
you run either one, it prompts for your `midi_drums` virtualenv's
`pythonw.exe` path and remembers it in REAPER's persistent `ExtState`
(`reaper.ini`-backed, scoped to this REAPER install, section `midi_drums`,
key `python_exe`), not in a file. Both scripts share the same stored value,
so configuring it via either one configures the other too. If the
configured path stops resolving (moved venv, new machine, a fresh REAPER
install), the same prompt reappears, pre-filled with the old value so
re-confirming is one click. `create_beat_from_riff.lua` additionally needs
`uv sync --group audio` run once inside that virtualenv (librosa for onset
detection) — this is a separate extras group from `--group ai`.

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
