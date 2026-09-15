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
local additive_rhythm = dofile(script_path .. "midi_drums/additive_rhythm.lua")
local options = dofile(script_path .. "midi_drums/options.lua")
local step_editor = dofile(script_path .. "midi_drums/step_editor.lua")

local ctx = reaper.ImGui_CreateContext("midi_drums Panel")

local FONT_SANS_SIZE = 14
local FONT_MONO_SIZE = 13
local font_sans = reaper.ImGui_CreateFont("Segoe UI", FONT_SANS_SIZE)
local font_mono = reaper.ImGui_CreateFont("Consolas", FONT_MONO_SIZE)
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

-- Generic string-preserving combo box (BeginCombo/Selectable) rather
-- than the classic index-based ImGui_Combo - every backing state var
-- here is a persisted string (from settings.get() or a plain local),
-- and a string-preserving combo avoids index/string desync when the
-- underlying option list changes out from under a stale index (e.g.
-- after a Refresh Options click). `empty_label`, when given, adds a
-- leading entry that displays as that label but stores/matches "" -
-- used for the optional Drummer field.
local function combo_from_list(label, current_value, items, empty_label)
  local changed = false
  local new_value = current_value
  local preview = current_value
  if preview == "" and empty_label then
    preview = empty_label
  end
  if reaper.ImGui_BeginCombo(ctx, label, preview) then
    if empty_label then
      local is_selected = (current_value == "")
      if reaper.ImGui_Selectable(ctx, empty_label, is_selected) then
        new_value = ""
        changed = true
      end
      if is_selected then reaper.ImGui_SetItemDefaultFocus(ctx) end
    end
    for _, item in ipairs(items) do
      local is_selected = (item == current_value)
      if reaper.ImGui_Selectable(ctx, item, is_selected) then
        new_value = item
        changed = true
      end
      if is_selected then reaper.ImGui_SetItemDefaultFocus(ctx) end
    end
    reaper.ImGui_EndCombo(ctx)
  end
  return changed, new_value
end

local GRID_VALUES = { "8th", "16th", "32nd", "8th_triplet", "16th_triplet" }

-- Non-prompting python_exe lookup for the silent startup refresh below -
-- unlike settings.resolve_python_exe(), this never opens the picker
-- dialog; an unset/stale path just means the options cache stays empty
-- until the user configures it and clicks Refresh Options.
local function cached_python_exe()
  local exe = settings.get("python_exe")
  if exe == "" then return nil end
  local f = io.open(exe, "rb")
  if not f then return nil end
  f:close()
  return exe
end

local function refresh_options()
  if job_runner.is_running() then return end
  local python_exe = cached_python_exe()
  if not python_exe then return end

  local cmd = options.build_cmd(python_exe)
  job_runner.start(cmd, "Load Options", function()
    local content = table.concat(job_runner.state.log_lines, "\n")
    local parsed, err = options.parse(content)
    if parsed then
      options.cache.genres = parsed.genres
      options.cache.drummers = parsed.drummers
      options.cache.mappings = parsed.mappings
      options.cache.genre_styles = parsed.genre_styles
      options.cache.loaded = true
      options.cache.error = nil
    else
      options.cache.error = err or "Could not parse options JSON."
    end
  end)
end

-- Forward-declared so refresh_kit_map's on_complete closure (defined
-- first, below) can call it once a lazily-fetched kit-map finishes
-- loading - see the Step Editor tab state block for the assignment.
local se_try_load_pattern

-- Lazily fetches `list kit-map --mapping <mapping>` into
-- options.cache.kit_maps, same shape as refresh_options() but scoped to
-- one mapping at a time (see options.lua's own header comment on why
-- kit-maps are cached lazily per-mapping rather than eagerly like
-- genres/drummers/mappings). Resumes a pending Step Editor load once the
-- fetch completes, so "Load Selected Item" only needs one click even
-- when the mapping's kit-map isn't cached yet.
local function refresh_kit_map(mapping)
  if job_runner.is_running() then return end
  local python_exe = cached_python_exe()
  if not python_exe then return end

  local cmd = options.build_kit_map_cmd(python_exe, mapping)
  job_runner.start(cmd, "Load Kit Map", function()
    local content = table.concat(job_runner.state.log_lines, "\n")
    local parsed, err = options.parse_kit_map(content)
    if parsed then
      options.cache.kit_maps[mapping] = { notes = parsed.notes, loaded = true, error = nil }
    else
      options.cache.kit_maps[mapping] =
        { notes = {}, loaded = false, error = err or "Could not parse kit-map JSON." }
    end
    if se_try_load_pattern then se_try_load_pattern() end
  end)
end

-- ===== Song Sections tab state =====
local ss_mode = 1 -- 1=REAPER, 2=Sidecar, 3=AI, 4=Song Map
local ss_genre = settings.get("default_genre")
local ss_style = settings.get("default_style")
local ss_mapping = settings.get("default_mapping")
local ss_drummer = ""
local ss_drummer_intensity = 1.0
local ss_ai_description = ""
local ss_ai_tempo = settings.get("default_ai_tempo")
local ss_ai_research_song = false
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

local SS_AI_RESEARCH_SONG_HELP = {
  { title = "Research Song (experimental)", body = "Before composing, let "
    .. "the AI agent look up verified metadata (tempo, genre, release "
    .. "date, drummer credit) for a real, named song via MusicBrainz/"
    .. "AcousticBrainz - use this when your Description names a real "
    .. "song or artist. Metadata-only: never fetches lyrics or audio. "
    .. "AI mode only. See claudedocs/design_song_research_grounding.md." },
}

local DRUMMER_INTENSITY_HELP = {
  { title = "Drummer Intensity", body = "How strongly the drummer's "
    .. "signature style overrides the genre pattern. 1.0 = full drummer "
    .. "character (default). Lower it toward 0.0 to keep more of the "
    .. "genre plugin's own identity - e.g. a low value gives a subtle "
    .. "Porcaro feel over a Death Metal pattern instead of Porcaro fully "
    .. "taking over." },
}

-- ===== Riff-Lock Beat tab state =====
local rl_genre = settings.get("default_genre")
local rl_style = settings.get("default_style")
local rl_drummer = ""
local rl_drummer_intensity = 1.0
local rl_section = "verse"
local rl_mapping = settings.get("default_mapping")
local rl_grid = "16th"
local rl_lock_strength = 1.0
local rl_snare_mode = 1 -- 1=Off, 2=Reinforce, 3=Stab
local rl_snare_threshold = 0.85
local rl_hihat_mode = 1 -- 1=Off, 2=Reinforce, 3=Stab
local rl_hihat_threshold = 0.85
local rl_crash_mode = 1 -- 1=Off, 2=Reinforce, 3=Stab
local rl_crash_threshold = 0.85
local rl_ride_mode = 1 -- 1=Off, 2=Reinforce, 3=Stab
local rl_ride_threshold = 0.85
local rl_china_mode = 1 -- 1=Off, 2=Reinforce, 3=Stab
local rl_china_threshold = 0.85
local rl_notes = ""
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

local RL_HIHAT_HELP = {
  { title = "Off", body = "Hi-hat is untouched by the riff — comes purely "
    .. "from the genre plugin/drummer style." },
  { title = "Reinforce", body = "Boosts velocity on existing hi-hat hits "
    .. "that land near a strong riff accent." },
  { title = "Stab", body = "Inserts a unison closed hi-hat hit at very "
    .. "strong accents where a kick was locked but no hi-hat is nearby. "
    .. "Threshold below controls how strong an accent must be." },
}

local RL_CRASH_HELP = {
  { title = "Off", body = "Crash is untouched by the riff — comes purely "
    .. "from the genre plugin/drummer style." },
  { title = "Reinforce", body = "Boosts velocity on existing crash hits "
    .. "that land near a strong riff accent." },
  { title = "Stab", body = "Inserts a unison crash hit at very strong "
    .. "accents where a kick was locked but no crash is nearby. "
    .. "Threshold below controls how strong an accent must be." },
}

local RL_RIDE_HELP = {
  { title = "Off", body = "Ride is untouched by the riff — comes purely "
    .. "from the genre plugin/drummer style." },
  { title = "Reinforce", body = "Boosts velocity on existing ride hits "
    .. "that land near a strong riff accent." },
  { title = "Stab", body = "Inserts a unison ride hit at very strong "
    .. "accents where a kick was locked but no ride is nearby. "
    .. "Threshold below controls how strong an accent must be." },
}

local RL_CHINA_HELP = {
  { title = "Off", body = "China is untouched by the riff — comes purely "
    .. "from the genre plugin/drummer style." },
  { title = "Reinforce", body = "Boosts velocity on existing china hits "
    .. "that land near a strong riff accent." },
  { title = "Stab", body = "Inserts a unison china hit at very strong "
    .. "accents where a kick was locked but no china is nearby. "
    .. "Threshold below controls how strong an accent must be." },
}

local RL_NOTES_HELP = {
  { title = "Notes (optional)", body = "When filled in, the AI pattern "
    .. "generator infers genre/style/pattern from this text instead of "
    .. "the Genre/Style fields above (e.g. 'aggressive death metal "
    .. "breakdown with blast beats'). Drummer, Lock Strength, and every "
    .. "reaction below still apply on top of the AI-generated pattern. "
    .. "Requires 'uv sync --group ai' and an AI provider API key." },
}

-- ===== Additive Rhythm tab state =====
local AR_GRID_VALUES = { "4", "8", "16", "32" }
local ar_grouping = "3-3-3-3-2-2"
local ar_grid = "16"
local ar_tempo = "120"
local ar_drummer = ""
local ar_drummer_intensity = 1.0
local ar_status = ""

local AR_GROUPING_HELP = {
  { title = "Additive Rhythm (experimental)", body = "Converts an "
    .. "additive rhythmic-grouping string (box notation) into per-bar "
    .. "time signatures and a kick/snare/hihat pattern - e.g. "
    .. "'3-3-3-3-2-2' at a 16th-note grid resolves to a 6/8 bar "
    .. "followed by a 2/8 bar. A run of identical group sizes auto-"
    .. "splits into one bar each; '|' marks an explicit heterogeneous "
    .. "bar instead (e.g. '2+2+3|' for a single 7/8 bar). See "
    .. "claudedocs/design_additive_rhythm_grouping.md." },
}

-- ===== Step Editor tab state =====
-- ADR 0009 - see claudedocs/design_step_editor_grid.md. `se_data` is nil
-- until "Load Selected Item" succeeds; `se_item` is the MediaItem it was
-- read from (commit() writes back to this item, not whatever's selected
-- at click time - matches riff_lock's "read selection fresh, then hold
-- it for the run" pattern, but held across many clicks here instead of
-- one Generate click).
local se_mapping = settings.get("default_mapping")
local se_grid = "16th"
local se_data = nil
local se_item = nil
local se_current_bar = 0
local se_selected_lanes = {}
local se_reassign_target = ""
local se_velocity_factor = 1.0
local se_velocity_style = "flat"
local se_status = ""

local SE_VELOCITY_STYLE_NAMES = { "flat", "crescendo", "halftime_accent", "backbeat_emphasis" }
local SE_STEP_CELL_SIZE = 22

local SE_HELP = {
  { title = "Step Editor", body = "Manually correct a generated drum "
    .. "pattern on the selected MIDI item. Grid clicks toggle individual "
    .. "hits; the controls above the grid act on whichever lane(s) are "
    .. "checked. Every change writes straight back to the item and is "
    .. "its own undo step - there's no separate Save." },
}

local SE_AMOUNT_HELP = {
  { title = "Amount (not yet wired up)", body = "Density-style +/- "
    .. "control that adds or removes hits in a lane, mirroring "
    .. "EZDrummer 3's Amount knob. The Python side (adjust_density, the "
    .. "'adjust-density' CLI verb) is implemented, but this slider isn't "
    .. "wired to call it yet - see ADR 0010's Implementation note "
    .. "(docs/adr/0010-amount-density-control-python-roundtrip.md)." },
}

local SE_DUPLICATE_HELP = {
  { title = "Duplicate Bar -> Forward", body = "Overwrites every bar "
    .. "after the one currently shown with its pattern, across every "
    .. "lane - not just the next bar, all the way to the end of the "
    .. "item. Whatever was in those later bars is replaced, not merged. "
    .. "Disabled on the last bar (nothing after it to fill)." },
}

local function se_kit_map_entry(mapping)
  return options.cache.kit_maps[mapping]
end

local function se_kit_map_instruments(mapping)
  local entry = se_kit_map_entry(mapping)
  if not entry or not entry.loaded then return {} end
  local out = {}
  for _, n in ipairs(entry.notes) do
    out[#out + 1] = n.instrument
  end
  return out
end

-- Attempts to (re)build se_data from se_pending_item using whatever
-- kit-map is cached for se_mapping - kicks off a fetch and defers to
-- itself (via refresh_kit_map's on_complete) instead of reading if the
-- kit-map isn't cached yet.
local se_pending_item = nil

se_try_load_pattern = function()
  local item = se_pending_item
  if not item then return end

  local entry = se_kit_map_entry(se_mapping)
  if not entry or not entry.loaded then
    refresh_kit_map(se_mapping)
    se_status = "Loading kit-map for '" .. se_mapping .. "'..."
    return
  end

  se_pending_item = nil
  local data, err = step_editor.read_pattern_from_item(item, entry.notes, se_grid)
  if not data then
    se_status = "Error: " .. (err or "could not read pattern from item.")
  else
    se_data = data
    se_item = item
    se_current_bar = 0
    se_selected_lanes = {}
    se_status = string.format("Loaded %d bar(s).", data.bars)
  end
end

local function se_lane_keys_sorted_by_note(data)
  local keys = {}
  for k, _ in pairs(data.lanes) do
    keys[#keys + 1] = k
  end
  table.sort(keys, function(a, b) return data.lanes[a].note < data.lanes[b].note end)
  return keys
end

local function se_find_note(lane, bar, step)
  for _, note in ipairs(lane.notes) do
    if note.bar == bar and note.step == step then
      return note
    end
  end
  return nil
end

local function se_selected_lane_keys()
  local out = {}
  for k, v in pairs(se_selected_lanes) do
    if v then out[#out + 1] = k end
  end
  table.sort(out)
  return out
end

local function draw_step_editor_tab()
  reaper.ImGui_Text(ctx, "Step Editor")
  draw_help_button("se_intro", SE_HELP)

  if not options.cache.loaded then
    reaper.ImGui_TextColored(ctx, 0xfbbf24ff,
      "Options not loaded - configure Python exe and click Refresh "
      .. "Options on the Settings tab."
    )
  end

  local changed
  changed, se_mapping = combo_from_list("Mapping", se_mapping, options.cache.mappings)
  changed, se_grid = combo_from_list("Grid", se_grid, GRID_VALUES)

  local item_count = reaper.CountSelectedMediaItems(0)
  local load_disabled = job_runner.is_running() or item_count == 0
  if load_disabled then reaper.ImGui_BeginDisabled(ctx) end
  if reaper.ImGui_Button(ctx, "Load Selected Item") then
    local item = reaper.GetSelectedMediaItem(0, 0)
    if not item then
      se_status = "Select a MIDI item first."
    else
      se_pending_item = item
      se_try_load_pattern()
    end
  end
  if load_disabled then reaper.ImGui_EndDisabled(ctx) end
  if item_count == 0 then
    reaper.ImGui_SameLine(ctx)
    reaper.ImGui_TextColored(ctx, 0xfb7185ff, "Select a MIDI item first.")
  end

  reaper.ImGui_TextWrapped(ctx, se_status)
  reaper.ImGui_Separator(ctx)

  if not se_data then
    reaper.ImGui_TextDisabled(ctx, "No pattern loaded yet.")
    return
  end

  -- ----- Macro Controls strip (acts on whichever lanes are checked) -----
  if reaper.ImGui_Button(ctx, "Select All##se") then
    for k, _ in pairs(se_data.lanes) do se_selected_lanes[k] = true end
  end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_Button(ctx, "Select None##se") then
    se_selected_lanes = {}
  end

  local kit_instruments = se_kit_map_instruments(se_mapping)

  reaper.ImGui_AlignTextToFramePadding(ctx)
  reaper.ImGui_Text(ctx, "Reassign to:")
  reaper.ImGui_SameLine(ctx)
  reaper.ImGui_SetNextItemWidth(ctx, 160)
  changed, se_reassign_target = combo_from_list("##se_reassign", se_reassign_target, kit_instruments)
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_Button(ctx, "Apply##se_reassign") then
    local lanes = se_selected_lane_keys()
    if #lanes == 0 or se_reassign_target == "" then
      se_status = "Check lane(s) and pick a target first."
    else
      local ok, err = step_editor.reassign_lane(se_data, lanes, se_reassign_target)
      if ok then
        step_editor.commit(se_item, se_data)
        se_selected_lanes = {}
        se_status = "Reassigned."
      else
        se_status = "Error: " .. (err or "reassign failed.")
      end
    end
  end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_Button(ctx, "Swap Articulation##se") then
    local lanes = se_selected_lane_keys()
    if #lanes == 0 or se_reassign_target == "" then
      se_status = "Check lane(s) and pick a target first."
    else
      local ok, err = step_editor.swap_articulation(se_data, lanes, se_reassign_target)
      if ok then
        step_editor.commit(se_item, se_data)
        se_selected_lanes = {}
        se_status = "Articulation swapped."
      else
        se_status = "Error: " .. (err or "swap failed.")
      end
    end
  end

  reaper.ImGui_SetNextItemWidth(ctx, 160)
  changed, se_velocity_factor = reaper.ImGui_SliderDouble(ctx, "Velocity Scale", se_velocity_factor, 0.5, 2.0)
  if reaper.ImGui_IsItemDeactivatedAfterEdit(ctx) then
    local lanes = se_selected_lane_keys()
    if #lanes == 0 then
      se_status = "Check lane(s) first."
    else
      step_editor.scale_velocity(se_data, lanes, se_velocity_factor)
      step_editor.commit(se_item, se_data)
      se_status = "Velocity scaled."
    end
    se_velocity_factor = 1.0
  end

  reaper.ImGui_SetNextItemWidth(ctx, 160)
  changed, se_velocity_style = combo_from_list("Velocity Style", se_velocity_style, SE_VELOCITY_STYLE_NAMES)
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_Button(ctx, "Apply##se_style") then
    local lanes = se_selected_lane_keys()
    if #lanes == 0 then
      se_status = "Check lane(s) first."
    else
      local ok, err = step_editor.apply_velocity_style(se_data, lanes, se_velocity_style)
      if ok then
        step_editor.commit(se_item, se_data)
        se_status = "Velocity style applied."
      else
        se_status = "Error: " .. (err or "apply failed.")
      end
    end
  end

  reaper.ImGui_BeginDisabled(ctx)
  reaper.ImGui_SetNextItemWidth(ctx, 160)
  reaper.ImGui_SliderDouble(ctx, "Amount##se", 0.0, -1.0, 1.0)
  reaper.ImGui_EndDisabled(ctx)
  draw_help_button("se_amount", SE_AMOUNT_HELP)

  reaper.ImGui_Separator(ctx)

  -- ----- Grid (direct manipulation), one bar at a time -----
  reaper.ImGui_Text(ctx, string.format("Bar %d / %d", se_current_bar + 1, se_data.bars))
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_Button(ctx, "< Prev##se") then
    if se_current_bar > 0 then se_current_bar = se_current_bar - 1 end
  end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_Button(ctx, "Next >##se") then
    if se_current_bar < se_data.bars - 1 then se_current_bar = se_current_bar + 1 end
  end

  -- ----- Bar Actions row -----
  local dup_disabled = se_current_bar >= se_data.bars - 1
  if dup_disabled then reaper.ImGui_BeginDisabled(ctx) end
  if reaper.ImGui_Button(ctx, "Duplicate Bar " .. (se_current_bar + 1) .. " -> Forward##se") then
    local ok, err = step_editor.duplicate_bar_forward(se_data, se_current_bar)
    if ok then
      step_editor.commit(se_item, se_data)
      se_status = string.format(
        "Duplicated bar %d into bars %d-%d.", se_current_bar + 1, se_current_bar + 2, se_data.bars
      )
    else
      se_status = "Error: " .. (err or "duplicate failed.")
    end
  end
  if dup_disabled then reaper.ImGui_EndDisabled(ctx) end
  reaper.ImGui_SameLine(ctx)
  draw_help_button("se_duplicate", SE_DUPLICATE_HELP)

  local steps_per_bar, spb_err = step_editor.steps_per_bar(
    se_data.grid_resolution, se_data.ts_num, se_data.ts_denom
  )
  if not steps_per_bar then
    reaper.ImGui_TextColored(ctx, 0xfb7185ff, "Error: " .. tostring(spb_err))
    return
  end

  for _, lane_key in ipairs(se_lane_keys_sorted_by_note(se_data)) do
    local lane = se_data.lanes[lane_key]
    reaper.ImGui_PushID(ctx, lane_key)

    local checked = se_selected_lanes[lane_key] or false
    local sel_changed, sel_new = reaper.ImGui_Checkbox(ctx, "##sel", checked)
    if sel_changed then se_selected_lanes[lane_key] = sel_new end
    reaper.ImGui_SameLine(ctx)
    reaper.ImGui_Text(ctx, lane.label)
    -- Fixed X offset (rather than SameLine()'s default spacing) so the
    -- step buttons line up into columns regardless of label length.
    reaper.ImGui_SameLine(ctx, 160)

    for step = 0, steps_per_bar - 1 do
      if step > 0 then reaper.ImGui_SameLine(ctx) end
      local note = se_find_note(lane, se_current_bar, step)
      local color = 0x2b2f36ff
      if note then
        color = note.off_grid and 0xf59e0bff or 0x38bdf8ff
      end
      reaper.ImGui_PushStyleColor(ctx, reaper.ImGui_Col_Button(), color)
      if reaper.ImGui_Button(ctx, "##s" .. step, SE_STEP_CELL_SIZE, SE_STEP_CELL_SIZE) then
        local kit_entry = se_data.kit_map_by_key[lane_key]
        local velocity = (kit_entry and kit_entry.default_velocity) or 100
        step_editor.toggle_step(se_data, lane_key, se_current_bar, step, velocity)
        step_editor.commit(se_item, se_data)
      end
      reaper.ImGui_PopStyleColor(ctx)
    end

    reaper.ImGui_PopID(ctx)
  end
end

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
    changed, ss_ai_research_song = reaper.ImGui_Checkbox(
      ctx, "Research Song (experimental)", ss_ai_research_song
    )
    draw_help_button("ss_ai_research_song", SS_AI_RESEARCH_SONG_HELP)
  else
    if not options.cache.loaded then
      reaper.ImGui_TextColored(ctx, 0xfbbf24ff,
        "Options not loaded - configure Python exe and click Refresh "
        .. "Options on the Settings tab."
      )
    end

    local changed
    changed, ss_genre = combo_from_list("Genre", ss_genre, options.cache.genres)
    local ss_styles = options.styles_for(ss_genre)
    if changed then
      local style_ok = false
      for _, s in ipairs(ss_styles) do
        if s == ss_style then style_ok = true end
      end
      if not style_ok then
        ss_style = ss_styles[1] or ""
      end
    end
    changed, ss_style = combo_from_list("Style", ss_style, ss_styles)
    changed, ss_drummer = combo_from_list("Drummer (optional)", ss_drummer, options.cache.drummers, "(none)")
    changed, ss_drummer_intensity = reaper.ImGui_SliderDouble(ctx, "Drummer Intensity", ss_drummer_intensity, 0.0, 1.0)
    draw_help_button("ss_drummer_intensity", DRUMMER_INTENSITY_HELP)
    changed, ss_mapping = combo_from_list("Mapping", ss_mapping, options.cache.mappings)
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
        local ts_num, ts_denom = reaper.GetProjectTimeSignature2(0)
        sections.create_regions_from_sections(default_sections, bpm, ts_num, ts_denom)

        local json = sections.sections_to_json(default_sections, bpm, ts_num, ts_denom)
        local f = io.open(sc_path, "w")
        if f then f:write(json); f:close() end

        local cmd = sections.build_template_cmd(python_exe, ss_genre, ss_style, ss_mapping, sc_path, midi_out, ss_drummer, ss_drummer_intensity)
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
        local cmd = sections.build_ai_cmd(python_exe, ss_ai_description, ss_ai_tempo, midi_out, sc_path, ss_ai_research_song)
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
        local cmd = sections.build_songmap_cmd(python_exe, ss_genre, ss_style, ss_mapping, map_path, timeline_path, midi_out, ss_drummer, ss_drummer_intensity)
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

  if not options.cache.loaded then
    reaper.ImGui_TextColored(ctx, 0xfbbf24ff,
      "Options not loaded - configure Python exe and click Refresh "
      .. "Options on the Settings tab."
    )
  end

  local changed
  changed, rl_genre = combo_from_list("Genre", rl_genre, options.cache.genres)
  local rl_styles = options.styles_for(rl_genre)
  if changed then
    local style_ok = false
    for _, s in ipairs(rl_styles) do
      if s == rl_style then style_ok = true end
    end
    if not style_ok then
      rl_style = rl_styles[1] or ""
    end
  end
  changed, rl_style = combo_from_list("Style", rl_style, rl_styles)
  changed, rl_drummer = combo_from_list("Drummer (optional)", rl_drummer, options.cache.drummers, "(none)")
  changed, rl_drummer_intensity = reaper.ImGui_SliderDouble(ctx, "Drummer Intensity", rl_drummer_intensity, 0.0, 1.0)
  draw_help_button("rl_drummer_intensity", DRUMMER_INTENSITY_HELP)
  changed, rl_section = reaper.ImGui_InputText(ctx, "Section", rl_section)
  changed, rl_mapping = combo_from_list("Mapping", rl_mapping, options.cache.mappings)
  changed, rl_grid = combo_from_list("Grid", rl_grid, GRID_VALUES)

  changed, rl_notes = reaper.ImGui_InputTextMultiline(ctx, "Notes (optional)", rl_notes, -1, 60)
  draw_help_button("rl_notes", RL_NOTES_HELP)

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

  reaper.ImGui_Text(ctx, "Hi-Hat Reaction:")
  if reaper.ImGui_RadioButton(ctx, "Off##hihat", rl_hihat_mode == 1) then rl_hihat_mode = 1 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Reinforce##hihat", rl_hihat_mode == 2) then rl_hihat_mode = 2 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Stab##hihat", rl_hihat_mode == 3) then rl_hihat_mode = 3 end
  draw_help_button("rl_hihat", RL_HIHAT_HELP)

  if rl_hihat_mode == 3 then
    changed, rl_hihat_threshold = reaper.ImGui_SliderDouble(ctx, "Stab Threshold##hihat", rl_hihat_threshold, 0.0, 1.0)
  end

  reaper.ImGui_Text(ctx, "Crash Reaction:")
  if reaper.ImGui_RadioButton(ctx, "Off##crash", rl_crash_mode == 1) then rl_crash_mode = 1 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Reinforce##crash", rl_crash_mode == 2) then rl_crash_mode = 2 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Stab##crash", rl_crash_mode == 3) then rl_crash_mode = 3 end
  draw_help_button("rl_crash", RL_CRASH_HELP)

  if rl_crash_mode == 3 then
    changed, rl_crash_threshold = reaper.ImGui_SliderDouble(ctx, "Stab Threshold##crash", rl_crash_threshold, 0.0, 1.0)
  end

  reaper.ImGui_Text(ctx, "Ride Reaction:")
  if reaper.ImGui_RadioButton(ctx, "Off##ride", rl_ride_mode == 1) then rl_ride_mode = 1 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Reinforce##ride", rl_ride_mode == 2) then rl_ride_mode = 2 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Stab##ride", rl_ride_mode == 3) then rl_ride_mode = 3 end
  draw_help_button("rl_ride", RL_RIDE_HELP)

  if rl_ride_mode == 3 then
    changed, rl_ride_threshold = reaper.ImGui_SliderDouble(ctx, "Stab Threshold##ride", rl_ride_threshold, 0.0, 1.0)
  end

  reaper.ImGui_Text(ctx, "China Reaction:")
  if reaper.ImGui_RadioButton(ctx, "Off##china", rl_china_mode == 1) then rl_china_mode = 1 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Reinforce##china", rl_china_mode == 2) then rl_china_mode = 2 end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_RadioButton(ctx, "Stab##china", rl_china_mode == 3) then rl_china_mode = 3 end
  draw_help_button("rl_china", RL_CHINA_HELP)

  if rl_china_mode == 3 then
    changed, rl_china_threshold = reaper.ImGui_SliderDouble(ctx, "Stab Threshold##china", rl_china_threshold, 0.0, 1.0)
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
        local function mode_str(mode_int)
          if mode_int == 2 then return "reinforce"
          elseif mode_int == 3 then return "stab"
          else return "off" end
        end
        local snare_mode_str = mode_str(rl_snare_mode)
        local hihat_mode_str = mode_str(rl_hihat_mode)
        local crash_mode_str = mode_str(rl_crash_mode)
        local ride_mode_str = mode_str(rl_ride_mode)
        local china_mode_str = mode_str(rl_china_mode)

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
          drummer_intensity = rl_drummer_intensity,
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
          hihat_mode = hihat_mode_str,
          hihat_threshold = rl_hihat_threshold,
          crash_mode = crash_mode_str,
          crash_threshold = rl_crash_threshold,
          ride_mode = ride_mode_str,
          ride_threshold = rl_ride_threshold,
          china_mode = china_mode_str,
          china_threshold = rl_china_threshold,
          notes = rl_notes,
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

local function draw_additive_rhythm_tab()
  reaper.ImGui_TextColored(ctx, 0xfbbf24ff, "Experimental spike - not yet part of the main generation pipeline.")

  local changed
  changed, ar_grouping = reaper.ImGui_InputText(ctx, "Grouping", ar_grouping)
  draw_help_button("ar_grouping", AR_GROUPING_HELP)

  changed, ar_grid = combo_from_list("Grid", ar_grid, AR_GRID_VALUES)
  changed, ar_tempo = reaper.ImGui_InputText(ctx, "Tempo (BPM)", ar_tempo)

  if not options.cache.loaded then
    reaper.ImGui_TextColored(ctx, 0xfbbf24ff,
      "Options not loaded - configure Python exe and click Refresh "
      .. "Options on the Settings tab."
    )
  end
  changed, ar_drummer = combo_from_list("Drummer (optional)", ar_drummer, options.cache.drummers, "(none)")
  changed, ar_drummer_intensity = reaper.ImGui_SliderDouble(ctx, "Drummer Intensity", ar_drummer_intensity, 0.0, 1.0)
  draw_help_button("ar_drummer_intensity", DRUMMER_INTENSITY_HELP)

  reaper.ImGui_Separator(ctx)

  local disabled = job_runner.is_running()
  if disabled then reaper.ImGui_BeginDisabled(ctx) end
  if reaper.ImGui_Button(ctx, "Generate") then
    local python_exe = settings.resolve_python_exe()
    if not python_exe then
      ar_status = "Cancelled: no Python interpreter configured."
    elseif ar_grouping == "" then
      ar_status = "Cancelled: Grouping is required."
    else
      local tempo = tonumber(ar_tempo) or 120
      local midi_out = midi_out_path("midi_drums_additive_rhythm.mid")
      local timeline_path = additive_rhythm.get_project_dir() .. "/midi_drums_additive_rhythm_timeline.json"

      local cmd = additive_rhythm.build_cmd(python_exe, {
        grouping = ar_grouping,
        grid = tonumber(ar_grid) or 16,
        tempo = tempo,
        drummer = ar_drummer,
        drummer_intensity = ar_drummer_intensity,
        midi_out = midi_out,
        timeline_path = timeline_path,
      })

      job_runner.start(cmd, "Additive Rhythm", function()
        additive_rhythm.on_job_complete({
          timeline_path = timeline_path,
          midi_out = midi_out,
        })
        ar_status = "Done."
      end)
      ar_status = "Running..."
    end
  end
  if disabled then reaper.ImGui_EndDisabled(ctx) end

  reaper.ImGui_TextWrapped(ctx, ar_status)
end

-- Auto-saving text field bound directly to an ExtState key — no
-- separate Save button, matches every other tab's "just works" feel.
local function settings_field(label, key)
  local value = settings.get(key)
  local changed, new_value = reaper.ImGui_InputText(ctx, label, value)
  if changed then
    settings.set(key, new_value)
  end
end

local function draw_settings_tab()
  reaper.ImGui_Text(ctx, "Python interpreter")
  local exe = settings.get("python_exe")
  reaper.ImGui_SetNextItemWidth(ctx, -170)
  local exe_changed, new_exe = reaper.ImGui_InputText(ctx, "##python_exe", exe)
  if exe_changed then
    settings.set("python_exe", new_exe)
  end
  reaper.ImGui_SameLine(ctx)
  if reaper.ImGui_Button(ctx, "Browse...") then
    local ok, picked = reaper.GetUserFileNameForRead(
      exe, "Select midi_drums pythonw.exe", ""
    )
    if ok and picked ~= "" then
      settings.set("python_exe", picked)
    end
  end
  reaper.ImGui_SameLine(ctx)
  reaper.ImGui_Text(ctx, "Python exe path")

  local refresh_disabled = job_runner.is_running()
  if refresh_disabled then reaper.ImGui_BeginDisabled(ctx) end
  if reaper.ImGui_Button(ctx, "Refresh Options") then
    refresh_options()
  end
  if refresh_disabled then reaper.ImGui_EndDisabled(ctx) end
  reaper.ImGui_SameLine(ctx)
  if options.cache.loaded then
    reaper.ImGui_TextColored(ctx, 0x4ade80ff,
      string.format(
        "Loaded: %d genres, %d drummers, %d mappings",
        #options.cache.genres, #options.cache.drummers, #options.cache.mappings
      )
    )
  elseif options.cache.error then
    reaper.ImGui_TextColored(ctx, 0xfb7185ff, "Error: " .. options.cache.error)
  else
    reaper.ImGui_TextColored(ctx, 0x778ca6ff, "Not loaded yet.")
  end

  reaper.ImGui_Separator(ctx)
  reaper.ImGui_Text(ctx, "Defaults")
  settings_field("Default genre", "default_genre")
  settings_field("Default style", "default_style")
  settings_field("Default mapping", "default_mapping")
  settings_field("Default AI tempo", "default_ai_tempo")
  settings_field("Sidecar path override", "sidecar_path_override")

  reaper.ImGui_Separator(ctx)
  reaper.ImGui_TextWrapped(ctx,
    "MIDI Drums Panel - unified replacement for create_song_sections.lua, "
    .. "create_beat_from_riff.lua, and midi_drums_help.lua. Generates "
    .. "drum MIDI via the midi_drums Python package and imports it into "
    .. "this project. See reaper/README.md for setup and docs."
  )
end

local STATUS_COLORS = {
  idle = 0x778ca6ff,
  running = 0x38bdf8ff,
  done = 0x4ade80ff,
  error = 0xfb7185ff,
}

local function draw_log_tab()
  local st = job_runner.state
  reaper.ImGui_Text(ctx, "Job: " .. (st.job_label or "(none)"))
  reaper.ImGui_SameLine(ctx)
  reaper.ImGui_Text(ctx, string.format("(%.1fs)", job_runner.elapsed_seconds()))
  reaper.ImGui_SameLine(ctx)
  reaper.ImGui_TextColored(ctx, STATUS_COLORS[st.status] or STATUS_COLORS.idle, st.status)

  reaper.ImGui_Separator(ctx)

  if font_mono then reaper.ImGui_PushFont(ctx, font_mono, FONT_MONO_SIZE) end
  if reaper.ImGui_BeginChild(ctx, "log_box", 0, 300) then
    if #st.log_lines == 0 then
      reaper.ImGui_TextDisabled(ctx, "No job run yet.")
    else
      for _, line in ipairs(st.log_lines) do
        reaper.ImGui_TextWrapped(ctx, line)
      end
      if job_runner.is_running() then
        reaper.ImGui_SetScrollHereY(ctx, 1.0)
      end
    end
    reaper.ImGui_EndChild(ctx)
  end
  if font_mono then reaper.ImGui_PopFont(ctx) end
end

local function loop()
  job_runner.poll()

  reaper.ImGui_SetNextWindowSize(ctx, 640, 520, reaper.ImGui_Cond_FirstUseEver())
  local visible, open = reaper.ImGui_Begin(ctx, "MIDI Drums", true)
  if visible then
    if font_sans then reaper.ImGui_PushFont(ctx, font_sans, FONT_SANS_SIZE) end

    if reaper.ImGui_BeginTabBar(ctx, "midi_drums_tabs") then
      if reaper.ImGui_BeginTabItem(ctx, "Song Sections") then
        draw_song_sections_tab()
        reaper.ImGui_EndTabItem(ctx)
      end
      if reaper.ImGui_BeginTabItem(ctx, "Riff-Lock Beat") then
        draw_riff_lock_tab()
        reaper.ImGui_EndTabItem(ctx)
      end
      if reaper.ImGui_BeginTabItem(ctx, "Additive Rhythm") then
        draw_additive_rhythm_tab()
        reaper.ImGui_EndTabItem(ctx)
      end
      if reaper.ImGui_BeginTabItem(ctx, "Step Editor") then
        draw_step_editor_tab()
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

-- Silent, non-prompting startup refresh: only fires if a python_exe is
-- already configured and opens successfully - never triggers the
-- python-exe picker dialog on script load (see cached_python_exe()).
refresh_options()

reaper.defer(loop)
