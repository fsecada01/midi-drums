-- create_beat_from_riff.lua
-- midi_drums × REAPER riff-locked drum generation
-- Part of: https://github.com/fsecada01/midi-drums
--
-- ─────────────────────────────────────────────────────────────────────────────
-- QUICK START
--   1. Set PYTHON_EXE below to your midi_drums virtualenv python.
--   2. Record/select a guitar or bass riff item on a track.
--   3. Select that item, then Actions → Load ReaScript → select this file →
--      assign a shortcut → run it.
--   4. `uv sync --group audio` must have been run once inside midi_drums
--      (installs librosa - NOT the same group as `--group ai`).
-- ─────────────────────────────────────────────────────────────────────────────
--
-- WHAT THIS DOES
--   Analyzes the selected riff item's audio for rhythmic accents (onset
--   detection), then generates a normal genre-plugin drum pattern whose
--   KICK hits lock onto those accents - snare, hi-hat, cymbals, and
--   drummer styling all still come from the ordinary generation pipeline
--   untouched (`python -m midi_drums riff`, see CLAUDE.md's "route through
--   genre plugins" design decision).
--
--   v1 scope: the riff is analyzed as ONE representative bar and tiled to
--   fill --bars (same limitation as the CLI's --bars help text) - a
--   multi-bar riff with a changing groove still only locks bar 1.
--
-- TWO SOURCE PATHS  (chosen automatically per the selected item's take)
--
--   Audio take   → fast path: reads the take's own source file directly
--                  (with --audio-offset/--audio-duration slicing to the
--                  item's played region). No rendering, no project state
--                  touched.
--   MIDI/VSTi    → render path: prints the item to a temp WAV via a
--                  bar-aligned TIME SELECTION render (action 42230, "using
--                  most recent settings"). RENDER_FILE / RENDER_PATTERN /
--                  RENDER_BOUNDSFLAG and the time selection are saved
--                  before and restored immediately after the render call,
--                  on every path - so this never corrupts your next manual
--                  render or leaves the time selection changed.
--
-- BAR-ALIGNMENT CORRECTION
--   If the selected item doesn't start on a bar line, position 0.0 of its
--   audio isn't beat 0.0 of a bar, and every accent would silently lock to
--   a phase-shifted riff. This script computes the item's start position in
--   quarter notes (TimeMap2_timeToQN) against the enclosing bar's start and
--   passes the difference as --offset-beats so the CLI corrects for it.
--
-- KNOWN UNVERIFIED (per the design plan - confirm live in a real REAPER
-- session before relying on this in production; this is the one piece of
-- the original design plan that explicitly called out needing empirical
-- confirmation rather than being derivable from the API docs alone):
--   • RENDER_BOUNDSFLAG = 2 ("Time selection") is used deliberately instead
--     of the "selected media items" flag (commonly cited as 4 in community
--     scripts but unverified here) - time selection is the better-attested
--     constant. Double-check the render actually bounds to the expected
--     range the first time you run this against a real project.
--
-- CLI EQUIVALENT
--   python -m midi_drums riff --audio riff.wav --genre metal --style death \
--     --tempo 155 --offset-beats 0.5 --output riff_drums.mid \
--     --write-sidecar midi_drums_riff_sidecar.json
--
-- TROUBLESHOOTING
--   • "uv sync --group audio" guidance → librosa isn't installed; run it
--     inside the midi_drums venv, then retry.
--   • "Generation Failed" → check PYTHON_EXE + REAPER Console (Ctrl+Alt+R).
--   • "Render Failed" → the project's current render format may not be one
--     of wav/flac/aiff/mp3/ogg; set it to WAV via File > Render... once.
-- ─────────────────────────────────────────────────────────────────────────────

-- ===========================================================================
-- USER CONFIG
-- ===========================================================================

local PYTHON_EXE = "C:/path/to/midi_drums/.venv/Scripts/pythonw.exe"

local DEFAULT_GENRE    = "metal"
local DEFAULT_STYLE    = "doom"
local DEFAULT_SECTION  = "verse"
local DEFAULT_MAPPING  = "ezdrummer3"
local DEFAULT_BARS     = "4"
local DEFAULT_GRID     = "16th"
local DEFAULT_LOCK_STRENGTH = "1.0"

-- Not exposed in the dialogs below (kept simple - two dialogs is already a
-- lot to fill in per riff). Edit here if you want a different starting
-- point; these match the CLI's own defaults.
local DEFAULT_HUMANIZATION = 0.0
local DEFAULT_COMPLEXITY   = 0.5

-- ===========================================================================

local MIDI_OUT_FILENAME    = "riff_drums.mid"
local SIDECAR_OUT_FILENAME = "midi_drums_riff_sidecar.json"
local RENDER_PATTERN       = "midi_drums_riff_render"
local RENDER_EXTENSIONS    = { ".wav", ".flac", ".aiff", ".mp3", ".ogg" }

-- ---------------------------------------------------------------------------
-- Helpers (duplicated from create_song_sections.lua rather than shared via
-- dofile() - each script in this folder is meant to be copyable/symlinkable
-- standalone into REAPER's Scripts/ directory, see reaper/README.md).
-- ---------------------------------------------------------------------------
local function get_project_dir()
  local p = reaper.GetProjectPath("")
  return (p ~= "") and p or reaper.GetResourcePath()
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

local function run_python(cmd)
  reaper.ShowConsoleMsg("midi_drums: " .. cmd .. "\n")
  local handle = io.popen('cmd /S /C "' .. cmd .. ' 2>&1"')
  local out    = handle:read("*a")
  local ok     = handle:close()
  if out and out ~= "" then
    reaper.ShowConsoleMsg(out .. "\n")
  end
  return ok, out
end

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

local function shell_escape(s)
  s = s:gsub("[\r\n]", " ")
  s = s:gsub('"', "'")
  s = s:gsub("[&|^<>%%]", "")
  return s
end

-- ---------------------------------------------------------------------------
-- Render a MIDI/VSTi item to a temp WAV via a bar-aligned time-selection
-- render. Saves and restores RENDER_FILE / RENDER_PATTERN /
-- RENDER_BOUNDSFLAG and the time selection unconditionally right after the
-- render call, before any success/failure branching - action 42230's whole
-- semantic is "use most recent settings", so skipping restore would
-- silently corrupt the user's next manual render.
-- ---------------------------------------------------------------------------
local function render_item_to_wav(render_start_time, render_end_time)
  local saved_ts_start, saved_ts_end =
    reaper.GetSet_LoopTimeRange(false, false, 0, 0, false)
  local _, saved_render_file =
    reaper.GetSetProjectInfo_String(0, "RENDER_FILE", "", false)
  local _, saved_render_pattern =
    reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", "", false)
  local saved_bounds_flag =
    reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 0, false)

  local render_dir = get_project_dir()

  reaper.GetSet_LoopTimeRange(
    true, false, render_start_time, render_end_time, false
  )
  reaper.GetSetProjectInfo_String(0, "RENDER_FILE", render_dir, true)
  reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", RENDER_PATTERN, true)
  -- 2 = "Time selection" - see the KNOWN UNVERIFIED note at the top of this
  -- file.
  reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 2, true)

  -- File: Render project, using the most recent render settings,
  -- auto-close render dialog.
  reaper.Main_OnCommand(42230, 0)

  -- Restore immediately - before any of the return paths below.
  reaper.GetSetProjectInfo_String(0, "RENDER_FILE", saved_render_file, true)
  reaper.GetSetProjectInfo_String(
    0, "RENDER_PATTERN", saved_render_pattern, true
  )
  reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", saved_bounds_flag, true)
  reaper.GetSet_LoopTimeRange(
    true, false, saved_ts_start, saved_ts_end, false
  )

  for _, ext in ipairs(RENDER_EXTENSIONS) do
    local candidate = render_dir .. "/" .. RENDER_PATTERN .. ext
    local f = io.open(candidate, "rb")
    if f then
      f:close()
      return true, candidate
    end
  end
  return false,
    "Render completed but no output file was found matching:\n"
    .. render_dir .. "/" .. RENDER_PATTERN .. ".{"
    .. table.concat(RENDER_EXTENSIONS, ","):gsub("%.", "") .. "}\n\n"
    .. "Check that the project's current render format (File > Render...) "
    .. "actually produces one of those, then rerun."
end

-- ---------------------------------------------------------------------------
-- 1. Resolve the selected riff item + its take
-- ---------------------------------------------------------------------------
local item_count = reaper.CountSelectedMediaItems(0)
if item_count == 0 then
  reaper.ShowMessageBox(
    "Select a riff media item first, then run this action.",
    "No Item Selected", 0
  )
  return
end
if item_count > 1 then
  reaper.ShowMessageBox(
    "Multiple items selected - only the first will be used.\n\n"
    .. "v1 locks kicks to ONE representative bar; multi-item riff "
    .. "transcription isn't supported yet.",
    "Using First Item", 0
  )
end

local item = reaper.GetSelectedMediaItem(0, 0)
local take = reaper.GetActiveTake(item)
if not take then
  reaper.ShowMessageBox(
    "Selected item has no active take.", "No Take", 0
  )
  return
end

local item_start  = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
local item_length = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
local item_end    = item_start + item_length

-- ---------------------------------------------------------------------------
-- 2. Bar-alignment: item start in quarter notes vs. the enclosing bar start
-- ---------------------------------------------------------------------------
local timesig_num, timesig_denom = reaper.TimeMap_GetTimeSigAtTime(0, item_start)
timesig_num   = timesig_num   or 4
timesig_denom = timesig_denom or 4
local bar_len_qn = timesig_num * (4.0 / timesig_denom)

local qn_start = reaper.TimeMap2_timeToQN(0, item_start)
local qn_end   = reaper.TimeMap2_timeToQN(0, item_end)
local bar_start_qn = math.floor(qn_start / bar_len_qn) * bar_len_qn
local bar_end_qn   = math.ceil(qn_end / bar_len_qn) * bar_len_qn

local offset_beats = qn_start - bar_start_qn

local bpm = reaper.Master_GetTempo()

-- ---------------------------------------------------------------------------
-- 3. Get the riff audio - fast path (existing audio file) or render path
-- ---------------------------------------------------------------------------
local audio_path, audio_offset, audio_duration

if not reaper.TakeIsMIDI(take) then
  local source = reaper.GetMediaItemTake_Source(take)
  audio_path = reaper.GetMediaSourceFileName(source, "")
  if not audio_path or audio_path == "" then
    reaper.ShowMessageBox(
      "Could not resolve the take's source audio file.", "No Source", 0
    )
    return
  end
  local take_startoffs = reaper.GetMediaItemTakeInfo_Value(take, "D_STARTOFFS")
  local take_playrate  = reaper.GetMediaItemTakeInfo_Value(take, "D_PLAYRATE")
  audio_offset   = take_startoffs
  audio_duration = item_length * take_playrate
else
  local render_start_time = reaper.TimeMap2_QNToTime(0, bar_start_qn)
  local render_end_time   = reaper.TimeMap2_QNToTime(0, bar_end_qn)

  reaper.Undo_BeginBlock()
  local ok, result = render_item_to_wav(render_start_time, render_end_time)
  reaper.Undo_EndBlock("Render Riff Item for midi_drums", -1)

  if not ok then
    reaper.ShowMessageBox(result, "Render Failed", 0)
    return
  end
  audio_path = result
  -- The rendered file already starts exactly at the bar line (that's the
  -- render range), so no further slicing is needed - and offset_beats
  -- above already accounts for where within that bar the item itself
  -- starts.
end

-- ---------------------------------------------------------------------------
-- 4. Prompt for generation settings
-- ---------------------------------------------------------------------------
local ok_a, csv_a = reaper.GetUserInputs(
  "Riff-Locked Drums — Style", 5,
  "Genre,Style,Drummer (blank = none),Section,Mapping,extrawidth=100",
  DEFAULT_GENRE .. "," .. DEFAULT_STYLE .. ",,"
    .. DEFAULT_SECTION .. "," .. DEFAULT_MAPPING
)
if not ok_a then return end

local genre, style, drummer, section, mapping =
  csv_a:match("^([^,]*),([^,]*),([^,]*),([^,]*),([^,]*)$")
genre   = shell_escape((genre   or DEFAULT_GENRE):match("^%s*(.-)%s*$"))
style   = shell_escape((style   or DEFAULT_STYLE):match("^%s*(.-)%s*$"))
drummer = shell_escape((drummer or ""):match("^%s*(.-)%s*$"))
section = shell_escape((section or DEFAULT_SECTION):match("^%s*(.-)%s*$"))
mapping = shell_escape((mapping or DEFAULT_MAPPING):match("^%s*(.-)%s*$"))

if genre == "" then genre = DEFAULT_GENRE end
if style == "" then style = DEFAULT_STYLE end
if section == "" then section = DEFAULT_SECTION end
if mapping == "" then mapping = DEFAULT_MAPPING end

local default_ts_str = string.format("%d/%d", timesig_num, timesig_denom)
local ok_b, csv_b = reaper.GetUserInputs(
  "Riff-Locked Drums — Timing", 4,
  "Time signature (N/D),Bars,Grid (8th/16th/32nd/8th_triplet/16th_triplet),"
    .. "Lock strength (0.0-1.0),extrawidth=100",
  default_ts_str .. "," .. DEFAULT_BARS .. "," .. DEFAULT_GRID .. ","
    .. DEFAULT_LOCK_STRENGTH
)
if not ok_b then return end

local ts_str, bars_str, grid, lock_strength_str =
  csv_b:match("^([^,]*),([^,]*),([^,]*),([^,]*)$")
ts_str = shell_escape((ts_str or default_ts_str):match("^%s*(.-)%s*$"))
if ts_str == "" then ts_str = default_ts_str end
local bars = tonumber((bars_str or ""):match("^%s*(.-)%s*$")) or tonumber(DEFAULT_BARS)
grid = shell_escape((grid or DEFAULT_GRID):match("^%s*(.-)%s*$"))
if grid == "" then grid = DEFAULT_GRID end
local lock_strength =
  tonumber((lock_strength_str or ""):match("^%s*(.-)%s*$"))
  or tonumber(DEFAULT_LOCK_STRENGTH)

-- ---------------------------------------------------------------------------
-- 5. Run the CLI
-- ---------------------------------------------------------------------------
local project_dir = get_project_dir()
local midi_out     = project_dir .. "/" .. MIDI_OUT_FILENAME
local sidecar_out  = project_dir .. "/" .. SIDECAR_OUT_FILENAME

local cmd_parts = {
  string.format(
    '"%s" -m midi_drums riff --audio "%s" --genre "%s" --style "%s"',
    PYTHON_EXE, audio_path, genre, style
  ),
  string.format('--tempo %g --offset-beats %g', bpm, offset_beats),
  string.format(
    '--section "%s" --time-signature "%s" --bars %d --grid "%s"',
    section, ts_str, bars, grid
  ),
  string.format(
    '--lock-strength %g --humanization %g --complexity %g',
    lock_strength, DEFAULT_HUMANIZATION, DEFAULT_COMPLEXITY
  ),
  string.format(
    '--mapping "%s" --output "%s" --write-sidecar "%s"',
    mapping, midi_out, sidecar_out
  ),
}
if drummer ~= "" then
  cmd_parts[#cmd_parts + 1] = string.format('--drummer "%s"', drummer)
end
if audio_offset then
  cmd_parts[#cmd_parts + 1] = string.format(
    '--audio-offset %g --audio-duration %g', audio_offset, audio_duration
  )
end
local cmd = table.concat(cmd_parts, " ")

local py_out = run_python_or_fail(
  cmd,
  "Common causes:\n"
  .. "  • Audio dependencies not installed (uv sync --group audio)\n"
  .. "  • PYTHON_EXE path incorrect: " .. PYTHON_EXE
)
if not py_out then return end

-- ---------------------------------------------------------------------------
-- 6. Read back the sidecar, create a region, import the MIDI
-- ---------------------------------------------------------------------------
local sidecar_content = read_generated_file_or_fail(sidecar_out, "sidecar")
if not sidecar_content then return end

local s_tempo, s_num, s_denom, s_sections, s_err = parse_sidecar(sidecar_content)
if not s_sections then
  reaper.ShowMessageBox(
    "Could not parse riff sidecar: " .. (s_err or "?"), "Error", 0
  )
  return
end

if not read_generated_file_or_fail(midi_out, "MIDI file") then return end

reaper.Undo_BeginBlock()

local region_start = reaper.TimeMap2_QNToTime(0, bar_start_qn)
local measure_length = (60.0 / (s_tempo or bpm)) * s_num * (4.0 / s_denom)
local region_end = region_start + ((s_sections[1].bars) * measure_length)
reaper.AddProjectMarker2(
  0, true, region_start, region_end, s_sections[1].name, -1, 0
)

-- InsertMedia places at the edit cursor - move it to the bar-aligned start
-- so the generated pattern lines up with the riff, then restore it.
local saved_cursor = reaper.GetCursorPosition()
reaper.SetEditCurPos(region_start, false, false)
reaper.InsertMedia(midi_out, 0)
reaper.SetEditCurPos(saved_cursor, false, false)

reaper.Undo_EndBlock("Create Riff-Locked Drums", -1)
reaper.UpdateArrange()

reaper.ShowMessageBox(
  "Done!\nMIDI imported: " .. midi_out
    .. "\nRegion: " .. s_sections[1].name,
  "Riff-Locked Drums Ready", 0
)
