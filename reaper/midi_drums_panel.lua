-- reaper/midi_drums_panel.lua
-- MIDI Drums: unified panel. Replaces create_song_sections.lua,
-- create_beat_from_riff.lua, and midi_drums_help.lua with one dockable
-- ReaImGui window (Song Sections / Riff-Lock Beat / Settings / Log).

-- Keep this string in sync with reaper/README.md's "Prerequisites"
-- section — both describe the same ReaPack install steps.
local REAIMGUI_INSTALL_STEPS =
  "This panel requires ReaImGui, which is not installed.\n\n"
  .. "To install it:\n"
  .. "1. Extensions > ReaPack > Browse packages...\n"
  .. "2. Search for \"ReaImGui\"\n"
  .. "3. Right-click \"ReaImGui: ReaScript binding for Dear ImGui\" > Install\n"
  .. "4. Apply, then restart REAPER.\n\n"
  .. "See reaper/README.md for full setup instructions."

if not reaper.APIExists("ImGui_CreateContext") then
  reaper.ShowMessageBox(REAIMGUI_INSTALL_STEPS, "ReaImGui Required", 0)
  return
end

local script_path = ({ reaper.get_action_context() })[2]:match("^(.*[/\\])")
package.path = package.path .. ";" .. script_path .. "midi_drums/?.lua"

local settings = dofile(script_path .. "midi_drums/settings.lua")
local job_runner = dofile(script_path .. "midi_drums/job_runner.lua")
local sections = dofile(script_path .. "midi_drums/sections.lua")
local riff_lock = dofile(script_path .. "midi_drums/riff_lock.lua")

local ctx = reaper.ImGui_CreateContext("midi_drums Panel")

local font_sans = reaper.ImGui_CreateFont("Segoe UI", 14)
local font_mono = reaper.ImGui_CreateFont("Consolas", 13)
if font_sans then reaper.ImGui_Attach(ctx, font_sans) end
if font_mono then reaper.ImGui_Attach(ctx, font_mono) end

local help_popover_open = {}

-- Renders a "?" button that opens a popover of {title, body} entries
-- when clicked. `id` must be unique per call site (used as the ImGui ID
-- and the popup name).
local function draw_help_button(id, lines)
  reaper.ImGui_SameLine(ctx)
  reaper.ImGui_TextColored(ctx, 0xa78bfaff, "(?)")
  if reaper.ImGui_IsItemClicked(ctx) then
    reaper.ImGui_OpenPopup(ctx, "help_popup_" .. id)
  end
  if reaper.ImGui_BeginPopup(ctx, "help_popup_" .. id) then
    for _, entry in ipairs(lines) do
      reaper.ImGui_TextColored(ctx, 0xa78bfaff, entry.title)
      reaper.ImGui_TextWrapped(ctx, entry.body)
      reaper.ImGui_Separator(ctx)
    end
    reaper.ImGui_EndPopup(ctx)
  end
end

-- ===== Song Sections tab state =====
local ss_mode = 1 -- 1=REAPER, 2=Sidecar, 3=AI, 4=Song Map
local ss_genre = settings.get("default_genre")
local ss_style = settings.get("default_style")
local ss_mapping = settings.get("default_mapping")
local ss_drummer = ""
local ss_tempo = "120"
local ss_ts_num, ss_ts_denom = reaper.GetProjectTimeSignature2(0)
local ss_ai_description = ""
local ss_ai_tempo = settings.get("default_ai_tempo")
local ss_status = ""

local SS_MODE_HELP = {
  { title = "REAPER", body = "Use REAPER's own section structure below. "
    .. "Regions are created directly and a matching drum pattern is "
    .. "generated in the background." },
  { title = "Sidecar", body = "Read an existing midi_drums_sections.json "
    .. "sidecar file (e.g. written by a prior run) and create regions "
    .. "to match it. No subprocess is launched." },
  { title = "AI", body = "Describe the song in plain text; an AI agent "
    .. "chooses the section structure and writes a matching sidecar "
    .. "and MIDI file." },
  { title = "Song Map", body = "Read a song-map JSON file with per-segment "
    .. "tempo/meter changes and build a tempo-aware timeline in REAPER." },
}

-- ===== Riff-Lock Beat tab state =====
local rl_genre = settings.get("default_genre")
local rl_style = settings.get("default_style")
local rl_drummer = ""
local rl_section = "verse"
local rl_mapping = settings.get("default_mapping")
local rl_grid = "16th"
local rl_lock_strength = 1.0
local rl_snare_mode = 1 -- 1=Off, 2=Reinforce, 3=Stab
local rl_snare_threshold = 0.85
local rl_status = ""

local RL_SNARE_HELP = {
  { title = "Off", body = "Snare is untouched by the riff — comes purely "
    .. "from the genre plugin/drummer style." },
  { title = "Reinforce", body = "Boosts velocity on existing snare hits "
    .. "that land near a strong riff accent." },
  { title = "Stab", body = "Inserts a unison snare hit at very strong "
    .. "accents where a kick was locked but no snare is nearby. "
    .. "Threshold below controls how strong an accent must be." },
}

local function sidecar_path()
  local override = settings.get("sidecar_path_override")
  if override ~= "" then
    return override
  end
  return sections.get_project_dir() .. "/midi_drums_sections.json"
end

local function midi_out_path(name)
  return sections.get_project_dir() .. "/" .. name
end

local function draw_song_sections_tab()
  reaper.ImGui_Text(ctx, "Mode:")
  if reaper.ImGui_RadioButton(ctx, "REAPER", ss_mode == 1) then ss_mode = 1 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Sidecar", ss_mode == 2) then ss_mode = 2 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "AI", ss_mode == 3) then ss_mode = 3 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Song Map", ss_mode == 4) then ss_mode = 4 end
  draw_help_button("ss_mode", SS_MODE_HELP)

  reaper.ImGui_Separator(ctx)

  if ss_mode == 3 then
    local changed
    changed, ss_ai_description = reaper.ImGui_InputTextMultiline(
      ctx, "Description", ss_ai_description, -1, 80
    )
    changed, ss_ai_tempo = reaper.ImGui_InputText(ctx, "Tempo (BPM)", ss_ai_tempo)
  else
    local changed
    changed, ss_genre = reaper.ImGui_InputText(ctx, "Genre", ss_genre)
    changed, ss_style = reaper.ImGui_InputText(ctx, "Style", ss_style)
    changed, ss_drummer = reaper.ImGui_InputText(ctx, "Drummer (optional)", ss_drummer)
    changed, ss_mapping = reaper.ImGui_InputText(ctx, "Mapping", ss_mapping)
  end

  reaper.ImGui_Separator(ctx)

  local disabled = job_runner.is_running()
  if disabled then reaper.ImGui_BeginDisabled(ctx) end
  if reaper.ImGui_Button(ctx, "Generate") then
    local python_exe = settings.resolve_python_exe()
    if not python_exe then
      ss_status = "Cancelled: no Python interpreter configured."
    else
      local sc_path = sidecar_path()
      local midi_out = midi_out_path("midi_drums_song.mid")

      if ss_mode == 1 then
        local default_sections = {
          { name = "Intro", bars = 8 },
          { name = "Verse", bars = 16 },
          { name = "Chorus", bars = 16 },
          { name = "Bridge", bars = 8 },
          { name = "Outro", bars = 4 },
        }
        local bpm = reaper.Master_GetTempo()
        sections.create_regions_from_sections(default_sections, bpm, ss_ts_num, ss_ts_denom)

        local json = sections.sections_to_json(default_sections, bpm, ss_ts_num, ss_ts_denom)
        local f = io.open(sc_path, "w")
        if f then f:write(json); f:close() end

        local cmd = sections.build_template_cmd(python_exe, ss_genre, ss_style, ss_mapping, sc_path, midi_out)
        job_runner.start(cmd, "Song Sections (REAPER)", function()
          sections.import_midi(midi_out)
          ss_status = "Done."
        end)
        ss_status = "Running..."
      elseif ss_mode == 2 then
        local f = io.open(sc_path, "rb")
        if not f then
          ss_status = "Sidecar not found: " .. sc_path
        else
          local content = f:read("*a")
          f:close()
          local tempo, ts_num, ts_denom, secs, err = sections.parse_sidecar(content)
          if not tempo then
            ss_status = "Sidecar parse error: " .. (err or "unknown")
          else
            sections.create_regions_from_sections(secs, tempo, ts_num, ts_denom)
            ss_status = "Regions created from sidecar."
          end
        end
      elseif ss_mode == 3 then
        local cmd = sections.build_ai_cmd(python_exe, ss_ai_description, ss_ai_tempo, midi_out, sc_path)
        job_runner.start(cmd, "Song Sections (AI)", function()
          local f = io.open(sc_path, "rb")
          if f then
            local content = f:read("*a")
            f:close()
            local tempo, ts_num, ts_denom, secs = sections.parse_sidecar(content)
            if tempo then
              sections.create_regions_from_sections(secs, tempo, ts_num, ts_denom)
            end
          end
          sections.import_midi(midi_out)
          ss_status = "Done."
        end)
        ss_status = "Running (this can take 20-45s)..."
      elseif ss_mode == 4 then
        local map_path = sections.get_project_dir() .. "/midi_drums_song_map.json"
        local timeline_path = sections.get_project_dir() .. "/midi_drums_timeline.json"
        local cmd = sections.build_songmap_cmd(python_exe, ss_genre, ss_style, ss_mapping, map_path, timeline_path, midi_out)
        job_runner.start(cmd, "Song Sections (Song Map)", function()
          local f = io.open(timeline_path, "rb")
          if f then
            local content = f:read("*a")
            f:close()
            local tempo_points, regions, color_groups = sections.parse_timeline(content)
            if tempo_points then
              sections.apply_timeline_to_reaper(tempo_points, regions, color_groups)
            end
          end
          sections.import_midi(midi_out)
          ss_status = "Done."
        end)
        ss_status = "Running..."
      end
    end
  end
  if disabled then reaper.ImGui_EndDisabled(ctx) end

  reaper.ImGui_TextWrapped(ctx, ss_status)
  if job_runner.is_running() then
    reaper.ImGui_TextWrapped(ctx, job_runner.state.job_label .. " - " .. job_runner.state.status)
  end
end

local function draw_riff_lock_tab()
  -- Read selection fresh every frame: unlike the retired per-run
  -- script, this panel persists across generations, so item selection
  -- must be read at Generate-click time, not panel-open time.
  local item_count = reaper.CountSelectedMediaItems(0)

  if item_count == 0 then
    reaper.ImGui_TextColored(ctx, 0xfb7185ff, "Select a riff media item first.")
  else
    reaper.ImGui_TextWrapped(ctx, item_count .. " item(s) selected (first will be used).")
  end

  reaper.ImGui_Separator(ctx)

  local changed
  changed, rl_genre = reaper.ImGui_InputText(ctx, "Genre", rl_genre)
  changed, rl_style = reaper.ImGui_InputText(ctx, "Style", rl_style)
  changed, rl_drummer = reaper.ImGui_InputText(ctx, "Drummer (optional)", rl_drummer)
  changed, rl_section = reaper.ImGui_InputText(ctx, "Section", rl_section)
  changed, rl_mapping = reaper.ImGui_InputText(ctx, "Mapping", rl_mapping)
  changed, rl_grid = reaper.ImGui_InputText(ctx, "Grid", rl_grid)

  changed, rl_lock_strength = reaper.ImGui_SliderDouble(ctx, "Lock Strength", rl_lock_strength, 0.0, 1.0)

  reaper.ImGui_Text(ctx, "Snare Reaction:")
  if reaper.ImGui_RadioButton(ctx, "Off", rl_snare_mode == 1) then rl_snare_mode = 1 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Reinforce", rl_snare_mode == 2) then rl_snare_mode = 2 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Stab", rl_snare_mode == 3) then rl_snare_mode = 3 end
  draw_help_button("rl_snare", RL_SNARE_HELP)

  if rl_snare_mode == 3 then
    changed, rl_snare_threshold = reaper.ImGui_SliderDouble(ctx, "Stab Threshold", rl_snare_threshold, 0.0, 1.0)
  end

  reaper.ImGui_Separator(ctx)

  local disabled = job_runner.is_running() or item_count == 0
  if disabled then reaper.ImGui_BeginDisabled(ctx) end
  if reaper.ImGui_Button(ctx, "Generate") then
    local python_exe = settings.resolve_python_exe()
    if not python_exe then
      rl_status = "Cancelled: no Python interpreter configured."
    else
      local item = reaper.GetSelectedMediaItem(0, 0)
      local take = reaper.GetActiveTake(item)

      local offset_beats, bar_start_qn, bar_end_qn, ts_num, ts_denom, bpm =
        riff_lock.compute_bar_alignment(item)

      local audio_path, audio_offset, audio_duration, err =
        riff_lock.resolve_audio_source(item, take, bar_start_qn, bar_end_qn)

      if not audio_path then
        reaper.ShowMessageBox(err or "Could not resolve riff audio.", "midi_drums", 0)
        rl_status = "Error: " .. (err or "could not resolve riff audio")
      else
        local snare_mode_str = "off"
        if rl_snare_mode == 2 then snare_mode_str = "reinforce"
        elseif rl_snare_mode == 3 then snare_mode_str = "stab" end

        local sc_path = sidecar_path()
        local midi_out = midi_out_path("midi_drums_riff.mid")
        local region_start_time = reaper.TimeMap2_QNToTime(0, bar_start_qn)

        local cmd = riff_lock.build_cmd(python_exe, {
          audio_path = audio_path,
          audio_offset = audio_offset,
          audio_duration = audio_duration,
          genre = rl_genre,
          style = rl_style,
          drummer = rl_drummer,
          bpm = bpm,
          section = rl_section,
          ts_num = ts_num,
          ts_denom = ts_denom,
          bars = 4,
          grid = rl_grid,
          lock_strength = rl_lock_strength,
          mapping = rl_mapping,
          snare_mode = snare_mode_str,
          snare_threshold = rl_snare_threshold,
          offset_beats = offset_beats,
          midi_out = midi_out,
          sidecar_path = sc_path,
        })

        job_runner.start(cmd, "Riff-Lock Beat", function()
          riff_lock.on_job_complete({
            sidecar_path = sc_path,
            midi_out = midi_out,
            region_start_time = region_start_time,
          })
          rl_status = "Done."
        end)
        rl_status = "Running..."
      end
    end
  end
  if disabled then reaper.ImGui_EndDisabled(ctx) end

  reaper.ImGui_TextWrapped(ctx, rl_status)
end

local function draw_settings_tab()
  -- Task 8 fills this in
end

local function draw_log_tab()
  -- Task 8 fills this in
end

local function loop()
  job_runner.poll()

  reaper.ImGui_SetNextWindowSize(ctx, 640, 520, reaper.ImGui_Cond_FirstUseEver())
  local visible, open = reaper.ImGui_Begin(ctx, "MIDI Drums", true)
  if visible then
    if font_sans then reaper.ImGui_PushFont(ctx, font_sans) end

    if reaper.ImGui_BeginTabBar(ctx, "midi_drums_tabs") then
      if reaper.ImGui_BeginTabItem(ctx, "Song Sections") then
        draw_song_sections_tab()
        reaper.ImGui_EndTabItem(ctx)
      end
      if reaper.ImGui_BeginTabItem(ctx, "Riff-Lock Beat") then
        draw_riff_lock_tab()
        reaper.ImGui_EndTabItem(ctx)
      end
      if reaper.ImGui_BeginTabItem(ctx, "Settings") then
        draw_settings_tab()
        reaper.ImGui_EndTabItem(ctx)
      end
      local log_tab_label = job_runner.is_running() and "Log *" or "Log"
      if reaper.ImGui_BeginTabItem(ctx, log_tab_label) then
        draw_log_tab()
        reaper.ImGui_EndTabItem(ctx)
      end
      reaper.ImGui_EndTabBar(ctx)
    end

    if font_sans then reaper.ImGui_PopFont(ctx) end
  end
  reaper.ImGui_End(ctx)

  if open then
    reaper.defer(loop)
  else
    reaper.ImGui_DestroyContext(ctx)
  end
end

reaper.defer(loop)
