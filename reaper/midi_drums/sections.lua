-- reaper/midi_drums/sections.lua
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

function M.sections_to_json(sections, tempo, num, denom)
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

function M.parse_timeline(content)
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

function M.build_template_cmd(python_exe, genre, style, mapping, sidecar_path, midi_out)
  return string.format(
    '"%s" -m midi_drums generate --genre "%s" --style "%s" --mapping "%s"'
    .. ' --sidecar "%s" --output "%s"',
    python_exe, M.shell_escape(genre), M.shell_escape(style),
    M.shell_escape(mapping), sidecar_path, midi_out
  )
end

function M.build_ai_cmd(python_exe, description, tempo_str, midi_out, sidecar_path)
  local tempo_arg = ""
  if tempo_str and tempo_str ~= "" and tonumber(tempo_str) then
    tempo_arg = "--tempo " .. tempo_str
  end
  return string.format(
    '"%s" -m midi_drums prompt "%s" --song %s --output "%s" --write-sidecar "%s"',
    python_exe, M.shell_escape(description), tempo_arg, midi_out, sidecar_path
  )
end

function M.build_songmap_cmd(python_exe, genre, style, mapping, map_path, timeline_path, midi_out)
  return string.format(
    '"%s" -m midi_drums generate --genre "%s" --style "%s" --mapping "%s"'
    .. ' --song-map "%s" --write-timeline "%s" --output "%s"',
    python_exe, M.shell_escape(genre), M.shell_escape(style),
    M.shell_escape(mapping), map_path, timeline_path, midi_out
  )
end

-- Project mutation — only call from an on_complete callback (or
-- REAPER-mode's direct path, which needs no subprocess to begin
-- with). REAPER's tempo is always quarter-note-based regardless of
-- time signature, so a bar's length in quarter notes is
-- ts_num * (4 / ts_denom) — e.g. a 6/8 bar is 3 quarter notes long.
function M.create_regions_from_sections(sections, bpm, ts_num, ts_denom)
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

-- Project mutation — song-map mode's equivalent of the above; places
-- one tempo/time-sig marker per resolved change point and one colored
-- region per song-map region, since a song map can vary tempo/meter
-- per bar (mirrors song_reaper_build.lua's B.apply_to_reaper).
function M.apply_timeline_to_reaper(tempo_points, regions, color_groups)
  reaper.Undo_BeginBlock()
  for _, tp in ipairs(tempo_points) do
    reaper.SetTempoTimeSigMarker(0, -1, tp.time, -1, -1, tp.bpm, tp.num, tp.denom, false)
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

function M.import_midi(midi_path)
  reaper.InsertMedia(midi_path, 0)
  reaper.UpdateArrange()
end

return M
