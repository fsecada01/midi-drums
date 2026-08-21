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
-- Task 6 fills this in

-- ===== Riff-Lock Beat tab state =====
-- Task 7 fills this in

local function draw_song_sections_tab()
  -- Task 6 fills this in
end

local function draw_riff_lock_tab()
  -- Task 7 fills this in
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
