-- reaper/midi_drums/settings.lua
-- ExtState configuration wrapper for midi_drums REAPER integration
-- Consolidates Python venv path resolution and default settings

local M = {}

M.SECTION = "midi_drums"

M.DEFAULTS = {
  python_exe = "",
  default_genre = "metal",
  default_style = "doom",
  default_mapping = "ezdrummer3",
  default_ai_tempo = "120",
  sidecar_path_override = "",
}

function M.get(key)
  local v = reaper.GetExtState(M.SECTION, key)
  if v == "" then
    return M.DEFAULTS[key] or ""
  end
  return v
end

function M.set(key, value)
  reaper.SetExtState(M.SECTION, key, value or "", true)
end

-- Resolve the midi_drums venv's pythonw.exe path, prompting via a
-- dialog if unset or if the stored path no longer opens (moved venv,
-- different machine, fresh REAPER install). Pre-fills the stale value
-- so re-confirming after a false alarm is one click. Returns nil if
-- the user cancels (caller should treat that as "abort this job").
function M.resolve_python_exe()
  local exe = M.get("python_exe")
  if exe ~= "" then
    local f = io.open(exe, "rb")
    if f then
      f:close()
      return exe
    end
  end

  local ok, input = reaper.GetUserInputs(
    "midi_drums Setup", 1,
    "Path to midi_drums venv pythonw.exe,extrawidth=200",
    (exe ~= "") and exe or "C:/path/to/midi_drums/.venv/Scripts/pythonw.exe"
  )
  if not ok then
    return nil
  end
  local new_exe = input:match("^%s*(.-)%s*$")
  if new_exe == "" then
    reaper.ShowMessageBox("Python path cannot be empty.", "Setup Error", 0)
    return nil
  end

  local f = io.open(new_exe, "rb")
  if f then
    f:close()
  else
    local proceed = reaper.ShowMessageBox(
      "Could not open:\n" .. new_exe .. "\n\nSave it anyway?",
      "Path Not Found", 4
    )
    if proceed ~= 6 then
      return nil
    end
  end

  M.set("python_exe", new_exe)
  return new_exe
end

return M
