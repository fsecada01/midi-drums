-- reaper/midi_drums/additive_rhythm.lua
-- Business logic for the panel's Additive Rhythm tab (experimental
-- spike - see claudedocs/design_additive_rhythm_grouping.md). Small
-- helpers duplicated from sections.lua/riff_lock.lua rather than shared
-- via a common util module, matching riff_lock.lua's own precedent for
-- why a third shared-util module isn't worth it here.
local M = {}

function M.get_project_dir()
  local p = reaper.GetProjectPath("")
  return (p ~= "") and p or reaper.GetResourcePath()
end

function M.shell_escape(s)
  s = s:gsub("[\r\n]", " ")
  s = s:gsub('"', "'")
  s = s:gsub("[&|^<>%%]", "")
  return s
end

function M.build_cmd(python_exe, p)
  local drummer_flag = ""
  if p.drummer and p.drummer ~= "" then
    drummer_flag = string.format(' --drummer "%s"', M.shell_escape(p.drummer))
    if p.drummer_intensity then
      drummer_flag = drummer_flag
        .. string.format(' --drummer-intensity %g', p.drummer_intensity)
    end
  end

  return string.format(
    '"%s" -m midi_drums additive-rhythm "%s" --grid %d --tempo %g'
    .. ' --output "%s" --write-timeline "%s"%s',
    python_exe, M.shell_escape(p.grouping), p.grid, p.tempo,
    p.midi_out, p.timeline_path, drummer_flag
  )
end

-- Parses the flat {tempo, bars: [{start_time, num, denom}, ...]} JSON
-- written by `additive-rhythm --write-timeline` (cli.py). Deliberately
-- its own parser rather than reusing sections.parse_timeline: that one
-- requires a non-empty "regions" array (song-map mode always has at
-- least one), which additive-rhythm bars have no equivalent of - see
-- the design doc's Non-goals ("Song"/"Section"/region support).
function M.parse_timeline(content)
  local tempo = tonumber(content:match('"tempo"%s*:%s*([%-%d%.]+)'))
  if not tempo then
    return nil, nil, "Could not parse 'tempo'."
  end

  local bars = {}
  for start_time, num, denom in content:gmatch(
    '"start_time"%s*:%s*([%-%d%.]+)%s*,%s*"num"%s*:%s*(%d+)%s*,'
    .. '%s*"denom"%s*:%s*(%d+)'
  ) do
    bars[#bars + 1] = {
      start_time = tonumber(start_time), num = tonumber(num), denom = tonumber(denom),
    }
  end
  if #bars == 0 then
    return nil, nil, "No bars found in timeline."
  end

  return tempo, bars
end

-- Project mutation - only call from an on_complete callback. Places one
-- SetTempoTimeSigMarker per resolved bar starting at project time 0.0,
-- matching sections.create_regions_from_sections's own start-at-zero
-- convention for the REAPER-mode Song Sections tab.
function M.apply_timeline_to_reaper(tempo, bars)
  reaper.Undo_BeginBlock()
  for _, bar in ipairs(bars) do
    reaper.SetTempoTimeSigMarker(0, -1, bar.start_time, -1, -1, tempo, bar.num, bar.denom, false)
  end
  reaper.Undo_EndBlock("Create Additive Rhythm Meter Markers", -1)
  reaper.UpdateArrange()
end

-- Project mutation - only call from an on_complete callback. Reads back
-- the timeline JSON, places per-bar tempo/time-signature markers, and
-- imports the rendered MIDI.
function M.on_job_complete(p)
  local f = io.open(p.timeline_path, "rb")
  if not f then
    reaper.ShowMessageBox(
      "Additive Rhythm generation finished, but the timeline file was "
        .. "not found:\n" .. p.timeline_path,
      "midi_drums", 0
    )
    return
  end
  local content = f:read("*a")
  f:close()

  local tempo, bars, err = M.parse_timeline(content)
  if not tempo then
    reaper.ShowMessageBox(
      "Additive Rhythm generation finished, but the timeline could not "
        .. "be parsed:\n" .. (err or "unknown error"),
      "midi_drums", 0
    )
    return
  end

  M.apply_timeline_to_reaper(tempo, bars)
  reaper.InsertMedia(p.midi_out, 0)
  reaper.UpdateArrange()
end

return M
