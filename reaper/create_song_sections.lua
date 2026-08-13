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
-- FOUR MODES  (chosen via dialog each time you run)
--
--   YES          REAPER mode  (default)
--   ├─ Uses the REAPER_SECTIONS table defined below
--   ├─ Creates timeline regions
--   ├─ Writes midi_drums_sections.json sidecar to project folder
--   └─ Optionally calls Python template engine → drums.mid → auto-imported
--      (~1-2 s, no AI key required)
--
--   NO → "sidecar"   Python sidecar mode  (default of the follow-up prompt)
--   ├─ Reads midi_drums_sections.json written by:
--   │      api.save_as_midi_with_sidecar(song, "drums.mid")
--   ├─ Creates regions matching Python's structure
--   └─ Offers to sync project tempo from sidecar
--      (import drums.mid manually via Media Explorer)
--
--   NO → "ai"        AI agent mode
--   ├─ Prompts for a natural-language description + tempo
--   ├─ Calls: python -m midi_drums prompt "..." --song --write-sidecar ...
--   ├─ AI composes song → writes drums.mid + sidecar (~20-45 s)
--   ├─ Project tempo synced to AI-chosen BPM
--   ├─ Regions created from AI structure
--   └─ drums.mid auto-imported on a new track
--      (requires ANTHROPIC_API_KEY / OPENAI_API_KEY in .env)
--
--   NO → "songmap"   Song-map mode  (per-section tempo/meter, issue #53)
--   ├─ Prompts for a song_creator-shaped song-map JSON path + genre/style
--   ├─ Calls: python -m midi_drums generate --song-map ... --write-timeline ...
--   ├─ Reads back the flat timeline JSON (tempo_points + regions +
--   │      color_groups - see DrumGeneratorAPI.export_song_timeline_json)
--   ├─ Places one SetTempoTimeSigMarker per tempo/meter change point
--   ├─ Creates one colored region per song-map region
--   └─ drums.mid auto-imported on a new track
--      (mirrors song_reaper_build.lua's B.apply_to_reaper logic/shape)
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
-- TIMELINE FORMAT  (song-map mode only, midi_drums_timeline.json)
--   {
--     "tempo_points": [{"time": 0.0, "bpm": 144, "num": 4, "denom": 4}, ...],
--     "regions": [{"name": "Verse 1", "color_group": "groove",
--                  "start_time": 8.0, "end_time": 20.0}, ...],
--     "color_groups": [{"name": "groove", "r": 200, "g": 120, "b": 40}, ...],
--     "total_time": 123.4
--   }
--
-- PYTHON API EQUIVALENTS
--   api.export_sections_json(song, path)           -- write sidecar from Song
--   api.create_song_from_sections_json(path, genre) -- read sidecar → Song
--   api.save_as_midi_with_sidecar(song, "drums.mid") -- MIDI + sidecar
--   api.create_song_from_song_map(song_map, genre)  -- read song-map → Song
--   api.export_song_timeline_json(song, path)       -- write flat timeline
--
-- CLI EQUIVALENTS
--   midi-drums generate --genre metal --sidecar sidecar.json --output drums.mid
--   midi-drums prompt "heavy doom" --song --write-sidecar sidecar.json -o drums.mid
--   midi-drums generate --genre metal --song-map map.json --write-timeline t.json -o drums.mid
--
-- TROUBLESHOOTING
--   • "Generation Failed"  → check PYTHON_EXE + REAPER Console (Ctrl+Alt+R)
--   • "Sidecar Not Found"  → run save_as_midi_with_sidecar in Python first
--   • "Timeline Not Found" → check the --song-map path is valid JSON
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

local SIDECAR_FILENAME  = "midi_drums_sections.json"
local TIMELINE_FILENAME = "midi_drums_timeline.json"

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

local function get_timeline_path()
  return get_project_dir() .. "/" .. TIMELINE_FILENAME
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

-- Parse the flat timeline JSON written by
-- DrumGeneratorAPI.export_song_timeline_json (song-map mode). Kept
-- deliberately flat on the Python side (no nested objects-within-objects)
-- so it can be read here with plain string patterns - no JSON library.
local function parse_timeline(content)
  local tempo_points = {}
  for time, bpm, num, denom in content:gmatch(
    '"time"%s*:%s*([%-%d%.]+)%s*,%s*"bpm"%s*:%s*([%-%d%.]+)%s*,'
    .. '%s*"num"%s*:%s*(%d+)%s*,%s*"denom"%s*:%s*(%d+)'
  ) do
    tempo_points[#tempo_points + 1] = {
      time = tonumber(time), bpm = tonumber(bpm),
      num = tonumber(num), denom = tonumber(denom),
    }
  end

  local regions = {}
  for name, color_group, start_time, end_time in content:gmatch(
    '"name"%s*:%s*"([^"]*)"%s*,%s*"color_group"%s*:%s*"([^"]*)"%s*,'
    .. '%s*"start_time"%s*:%s*([%-%d%.]+)%s*,%s*"end_time"%s*:%s*([%-%d%.]+)'
  ) do
    regions[#regions + 1] = {
      name = name, color_group = color_group,
      start_time = tonumber(start_time), end_time = tonumber(end_time),
    }
  end

  local color_groups = {}
  for name, r, g, b in content:gmatch(
    '"name"%s*:%s*"([^"]*)"%s*,%s*"r"%s*:%s*(%d+)%s*,'
    .. '%s*"g"%s*:%s*(%d+)%s*,%s*"b"%s*:%s*(%d+)'
  ) do
    color_groups[name] = { r = tonumber(r), g = tonumber(g), b = tonumber(b) }
  end

  if #tempo_points == 0 or #regions == 0 then
    return nil, nil, nil, "Could not parse timeline (no tempo_points/regions)."
  end
  return tempo_points, regions, color_groups
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

-- Shared by the ai/songmap/reaper-template blocks below: run a Python
-- command and, on failure, show one standard error dialog instead of
-- each mode hand-rolling its own wording (which had already drifted
-- between modes before this helper existed). Returns captured
-- stdout/stderr on success, or nil on failure (caller should `return`).
local function run_python_or_fail(cmd, extra_hint)
  local ok, py_out = run_python(cmd)
  if not ok then
    reaper.ShowMessageBox(
      "Python generation failed.\nCheck REAPER console for details.\n\n"
      .. (extra_hint or ("PYTHON_EXE: " .. PYTHON_EXE)),
      "Generation Failed", 0
    )
    return nil
  end
  return py_out
end

-- Shared read-back-after-generation step: open a file Python was just
-- asked to write, show one standard "missing" dialog if it isn't
-- there. Returns the file's content on success, or nil on failure
-- (caller should `return`).
local function read_generated_file_or_fail(path, what)
  local f = io.open(path, "r")
  if not f then
    reaper.ShowMessageBox(
      "Generation succeeded but " .. what .. " not found:\n" .. path,
      what .. " Not Found", 0
    )
    return nil
  end
  local content = f:read("*all")
  f:close()
  return content
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
-- Mode selection — a dialog + a text prompt to cover four choices
-- ---------------------------------------------------------------------------
local mode_choice = reaper.ShowMessageBox(
  "Select drum generation mode:\n\n"
  .. "YES    = REAPER  — use sections defined in this script (default)\n"
  .. "NO     = External source (sidecar / AI agent / song-map)",
  "Drum Generation Mode", 4   -- MB_YESNO
)

local MODE = "reaper"

if mode_choice ~= 6 then   -- user chose External
  local ok_ext, ext_input = reaper.GetUserInputs(
    "External Source", 1,
    "Mode: sidecar / ai / songmap",
    "sidecar"
  )
  if not ok_ext then return end
  -- Normalize away whitespace/hyphens/underscores so "song-map",
  -- "song map", and "songmap" all resolve the same way, instead of
  -- silently falling into sidecar mode on any variant we didn't
  -- special-case.
  local ext_mode = ext_input:match("^%s*(.-)%s*$"):lower():gsub("[%s%-_]", "")
  if ext_mode == "ai" then
    MODE = "ai"
  elseif ext_mode == "songmap" then
    MODE = "songmap"
  elseif ext_mode == "sidecar" or ext_mode == "" then
    MODE = "sidecar"
  else
    reaper.ShowMessageBox(
      "Unrecognized external source: '" .. ext_input .. "'\n\n"
      .. "Expected one of: sidecar, ai, songmap.",
      "Invalid Mode", 0
    )
    return
  end
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

  local py_out = run_python_or_fail(
    cmd,
    "Common causes:\n"
    .. "  • AI API key not set (ANTHROPIC_API_KEY / OPENAI_API_KEY)\n"
    .. "  • AI dependencies not installed (uv sync --group ai)\n"
    .. "  • PYTHON_EXE path incorrect: " .. PYTHON_EXE
  )
  if not py_out then return end

  -- 5. Read back the AI-generated sidecar to build regions
  local content = read_generated_file_or_fail(sp, "sidecar")
  if not content then return end

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

-- ── Song-map mode (issue #53: per-section tempo/meter) ──────────────────────
elseif MODE == "songmap" then
  local ok_map, map_input = reaper.GetUserInputs(
    "Song-Map Source", 1,
    "Path to song-map JSON (regions with per-segment bars/bpm/num/denom)",
    get_project_dir() .. "/song_map.json"
  )
  if not ok_map then return end
  local map_path = map_input:match("^%s*(.-)%s*$")
  if map_path == "" then
    reaper.ShowMessageBox("Song-map path cannot be empty.", "Error", 0)
    return
  end

  local mf_check = io.open(map_path, "r")
  if not mf_check then
    reaper.ShowMessageBox(
      "Could not open song-map JSON:\n" .. map_path, "Song Map Not Found", 0
    )
    return
  end
  mf_check:close()

  local ok_inp, csv = reaper.GetUserInputs(
    "Song-Map Generation Settings", 3,
    "Genre (metal/rock/jazz/funk),Style (doom/heavy/classic…),Mapping (ezdrummer3/gm_drums…)",
    DEFAULT_GENRE .. "," .. DEFAULT_STYLE .. "," .. DEFAULT_MAPPING
  )
  if not ok_inp then return end

  local genre, style, mapping = csv:match("^([^,]+),([^,]+),([^,]+)$")
  genre   = shell_escape((genre   or DEFAULT_GENRE):match("^%s*(.-)%s*$"))
  style   = shell_escape((style   or DEFAULT_STYLE):match("^%s*(.-)%s*$"))
  mapping = shell_escape((mapping or DEFAULT_MAPPING):match("^%s*(.-)%s*$"))

  local timeline_path = get_timeline_path()
  local cmd = string.format(
    '"%s" -m midi_drums generate --genre "%s" --style "%s" --mapping "%s"'
    .. ' --song-map "%s" --write-timeline "%s" --output "%s"',
    PYTHON_EXE, genre, style, mapping, map_path, timeline_path, midi_out
  )

  if not run_python_or_fail(cmd) then return end

  local timeline_content = read_generated_file_or_fail(timeline_path, "timeline")
  if not timeline_content then return end

  local tempo_points, regions, color_groups, terr = parse_timeline(timeline_content)
  if not tempo_points then
    reaper.ShowMessageBox("Could not parse timeline: " .. (terr or "?"), "Error", 0)
    return
  end

  -- Mirrors song_reaper_build.lua's B.apply_to_reaper: one tempo/time-sig
  -- marker per resolved change point, one colored region per song-map
  -- region - rather than the single global measure_length this script's
  -- other modes use, since song-map songs may vary tempo/meter per bar.
  reaper.Undo_BeginBlock()
  for _, tp in ipairs(tempo_points) do
    reaper.SetTempoTimeSigMarker(
      0, -1, tp.time, -1, -1, tp.bpm, tp.num, tp.denom, false
    )
  end
  for _, r in ipairs(regions) do
    local color = 0
    local cg = color_groups[r.color_group]
    if cg then
      color = reaper.ColorToNative(cg.r, cg.g, cg.b) | 0x1000000
    end
    reaper.AddProjectMarker2(0, true, r.start_time, r.end_time, r.name, -1, color)
  end
  reaper.Undo_EndBlock("Create Song Sections from Song Map", -1)
  reaper.UpdateArrange()
end

-- ---------------------------------------------------------------------------
-- Create REAPER regions (song-map mode creates its own above, from the
-- resolved per-segment timeline rather than one global measure_length)
-- ---------------------------------------------------------------------------
if MODE ~= "songmap" then
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
end

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

  if not run_python_or_fail(cmd) then return end
end

-- ---------------------------------------------------------------------------
-- Auto-import MIDI (REAPER, AI, and song-map modes all produce drums.mid)
-- ---------------------------------------------------------------------------
if MODE == "reaper" or MODE == "ai" or MODE == "songmap" then
  if not read_generated_file_or_fail(midi_out, "MIDI file") then return end

  reaper.InsertMedia(midi_out, 0)
  reaper.UpdateArrange()

  local mode_label = (MODE == "ai") and "AI agent"
    or (MODE == "songmap") and "song-map engine"
    or "template engine"
  reaper.ShowMessageBox(
    "Done!  (" .. mode_label .. ")\nMIDI imported: " .. midi_out,
    "Drums Ready", 0
  )
end
