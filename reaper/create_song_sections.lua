-- create_song_sections.lua
-- midi_drums × REAPER bi-directional integration
-- Part of: https://github.com/fsecada01/midi-drums
--
-- ─────────────────────────────────────────────────────────────────────────────
-- QUICK START
--   1. Set PYTHON_EXE below to your midi_drums virtualenv python.
--   2. Actions → Load ReaScript → select this file → assign a shortcut.
--   3. Run midi_drums_help.lua (same folder) for full in-REAPER help.
-- ─────────────────────────────────────────────────────────────────────────────
--
-- THREE MODES  (chosen via dialog each time you run)
--
--   YES          REAPER mode  (default)
--   ├─ Uses the REAPER_SECTIONS table defined below
--   ├─ Creates timeline regions
--   ├─ Writes midi_drums_sections.json sidecar to project folder
--   └─ Optionally calls Python template engine → drums.mid → auto-imported
--      (~1-2 s, no AI key required)
--
--   NO → YES     Python sidecar mode
--   ├─ Reads midi_drums_sections.json written by:
--   │      api.save_as_midi_with_sidecar(song, "drums.mid")
--   ├─ Creates regions matching Python's structure
--   └─ Offers to sync project tempo from sidecar
--      (import drums.mid manually via Media Explorer)
--
--   NO → NO      AI agent mode
--   ├─ Prompts for a natural-language description + tempo
--   ├─ Calls: python -m midi_drums prompt "..." --song --write-sidecar ...
--   ├─ AI composes song → writes drums.mid + sidecar (~20-45 s)
--   ├─ Project tempo synced to AI-chosen BPM
--   ├─ Regions created from AI structure
--   └─ drums.mid auto-imported on a new track
--      (requires ANTHROPIC_API_KEY / OPENAI_API_KEY in .env)
--
-- SIDECAR FORMAT  (midi_drums_sections.json)
--   {
--     "source": "reaper",          -- "reaper" | "python"
--     "tempo": 70,
--     "time_signature": [4, 4],
--     "sections": [
--       {"name": "Intro",  "bars": 8},
--       {"name": "Verse",  "bars": 16},
--       ...
--     ]
--   }
--
-- PYTHON API EQUIVALENTS
--   api.export_sections_json(song, path)           -- write sidecar from Song
--   api.create_song_from_sections_json(path, genre) -- read sidecar → Song
--   api.save_as_midi_with_sidecar(song, "drums.mid") -- MIDI + sidecar
--
-- CLI EQUIVALENTS
--   midi-drums generate --genre metal --sidecar sidecar.json --output drums.mid
--   midi-drums prompt "heavy doom" --song --write-sidecar sidecar.json -o drums.mid
--
-- TROUBLESHOOTING
--   • "Generation Failed"  → check PYTHON_EXE + REAPER Console (Ctrl+Alt+R)
--   • "Sidecar Not Found"  → run save_as_midi_with_sidecar in Python first
--   • AI API error         → set ANTHROPIC_API_KEY in .env; run: uv sync --group ai
--   • AI too slow          → try Groq (GROQ_API_KEY, AI_PROVIDER=groq in .env)
-- ─────────────────────────────────────────────────────────────────────────────

-- ===========================================================================
-- USER CONFIG
-- ===========================================================================

-- Path to the Python executable inside the midi_drums virtualenv.
-- pythonw.exe suppresses the console window on Windows.
local PYTHON_EXE = "C:/path/to/midi_drums/.venv/Scripts/pythonw.exe"

-- Override sidecar path (nil = <project dir>/midi_drums_sections.json)
local SIDECAR_PATH = nil

-- Defaults pre-filled in the template generation dialog
local DEFAULT_GENRE   = "metal"
local DEFAULT_STYLE   = "doom"
local DEFAULT_MAPPING = "ezdrummer3"

-- Default tempo pre-filled in the AI generation dialog
local DEFAULT_AI_TEMPO = "120"

-- ===========================================================================

local SIDECAR_FILENAME = "midi_drums_sections.json"

-- ---------------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------------
local function get_project_dir()
  local p = reaper.GetProjectPath("")
  return (p ~= "") and p or reaper.GetResourcePath()
end

local function get_sidecar_path()
  return SIDECAR_PATH or (get_project_dir() .. "/" .. SIDECAR_FILENAME)
end

local function sections_to_json(sections, tempo, num, denom)
  local parts = {}
  for _, s in ipairs(sections) do
    parts[#parts + 1] = string.format(
      '    {"name": "%s", "bars": %d}', s.name, s.bars
    )
  end
  return string.format(
    '{\n'
    .. '  "source": "reaper",\n'
    .. '  "tempo": %g,\n'
    .. '  "time_signature": [%d, %d],\n'
    .. '  "sections": [\n%s\n  ]\n'
    .. '}',
    tempo, num, denom, table.concat(parts, ",\n")
  )
end

local function parse_sidecar(content)
  local tempo = tonumber(content:match('"tempo"%s*:%s*([%d%.]+)'))
  if not tempo then
    return nil, nil, nil, nil, "Could not parse 'tempo'."
  end
  local ts_num, ts_denom = content:match(
    '"time_signature"%s*:%s*%[%s*(%d+)%s*,%s*(%d+)%s*%]'
  )
  ts_num   = tonumber(ts_num)   or 4
  ts_denom = tonumber(ts_denom) or 4
  local sections = {}
  for name, bars in content:gmatch(
    '"name"%s*:%s*"([^"]+)"%s*,%s*"bars"%s*:%s*(%d+)'
  ) do
    sections[#sections + 1] = { name = name, bars = tonumber(bars) }
  end
  if #sections == 0 then
    return nil, nil, nil, nil, "No sections found."
  end
  return tempo, ts_num, ts_denom, sections
end

-- Run a Python command via io.popen, return (ok, output_string).
local function run_python(cmd)
  reaper.ShowConsoleMsg("midi_drums: " .. cmd .. "\n")
  local handle = io.popen(cmd .. " 2>&1")
  local out    = handle:read("*a")
  local ok     = handle:close()
  if out and out ~= "" then
    reaper.ShowConsoleMsg(out .. "\n")
  end
  return ok, out
end

-- Sanitise a string for use inside a double-quoted cmd.exe argument.
-- cmd.exe treats &|^<>% as special even inside double quotes, so strip
-- them along with embedded quotes/newlines rather than trying to replicate
-- cmd.exe's notoriously inconsistent escaping rules.
local function shell_escape(s)
  s = s:gsub("[\r\n]", " ")
  s = s:gsub('"', "'")
  s = s:gsub("[&|^<>%%]", "")
  return s
end

-- ---------------------------------------------------------------------------
-- Mode selection — two dialogs to cover three choices
-- ---------------------------------------------------------------------------
local mode_choice = reaper.ShowMessageBox(
  "Select drum generation mode:\n\n"
  .. "YES    = REAPER  — use sections defined in this script (default)\n"
  .. "NO     = External source (Python sidecar or AI agent)",
  "Drum Generation Mode", 4   -- MB_YESNO
)

local MODE = "reaper"

if mode_choice ~= 6 then   -- user chose External
  local ext_choice = reaper.ShowMessageBox(
    "External source:\n\n"
    .. "YES    = Python sidecar  — read midi_drums_sections.json\n"
    .. "NO     = AI agent  — enter a natural language description",
    "External Source", 4
  )
  MODE = (ext_choice == 6) and "sidecar" or "ai"
end

-- ---------------------------------------------------------------------------
-- Build sections + timing
-- ---------------------------------------------------------------------------
local REAPER_SECTIONS = {
  { name = "Intro",  bars = 8  },
  { name = "Verse",  bars = 16 },
  { name = "Chorus", bars = 16 },
  { name = "Bridge", bars = 8  },
  { name = "Outro",  bars = 4  },
}

local sections = {}
local bpm      = reaper.Master_GetTempo()
local _, ts_num, ts_denom = reaper.GetProjectTimeSignature2(0)
local midi_out  = get_project_dir() .. "/drums.mid"
local sp        = get_sidecar_path()

-- ── REAPER mode ─────────────────────────────────────────────────────────────
if MODE == "reaper" then
  sections = REAPER_SECTIONS

-- ── Python sidecar mode ──────────────────────────────────────────────────────
elseif MODE == "sidecar" then
  local f = io.open(sp, "r")
  if not f then
    reaper.ShowMessageBox(
      "Could not open sidecar:\n" .. sp
      .. "\n\nCreate it from Python:\n"
      .. "  api.save_as_midi_with_sidecar(song, 'drums.mid')",
      "Sidecar Not Found", 0
    )
    return
  end
  local content = f:read("*all"); f:close()

  local p_tempo, p_num, p_denom, p_sections, err = parse_sidecar(content)
  if not p_sections then
    reaper.ShowMessageBox("Parse error: " .. (err or "?"), "Error", 0)
    return
  end
  sections = p_sections

  if math.abs(p_tempo - bpm) > 0.5 then
    local sync = reaper.ShowMessageBox(
      string.format(
        "Sidecar tempo: %g BPM\nProject tempo: %g BPM\n\nSync project?",
        p_tempo, bpm
      ), "Tempo Mismatch", 4
    )
    if sync == 6 then
      reaper.SetTempoTimeSigMarker(0, -1, 0, -1, -1, p_tempo, 0, 0, false)
      bpm = p_tempo; ts_num = p_num; ts_denom = p_denom
    end
  end

-- ── AI agent mode ────────────────────────────────────────────────────────────
elseif MODE == "ai" then
  -- 1. Get description
  local ok1, desc_csv = reaper.GetUserInputs(
    "AI Drum Description", 1,
    "Describe the drums (e.g. 'heavy doom riff, slow and crushing')",
    "heavy doom riff, slow and crushing"
  )
  if not ok1 then return end
  local description = desc_csv:match("^%s*(.-)%s*$")
  if description == "" then
    reaper.ShowMessageBox("Description cannot be empty.", "Error", 0)
    return
  end

  -- 2. Get tempo
  local ok2, tempo_csv = reaper.GetUserInputs(
    "AI Generation Settings", 1,
    "Tempo (BPM)  — leave blank to let the AI decide",
    DEFAULT_AI_TEMPO
  )
  if not ok2 then return end
  local tempo_str = tempo_csv:match("^%s*(.-)%s*$")
  local tempo_arg = (tempo_str ~= "" and tonumber(tempo_str))
                    and ("--tempo " .. tempo_str) or ""

  -- 3. Warn about wait time (AI calls take 15–45 seconds)
  local confirm = reaper.ShowMessageBox(
    "The AI agent will compose a full song from your description.\n\n"
    .. '"' .. description .. '"\n\n'
    .. "REAPER will be unresponsive for ~20–45 seconds while the AI works.\n\n"
    .. "Continue?",
    "AI Generation — Please Wait", 4
  )
  if confirm ~= 6 then return end

  -- 4. Run the AI agent
  local cmd = string.format(
    '"%s" -m midi_drums prompt "%s" --song %s --output "%s" --write-sidecar "%s"',
    PYTHON_EXE, shell_escape(description), tempo_arg, midi_out, sp
  )

  local ok, py_out = run_python(cmd)

  if not ok then
    reaper.ShowMessageBox(
      "AI generation failed.\nCheck REAPER console for details.\n\n"
      .. "Common causes:\n"
      .. "  • AI API key not set (ANTHROPIC_API_KEY / OPENAI_API_KEY)\n"
      .. "  • AI dependencies not installed (uv sync --group ai)\n"
      .. "  • PYTHON_EXE path incorrect: " .. PYTHON_EXE,
      "Generation Failed", 0
    )
    return
  end

  -- 5. Read back the AI-generated sidecar to build regions
  local sf = io.open(sp, "r")
  if not sf then
    reaper.ShowMessageBox(
      "AI generation succeeded but sidecar not found:\n" .. sp,
      "Sidecar Missing", 0
    )
    return
  end
  local content = sf:read("*all"); sf:close()

  local p_tempo, p_num, p_denom, p_sections, err = parse_sidecar(content)
  if not p_sections then
    reaper.ShowMessageBox("Could not parse AI sidecar: " .. (err or "?"), "Error", 0)
    return
  end

  sections = p_sections
  -- Sync project tempo to the AI-chosen tempo
  if p_tempo and math.abs(p_tempo - bpm) > 0.5 then
    reaper.SetTempoTimeSigMarker(0, -1, 0, -1, -1, p_tempo, 0, 0, false)
    bpm = p_tempo; ts_num = p_num; ts_denom = p_denom
  end
end

-- ---------------------------------------------------------------------------
-- Create REAPER regions
-- ---------------------------------------------------------------------------
-- REAPER's tempo (bpm) is always quarter-note-based regardless of time
-- signature, so a measure's length in quarter notes is ts_num * (4/ts_denom)
-- - e.g. a 6/8 bar is 3 quarter notes long, not 6.
local measure_length = (60.0 / bpm) * ts_num * (4.0 / ts_denom)

reaper.Undo_BeginBlock()
local current_time = 0.0
for _, s in ipairs(sections) do
  local region_end = current_time + (s.bars * measure_length)
  reaper.AddProjectMarker2(0, true, current_time, region_end, s.name, -1, 0)
  current_time = region_end
end
reaper.Undo_EndBlock("Create Song Sections as Regions", -1)
reaper.UpdateArrange()

-- ---------------------------------------------------------------------------
-- REAPER mode: write sidecar, optionally call template Python
-- ---------------------------------------------------------------------------
if MODE == "reaper" then
  local sf = io.open(sp, "w")
  if sf then sf:write(sections_to_json(sections, bpm, ts_num, ts_denom)); sf:close() end

  local gen = reaper.ShowMessageBox(
    "Regions created" .. (sf and ("\nSidecar: " .. sp) or "") .. "\n\n"
    .. "Generate matching MIDI drums with Python now?\n"
    .. "(Uses template engine — no AI required)",
    "Generate MIDI?", 4
  )
  if gen ~= 6 then return end

  local ok_inp, csv = reaper.GetUserInputs(
    "Template Generation Settings", 3,
    "Genre (metal/rock/jazz/funk),Style (doom/heavy/classic…),Mapping (ezdrummer3/gm_drums…)",
    DEFAULT_GENRE .. "," .. DEFAULT_STYLE .. "," .. DEFAULT_MAPPING
  )
  if not ok_inp then return end

  local genre, style, mapping = csv:match("^([^,]+),([^,]+),([^,]+)$")
  genre   = shell_escape((genre   or DEFAULT_GENRE):match("^%s*(.-)%s*$"))
  style   = shell_escape((style   or DEFAULT_STYLE):match("^%s*(.-)%s*$"))
  mapping = shell_escape((mapping or DEFAULT_MAPPING):match("^%s*(.-)%s*$"))

  local cmd = string.format(
    '"%s" -m midi_drums generate --genre "%s" --style "%s" --mapping "%s"'
    .. ' --sidecar "%s" --output "%s"',
    PYTHON_EXE, genre, style, mapping, sp, midi_out
  )

  local ok, _ = run_python(cmd)
  if not ok then
    reaper.ShowMessageBox(
      "Python generation failed.\nCheck REAPER console.\n\nPYTHON_EXE: " .. PYTHON_EXE,
      "Generation Failed", 0
    )
    return
  end
end

-- ---------------------------------------------------------------------------
-- Auto-import MIDI (REAPER and AI modes both produce drums.mid)
-- ---------------------------------------------------------------------------
if MODE == "reaper" or MODE == "ai" then
  local mf = io.open(midi_out, "r")
  if not mf then
    reaper.ShowMessageBox(
      "MIDI file not found after generation:\n" .. midi_out,
      "File Not Found", 0
    )
    return
  end
  mf:close()

  reaper.InsertMedia(midi_out, 0)
  reaper.UpdateArrange()

  local mode_label = (MODE == "ai") and "AI agent" or "template engine"
  reaper.ShowMessageBox(
    "Done!  (" .. mode_label .. ")\nMIDI imported: " .. midi_out,
    "Drums Ready", 0
  )
end
