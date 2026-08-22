-- reaper/midi_drums/job_runner.lua
-- Async detached-subprocess execution engine for the midi_drums REAPER
-- panel. Launches Python (or any shell command) detached via a temp .bat
-- wrapper so the calling defer() frame never blocks — the single fix this
-- whole panel redesign exists to deliver. No dependency on any other new
-- module.

local M = {}

M.STATUS = { IDLE = "idle", RUNNING = "running", DONE = "done", ERROR = "error" }

M.state = {
  status = M.STATUS.IDLE,
  job_label = nil,
  log_lines = {},
  log_path = nil,
  start_time = nil,
  exit_code = nil,
  _on_complete = nil,
  _last_read_pos = 0,
}

function M.is_running()
  return M.state.status == M.STATUS.RUNNING
end

function M.elapsed_seconds()
  if not M.state.start_time then return 0 end
  return reaper.time_precise() - M.state.start_time
end

-- Launches `cmd` detached via a temp .bat wrapper: `start /B` hands
-- the child off to Windows and returns immediately (os.execute here
-- only waits for `start` itself to launch it, not for the child to
-- finish), so this never blocks the calling defer() frame the way the
-- retired scripts' handle:read("*a") did. stdout+stderr are captured
-- to a temp log file, with a trailing "DONE <exitcode>" line appended
-- once the child exits — poll() watches for that line.
function M.start(cmd, job_label, on_complete)
  if M.is_running() then
    return false, "A job is already running — wait for it to finish."
  end

  local temp_dir = os.getenv("TEMP") or os.getenv("TMP") or "."
  local stamp = string.format("%d", math.floor(reaper.time_precise() * 1000))
  local bat_path = temp_dir .. "/midi_drums_job_" .. stamp .. ".bat"
  local log_path = temp_dir .. "/midi_drums_job_" .. stamp .. ".log"

  local bat = io.open(bat_path, "w")
  if not bat then
    return false, "Could not create temp launcher script: " .. bat_path
  end
  bat:write("@echo off\r\n")
  bat:write(cmd .. ' > "' .. log_path .. '" 2>&1\r\n')
  -- Note the space before ">>": "%errorlevel%>>" (no space) makes
  -- cmd.exe's parser mis-tokenize the line — %errorlevel% expands to
  -- empty AND the redirection is dropped, so "DONE" ends up on stdout
  -- (lost under a detached launch) instead of in the log. Confirmed by
  -- direct cmd.exe testing outside REAPER; see task-2-report.md.
  bat:write('echo DONE %errorlevel% >> "' .. log_path .. '"\r\n')
  bat:close()

  os.execute('start "" /B "' .. bat_path .. '"')

  M.state.status = M.STATUS.RUNNING
  M.state.job_label = job_label
  M.state.log_lines = {}
  M.state.log_path = log_path
  M.state.start_time = reaper.time_precise()
  M.state.exit_code = nil
  M.state._on_complete = on_complete
  M.state._last_read_pos = 0
  return true
end

-- Tails M.state.log_path for new bytes since the last poll, splits
-- them into lines, and watches the most recent line for the DONE
-- marker. Safe to call every defer() frame even when idle (no-op).
function M.poll()
  if not M.is_running() then return end

  local f = io.open(M.state.log_path, "r")
  if not f then return end -- bat hasn't created the log yet this frame

  f:seek("set", M.state._last_read_pos)
  local chunk = f:read("*a")
  M.state._last_read_pos = f:seek()
  f:close()

  if not chunk or chunk == "" then return end

  for line in chunk:gmatch("([^\r\n]*)\r?\n") do
    M.state.log_lines[#M.state.log_lines + 1] = line
    local code = line:match("^DONE (%-?%d+)%s*$")
    if code then
      M.state.exit_code = tonumber(code)
      if M.state.exit_code == 0 then
        M.state.status = M.STATUS.DONE
        if M.state._on_complete then M.state._on_complete() end
      else
        M.state.status = M.STATUS.ERROR
      end
    end
  end
end

return M
