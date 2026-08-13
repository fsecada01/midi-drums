-- midi_drums_help.lua
-- Run this as a REAPER action to display midi_drums integration help.
-- Actions → Load ReaScript → select this file → assign a shortcut.

local HELP = [[
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  midi_drums  ×  REAPER Integration
  Script: create_song_sections.lua
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SETUP (one-time)
  1. Open create_song_sections.lua in a text editor.
  2. Set PYTHON_EXE to your virtualenv python:
       C:/path/to/midi_drums/.venv/Scripts/pythonw.exe
  3. Actions → Load ReaScript → select create_song_sections.lua
  4. Assign a keyboard shortcut for quick access.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THREE MODES  (chosen each time you run the script)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌─ Dialog 1 ──────────────────────────────────────┐
  │  YES  →  REAPER mode  (default)                 │
  │  NO   →  Dialog 2 (external source)             │
  └─────────────────────────────────────────────────┘

  ┌─ Dialog 2 (if NO above) ────────────────────────┐
  │  YES  →  Python sidecar mode                    │
  │  NO   →  AI agent mode                          │
  └─────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODE 1 — REAPER  (you define the structure)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Edit REAPER_SECTIONS in the script to set section names
  and bar counts, then run the script.

  What happens:
    • REAPER timeline regions created from the table
    • midi_drums_sections.json written to project folder
    • Optional: generate matching MIDI drums right now?
        → Genre/style/mapping dialog → template engine
        → drums.mid generated (~1-2 s) → auto-imported

  To use the sidecar later in Python:
    from midi_drums.api.python_api import DrumGeneratorAPI
    api = DrumGeneratorAPI()
    song = api.create_song_from_sections_json(
        r"<project_dir>/midi_drums_sections.json",
        genre="metal", style="doom"
    )
    api.save_as_midi(song, "drums.mid")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODE 2 — Python sidecar  (Python defines the structure)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  First generate in Python:
    song = api.create_song("metal", "doom", tempo=70)
    api.save_as_midi_with_sidecar(song, "drums.mid")
    # → writes drums.mid + midi_drums_sections.json

  Then run script (NO → YES):
    • Sidecar read → regions created to match Python's structure
    • Tempo sync offered if sidecar BPM differs from project

  Import drums.mid manually: Media Explorer or drag-and-drop.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODE 3 — AI agent  (natural language drives everything)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Prerequisites:
    uv sync --group ai
    # Set in .env:  ANTHROPIC_API_KEY=sk-ant-...
    #            or OPENAI_API_KEY=sk-...
    #            or GROQ_API_KEY=gsk_...

  Run script (NO → NO):
    1. Enter a description, e.g.:
         "heavy doom riff, slow and crushing with sparse fills"
         "Testament-style thrash, Hoglan blast beats, 185 BPM"
         "jazz trio, brushed swing feel, medium tempo"
    2. Enter tempo (or leave blank — AI will choose)
    3. Confirm the ~20-45 second wait
    4. AI composes song → drums.mid + sidecar written
    5. Project tempo synced to AI-chosen BPM
    6. Regions created from AI structure
    7. drums.mid auto-imported on a new track

  Output location: <project_dir>/drums.mid
  Sidecar:         <project_dir>/midi_drums_sections.json

  Check REAPER Console (Ctrl+Alt+R) for Python output / errors.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SIDECAR FORMAT  (midi_drums_sections.json)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  {
    "source": "reaper",       // "reaper" | "python"
    "tempo": 70,
    "time_signature": [4, 4],
    "sections": [
      {"name": "Intro",  "bars": 8},
      {"name": "Verse",  "bars": 16},
      {"name": "Chorus", "bars": 16},
      {"name": "Bridge", "bars": 8},
      {"name": "Outro",  "bars": 4}
    ]
  }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLI EQUIVALENTS  (run outside REAPER)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  # Template generation from REAPER sidecar:
  midi-drums generate --genre metal --style doom \
      --sidecar midi_drums_sections.json \
      --output drums.mid

  # AI generation + write sidecar for REAPER:
  midi-drums prompt "heavy doom metal" \
      --song --write-sidecar midi_drums_sections.json \
      --output drums.mid

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  "Generation Failed"
    → Check PYTHON_EXE path in create_song_sections.lua
    → Check REAPER Console (Ctrl+Alt+R) for Python errors

  "Sidecar Not Found"
    → In Python mode: run save_as_midi_with_sidecar first
    → In AI mode: check that PYTHON_EXE is correct

  "AI generation failed / API key"
    → Set ANTHROPIC_API_KEY (or OPENAI_API_KEY) in .env
    → Run: uv sync --group ai   (installs AI dependencies)

  AI takes too long / times out
    → Try Groq (GROQ_API_KEY) — fastest inference
    → Set AI_PROVIDER=groq in .env

  Project docs:  https://fsecada01.github.io/midi-drums/
  REAPER forum:  https://forum.cockos.com/forumdisplay.php?f=22
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
]]

-- Print to REAPER console
reaper.ShowConsoleMsg(HELP)

-- Also show a compact popup for quick reference
reaper.ShowMessageBox(
  "midi_drums integration help printed to REAPER Console.\n\n"
  .. "Open Console:  View → Show REAPER console  (Ctrl+Alt+R)\n\n"
  .. "MODES:\n"
  .. "  YES        = REAPER  (edit REAPER_SECTIONS in script)\n"
  .. "  NO → YES   = Python sidecar  (run save_as_midi_with_sidecar first)\n"
  .. "  NO → NO    = AI agent  (enter a natural language description)\n\n"
  .. "Output: <project_dir>/drums.mid\n"
  .. "Sidecar: <project_dir>/midi_drums_sections.json",
  "midi_drums Help",
  0
)
