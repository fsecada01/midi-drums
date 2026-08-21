-- reaper/midi_drums/riff_lock.lua

-- Small helpers duplicated from sections.lua rather than shared via a
-- common util module — see the plan's pre-ruling: neither module is a
-- standalone script any more, but the spec's file table lists exactly
-- sections.lua and riff_lock.lua, so a third shared-util module would be
-- undocumented scope creep. Each duplicated helper is ~5-15 lines.
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

function M.parse_sidecar(content)
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

-- Computes how far the selected item's start sits from its enclosing
-- bar line, in quarter notes, plus the bar's own bounds and the
-- tempo/time-sig in effect there. A riff that doesn't start on a bar
-- line would otherwise get its accents locked to a phase-shifted
-- reading of the riff — this is the correction for that.
function M.compute_bar_alignment(item)
  local item_start = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
  local item_qn = reaper.TimeMap2_timeToQN(0, item_start)

  local ts_num, ts_denom, bpm = reaper.TimeMap_GetTimeSigAtTime(0, item_start)
  if not ts_num or ts_num == 0 then
    ts_num, ts_denom = 4, 4
  end
  if not bpm or bpm == 0 then
    bpm = reaper.Master_GetTempo()
  end

  local qn_per_bar = ts_num * (4.0 / ts_denom)
  local bar_index = math.floor(item_qn / qn_per_bar + 1e-9)
  local bar_start_qn = bar_index * qn_per_bar
  local bar_end_qn = bar_start_qn + qn_per_bar
  local offset_beats = item_qn - bar_start_qn

  return offset_beats, bar_start_qn, bar_end_qn, ts_num, ts_denom, bpm
end

-- Renders the given time range (in project time, already expanded to
-- bar lines by the caller) to a temp WAV via "render using most recent
-- settings, auto-close" (42230). RENDER_FILE/RENDER_PATTERN/
-- RENDER_BOUNDSFLAG and the time selection are saved and restored on
-- every exit path, since 42230's whole semantic is "reuse whatever the
-- user last configured manually" — skipping save/restore would silently
-- corrupt their next manual render.
--
-- KNOWN UNVERIFIED: RENDER_BOUNDSFLAG=2 (time selection) is carried
-- over from the plan as the intended value; confirm empirically against
-- a real REAPER install as part of the manual verification pass.
function M.render_item_to_wav(render_start_time, render_end_time)
  local proj = 0

  local _, old_file = reaper.GetSetProjectInfo_String(proj, "RENDER_FILE", "", false)
  local _, old_pattern = reaper.GetSetProjectInfo_String(proj, "RENDER_PATTERN", "", false)
  local old_bounds = reaper.GetSetProjectInfo(proj, "RENDER_BOUNDSFLAG", 0, false)
  local old_ts_start, old_ts_end = reaper.GetSet_LoopTimeRange(false, false, 0, 0, false)

  local out_dir = M.get_project_dir()
  local out_pattern = "midi_drums_riff_render"

  reaper.Undo_BeginBlock()

  local ok = pcall(function()
    reaper.GetSetProjectInfo_String(proj, "RENDER_FILE", out_dir, true)
    reaper.GetSetProjectInfo_String(proj, "RENDER_PATTERN", out_pattern, true)
    reaper.GetSetProjectInfo(proj, "RENDER_BOUNDSFLAG", 2, true)
    reaper.GetSet_LoopTimeRange(true, false, render_start_time, render_end_time, false)

    reaper.Main_OnCommand(42230, 0) -- render using most recent settings, auto-close
  end)

  reaper.GetSetProjectInfo_String(proj, "RENDER_FILE", old_file or "", true)
  reaper.GetSetProjectInfo_String(proj, "RENDER_PATTERN", old_pattern or "", true)
  reaper.GetSetProjectInfo(proj, "RENDER_BOUNDSFLAG", old_bounds or 0, true)
  reaper.GetSet_LoopTimeRange(true, false, old_ts_start, old_ts_end, false)

  reaper.Undo_EndBlock("Render Riff Item to WAV", -1)

  if not ok then
    return false, "Render failed (see REAPER console)."
  end

  local wav_path = out_dir .. "/" .. out_pattern .. ".wav"
  local f = io.open(wav_path, "rb")
  if not f then
    return false, "Render did not produce the expected file: " .. wav_path
  end
  f:close()

  return true, wav_path
end

-- Resolves audio for the selected item/take: an audio take reads its
-- own source file directly (fast path, no project mutation); a MIDI/
-- VSTi take is rendered to a temp WAV via a bar-aligned time selection.
function M.resolve_audio_source(item, take, bar_start_qn, bar_end_qn)
  if not take then
    return nil, nil, nil, "Selected item has no active take."
  end

  if not reaper.TakeIsMIDI(take) then
    local source = reaper.GetMediaItemTake_Source(take)
    if not source then
      return nil, nil, nil, "Could not read the take's audio source."
    end
    local audio_path = reaper.GetMediaSourceFileName(source, "")
    if audio_path == "" then
      return nil, nil, nil, "Audio take has no source file on disk."
    end

    local item_start = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
    local item_len = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
    local take_offset = reaper.GetMediaItemTakeInfo_Value(take, "D_STARTOFFS")

    return audio_path, take_offset, item_len, nil
  end

  -- MIDI/VSTi take: render the bar-aligned range to a temp WAV.
  local bar_start_time = reaper.TimeMap2_QNToTime(0, bar_start_qn)
  local bar_end_time = reaper.TimeMap2_QNToTime(0, bar_end_qn)

  local ok, result = M.render_item_to_wav(bar_start_time, bar_end_time)
  if not ok then
    return nil, nil, nil, result
  end

  return result, 0.0, (bar_end_time - bar_start_time), nil
end

function M.build_cmd(python_exe, p)
  local snare_flag = ""
  if p.snare_mode == "stab" then
    snare_flag = string.format(
      ' --snare-mode stab --snare-stab-threshold %g', p.snare_threshold
    )
  elseif p.snare_mode == "reinforce" then
    snare_flag = ' --snare-mode reinforce'
  else
    snare_flag = ' --snare-mode off'
  end

  local offset_flag = ""
  if p.offset_beats and p.offset_beats ~= 0 then
    offset_flag = string.format(' --offset-beats %g', p.offset_beats)
  end

  local audio_offset_flag = ""
  if p.audio_offset and p.audio_offset ~= 0 then
    audio_offset_flag = string.format(' --audio-offset %g', p.audio_offset)
  end
  local audio_duration_flag = ""
  if p.audio_duration then
    audio_duration_flag = string.format(' --audio-duration %g', p.audio_duration)
  end

  return string.format(
    '"%s" -m midi_drums riff --audio "%s" --genre "%s" --style "%s"'
    .. ' --tempo %g --section "%s" --time-signature "%d/%d" --bars %d'
    .. ' --grid "%s" --lock-strength %g --mapping "%s"'
    .. ' --output "%s" --write-sidecar "%s"%s%s%s%s',
    python_exe, p.audio_path, M.shell_escape(p.genre), M.shell_escape(p.style),
    p.bpm, M.shell_escape(p.section), p.ts_num, p.ts_denom, p.bars,
    M.shell_escape(p.grid), p.lock_strength, M.shell_escape(p.mapping),
    p.midi_out, p.sidecar_path, snare_flag, offset_flag,
    audio_offset_flag, audio_duration_flag
  )
end

-- Project mutation — only call from an on_complete callback. Reads
-- back the sidecar + rendered MIDI, creates a region for the section,
-- and imports the MIDI.
function M.on_job_complete(p)
  local f = io.open(p.sidecar_path, "rb")
  if not f then
    reaper.ShowMessageBox(
      "Riff-Lock Beat generation finished, but the sidecar file was not found:\n"
        .. p.sidecar_path,
      "midi_drums", 0
    )
    return
  end
  local content = f:read("*a")
  f:close()

  local tempo, ts_num, ts_denom, sections, err = M.parse_sidecar(content)
  if not tempo then
    reaper.ShowMessageBox(
      "Riff-Lock Beat generation finished, but the sidecar could not be parsed:\n"
        .. (err or "unknown error"),
      "midi_drums", 0
    )
    return
  end

  reaper.Undo_BeginBlock()

  local measure_length = (60.0 / tempo) * ts_num * (4.0 / ts_denom)
  local current_time = p.region_start_time or 0.0
  for _, s in ipairs(sections) do
    local region_end = current_time + (s.bars * measure_length)
    reaper.AddProjectMarker2(0, true, current_time, region_end, s.name, -1, 0)
    current_time = region_end
  end

  reaper.InsertMedia(p.midi_out, 0)

  reaper.Undo_EndBlock("Create Riff-Lock Beat", -1)
  reaper.UpdateArrange()
end

return M
