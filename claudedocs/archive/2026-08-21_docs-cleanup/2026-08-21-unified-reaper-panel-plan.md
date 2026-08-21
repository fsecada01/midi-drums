# Unified REAPER Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the three independent REAPER Lua scripts
(`create_song_sections.lua`, `create_beat_from_riff.lua`,
`midi_drums_help.lua`) with one dockable ReaImGui panel
(`reaper/midi_drums_panel.lua`) that exposes Song Sections generation,
Riff-Lock Beat generation, consolidated Settings, and a live Log — driven
by an async detached-subprocess job runner so the panel never freezes.

**Architecture:** One entry-point script owns a ReaImGui window and a
`defer()` render loop; four small modules under `reaper/midi_drums/` hold
everything that isn't drawing widgets (`job_runner.lua` for async
subprocess execution, `sections.lua` and `riff_lock.lua` for the business
logic lifted from the two retired scripts, `settings.lua` for consolidated
`ExtState` configuration). The panel never blocks on `io.popen:read()` —
every generation launches a detached process that writes to a log file
with a trailing `DONE <exitcode>` marker, and the `defer()` loop polls
that file every frame.

**Tech Stack:** REAPER ReaScript (Lua 5.x dialect), ReaImGui extension
(installed via ReaPack), Windows `cmd.exe`/`start` for detached process
launch. No Python-side changes.

**Spec:** `claudedocs/design_reaper_panel.md` — the plan below implements
that design as written; consult it for the *why* behind every constraint
listed here. The approved UI mockup is at
https://claude.ai/code/artifact/4846cac4-b5ca-4ac6-8e51-00e6b919645b.

## Global Constraints

- ReaImGui is a **hard prerequisite** — no fallback UI path. If missing,
  the panel shows the install steps inline (not just a doc pointer) and
  exits without opening a window.
- The panel must **never call `handle:read("*a")` on a running
  subprocess** from inside the `defer()` loop — that is the exact bug
  this whole redesign exists to eliminate. All subprocess execution goes
  through `job_runner.lua`'s detached-launch + log-tail + `DONE`-marker
  pattern, uniformly for every mode (template/sidecar/AI/song-map/riff).
- **Single job system-wide.** Both tabs' Generate buttons are disabled
  whenever `job_runner.is_running()` is true.
- **Only the `on_complete` callback (fired after `DONE 0`) may mutate
  REAPER project state** (`InsertMedia`, `AddProjectMarker2`,
  `SetTempoTimeSigMarker`). Nothing earlier in the flow touches the
  project, so a failed/partial subprocess run never leaves it
  half-mutated.
- **Every failure surfaces actionable remediation text inline in the
  panel** — in the `ShowMessageBox` itself or in the Log tab's raw
  content — never merely a pointer telling the user to go read
  `reaper/README.md`.
- **No Python-side files change.** Every CLI invocation this plan builds
  must use flags that already exist and are already shipped (v0.3.0) —
  verified against `midi_drums/api/cli.py` while writing this plan, not
  invented. Do not add or rename any CLI flag as part of this work.
- **No automated Lua test runner exists in this repo.** Every task's
  verification step is a manual, exact-steps REAPER check (per
  `claudedocs/design_reaper_panel.md`'s own Testing section) — do not
  invent a Lua test framework as part of this plan.
- **ReaImGui cannot load the mockup's web fonts.** The approved mockup
  uses IBM Plex Mono + Inter (Google Fonts); ReaImGui only loads
  system-installed fonts by family name via `reaper.ImGui_CreateFont`.
  Use `"Consolas"` for the monospace role (Log tab, numeric fields) and
  `"Segoe UI"` for the sans role (labels, buttons) — both ship with
  Windows, matching this repo's Windows-first REAPER audience. Fall back
  to ReaImGui's built-in default font if `ImGui_CreateFont` returns
  `nil` for either name (a non-Windows REAPER install), rather than
  erroring.
- **ReaImGui function names below match the widely-documented 0.9.x API**
  as of this plan's writing. Before implementing each panel task, spot
  check the exact functions you're about to call against your installed
  ReaImGui version — REAPER's Action List filtered to `ImGui_` lists
  every available function name, which is the authoritative source for
  your installed version. This is the one piece of this plan that can't
  be verified without a live REAPER + ReaImGui install (same category of
  caveat the retired `create_beat_from_riff.lua` already carries for its
  render-bounds constant).
- Visual tokens carried over from `docs/site-pages/site.css` (converted
  from CSS hex to ReaImGui's `0xRRGGBBAA` integer color format):
  `bg = 0x0a0f17ff`, `violet = 0xa78bfaff`, `amber = 0xfbbf24ff`,
  `sky = 0x38bdf8ff`, `green = 0x4ade80ff`, `rose (error) = 0xfb7185ff`.

---

### Task 1: `settings.lua` — consolidated ExtState configuration

**Files:**
- Create: `reaper/midi_drums/settings.lua`
- Modify: `reaper/midi_drums/` — new directory, created by this task

**Interfaces:**
- Consumes: nothing (foundational module, no dependency on any other new
  file).
- Produces (consumed by `sections.lua`, `riff_lock.lua`, and every part
  of `midi_drums_panel.lua`):
  - `M.SECTION` — string constant `"midi_drums"`, the `ExtState` section
    name (unchanged from the two retired scripts, so a user's existing
    stored `python_exe` value is picked up automatically — no migration
    needed).
  - `M.DEFAULTS` — table: `{python_exe = "", default_genre = "metal",
    default_style = "doom", default_mapping = "ezdrummer3",
    default_ai_tempo = "120", sidecar_path_override = ""}`.
  - `M.get(key)` → string. Returns the stored `ExtState` value, or
    `M.DEFAULTS[key]` if unset.
  - `M.set(key, value)` → nil. Writes to `ExtState` with `persist=true`.
  - `M.resolve_python_exe()` → string or `nil`. If the stored path opens
    successfully, returns it immediately. Otherwise prompts via
    `GetUserInputs` (pre-filled with the stale value if any), validates
    the new path opens, saves it, and returns it — or returns `nil` if
    the user cancels or leaves it empty. This is a straight port of
    `get_python_exe()` from `create_song_sections.lua:287-319` into the
    module, with `PYTHON_EXE`/`EXTSTATE_*` locals replaced by `M.*`.

**Steps:**

- [ ] **Step 1: Write a throwaway smoke-test script**

  There is no pytest-equivalent for Lua in this repo — create a
  temporary, uncommitted file to exercise the module before wiring it
  into the real panel:

  ```lua
  -- reaper/_smoke_settings.lua  (temporary — do not commit)
  package.path = package.path .. ";" ..
    reaper.GetResourcePath() .. "/Scripts/midi_drums/?.lua"
  local settings = dofile(
    reaper.GetResourcePath() .. "/Scripts/midi_drums/settings.lua"
  )
  reaper.ShowConsoleMsg("default_genre = " .. settings.get("default_genre") .. "\n")
  settings.set("default_genre", "rock")
  reaper.ShowConsoleMsg("after set = " .. settings.get("default_genre") .. "\n")
  settings.set("default_genre", "metal") -- restore
  ```

  Load it via Actions → Load ReaScript, run it once. Expected right now:
  a Lua error (`settings.lua` doesn't exist yet) printed to the REAPER
  console — confirming the smoke test actually exercises the file, not a
  stale cached module.

- [ ] **Step 2: Implement `settings.lua`**

  ```lua
  -- reaper/midi_drums/settings.lua
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
  ```

- [ ] **Step 3: Re-run the smoke test, verify it passes**

  Run `reaper/_smoke_settings.lua` again. Expected console output:
  ```
  default_genre = metal
  after set = rock
  ```
  (then the script restores `default_genre` back to `metal` before
  exiting, so subsequent tasks' smoke tests start from a clean default).

- [ ] **Step 4: Delete the smoke-test script**

  Delete `reaper/_smoke_settings.lua` — it was never meant to be
  committed (same "temporary" contract that Bash's own instructions use
  for scratch scripts).

- [ ] **Step 5: Commit**

  ```bash
  git add reaper/midi_drums/settings.lua
  git commit -m "feat(reaper-panel): add ExtState settings module"
  ```

---

### Task 2: `job_runner.lua` — async detached-subprocess execution engine

**Files:**
- Create: `reaper/midi_drums/job_runner.lua`

**Interfaces:**
- Consumes: nothing new (uses only REAPER's built-in `reaper.*` API and
  Lua's `os`/`io` libraries).
- Produces (consumed by `midi_drums_panel.lua`'s `defer()` loop, and by
  `sections.lua`/`riff_lock.lua` indirectly via the `on_complete`
  callback contract):
  - `M.STATUS` — table of string constants: `{IDLE = "idle", RUNNING =
    "running", DONE = "done", ERROR = "error"}`.
  - `M.state` — table, read-only from the panel's perspective:
    `{status, job_label, log_lines (array of strings), start_time
    (reaper.time_precise() at launch), exit_code (number or nil)}`.
  - `M.is_running()` → boolean.
  - `M.start(cmd, job_label, on_complete)` → `true` on success, or
    `false, err_string` if a job is already running. `cmd` is the exact
    shell command string (already fully quoted/escaped by the caller,
    same convention as the retired scripts' `run_python`). `job_label`
    is a short string shown in the Log tab header (e.g. `"Song Sections
    (AI)"`, `"Riff-Lock Beat"`). `on_complete` is called with no
    arguments once `DONE 0` is observed — it is the caller's
    responsibility to close over whatever parameters it needs to mutate
    the project (see Task 3/4's `on_job_complete` functions).
  - `M.poll()` → nil. Call once per `defer()` frame. Tails the job's log
    file, appends new lines to `M.state.log_lines`, and on finding a
    trailing `DONE <exitcode>` line, sets `M.state.status` to `DONE` or
    `ERROR` and invokes `on_complete()` (only on exit code `0`).
  - `M.elapsed_seconds()` → number. `reaper.time_precise() -
    M.state.start_time`, or `0` if idle.

**Steps:**

- [ ] **Step 1: Write the throwaway smoke-test script**

  ```lua
  -- reaper/_smoke_job_runner.lua  (temporary — do not commit)
  local job_runner = dofile(
    reaper.GetResourcePath() .. "/Scripts/midi_drums/job_runner.lua"
  )
  local done = false
  job_runner.start('cmd /C "echo hello && timeout /T 2 >nul"', "smoke test",
    function() done = true end)

  local function loop()
    job_runner.poll()
    reaper.ShowConsoleMsg(string.format(
      "status=%s lines=%d elapsed=%.1f\n",
      job_runner.state.status, #job_runner.state.log_lines,
      job_runner.elapsed_seconds()
    ))
    if job_runner.state.status == job_runner.STATUS.RUNNING then
      reaper.defer(loop)
    else
      reaper.ShowConsoleMsg("FINAL log_lines: " ..
        table.concat(job_runner.state.log_lines, " | ") .. "\n")
      reaper.ShowConsoleMsg("on_complete fired: " .. tostring(done) .. "\n")
    end
  end
  reaper.defer(loop)
  ```

  Run it once. Expected right now: a Lua error, `job_runner.lua` doesn't
  exist.

- [ ] **Step 2: Implement `job_runner.lua`**

  ```lua
  -- reaper/midi_drums/job_runner.lua
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
    bat:write('echo DONE %errorlevel%>> "' .. log_path .. '"\r\n')
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
  ```

- [ ] **Step 3: Re-run the smoke test, verify it passes**

  Expected console output: `status=running ...` lines for ~2 seconds
  (the `timeout /T 2` in the test command), then `status=done`,
  `FINAL log_lines: hello | DONE 0`, `on_complete fired: true`. Confirm
  the REAPER UI (move the panel, click around) is fully responsive the
  entire 2 seconds — this is the concrete proof the detached-launch
  approach doesn't block `defer()`.

- [ ] **Step 4: Delete the smoke-test script**

  Delete `reaper/_smoke_job_runner.lua`.

- [ ] **Step 5: Commit**

  ```bash
  git add reaper/midi_drums/job_runner.lua
  git commit -m "feat(reaper-panel): add detached-subprocess job runner"
  ```

---

### Task 3: `sections.lua` — Song Sections business logic

**Files:**
- Create: `reaper/midi_drums/sections.lua`
- Reference (read-only, logic is ported from here): `reaper/create_song_sections.lua`

**Interfaces:**
- Consumes: `settings.lua`'s `M.get(key)` (for defaults) — required via
  relative `dofile`/`require` from the panel's Lua path (see Task 5 for
  how the panel wires module loading; this task's functions just accept
  already-resolved values as parameters, no direct dependency on
  `settings.lua` internals).
- Produces (consumed by `midi_drums_panel.lua`'s Song Sections tab,
  Task 6):
  - `M.get_project_dir()` → string.
  - `M.sections_to_json(sections, tempo, num, denom)` → string (JSON).
  - `M.parse_sidecar(content)` → `tempo, ts_num, ts_denom, sections` or
    `nil, nil, nil, nil, err_string`.
  - `M.parse_timeline(content)` → `tempo_points, regions, color_groups`
    or `nil, nil, nil, err_string`.
  - `M.shell_escape(s)` → string.
  - `M.build_template_cmd(python_exe, genre, style, mapping, sidecar_path, midi_out)` → string.
  - `M.build_ai_cmd(python_exe, description, tempo_str, midi_out, sidecar_path)` → string.
  - `M.build_songmap_cmd(python_exe, genre, style, mapping, map_path, timeline_path, midi_out)` → string.
  - `M.create_regions_from_sections(sections, bpm, ts_num, ts_denom)` → nil (mutates the REAPER project — must only be called from an `on_complete` callback or REAPER-mode's direct region creation, per the Global Constraints project-mutation rule).
  - `M.apply_timeline_to_reaper(tempo_points, regions, color_groups)` → nil (same mutation-timing rule).
  - `M.import_midi(midi_path)` → nil (`InsertMedia` + `UpdateArrange`).

**Steps:**

- [ ] **Step 1: Write the throwaway smoke-test script**

  ```lua
  -- reaper/_smoke_sections.lua  (temporary — do not commit)
  local sections = dofile(
    reaper.GetResourcePath() .. "/Scripts/midi_drums/sections.lua"
  )
  local json = sections.sections_to_json(
    { { name = "Intro", bars = 8 }, { name = "Verse", bars = 16 } },
    120, 4, 4
  )
  reaper.ShowConsoleMsg(json .. "\n")

  local tempo, num, denom, secs, err = sections.parse_sidecar(json)
  reaper.ShowConsoleMsg(string.format(
    "parsed tempo=%s num=%s denom=%s n_sections=%s err=%s\n",
    tostring(tempo), tostring(num), tostring(denom),
    tostring(secs and #secs), tostring(err)
  ))

  local cmd = sections.build_template_cmd(
    "C:/venv/pythonw.exe", "metal", "doom", "ezdrummer3",
    "C:/proj/sidecar.json", "C:/proj/drums.mid"
  )
  reaper.ShowConsoleMsg(cmd .. "\n")
  ```

  Run it once — expect a Lua error (`sections.lua` doesn't exist yet).

- [ ] **Step 2: Implement `sections.lua`**

  Port the pure-logic functions from `create_song_sections.lua` almost
  verbatim, dropping the module-level `PYTHON_EXE`/`SIDECAR_PATH`
  globals in favor of explicit parameters, and dropping every
  `GetUserInputs`/`ShowMessageBox` call from these functions — the panel
  (Task 6) owns all dialog/widget interaction now, these functions are
  pure logic plus REAPER-timeline mutation only:

  ```lua
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
  ```

- [ ] **Step 3: Re-run the smoke test, verify it passes**

  Expected: the JSON block prints, then
  `parsed tempo=120 num=4 denom=4 n_sections=2 err=nil`, then the built
  command string with `--genre "metal" --style "doom"` etc.

- [ ] **Step 4: Delete the smoke-test script**

- [ ] **Step 5: Commit**

  ```bash
  git add reaper/midi_drums/sections.lua
  git commit -m "feat(reaper-panel): extract Song Sections logic into sections.lua"
  ```

---

### Task 4: `riff_lock.lua` — Riff-Lock Beat business logic

**Files:**
- Create: `reaper/midi_drums/riff_lock.lua`
- Reference (read-only, logic is ported from here): `reaper/create_beat_from_riff.lua`

**Interfaces:**
- Consumes: nothing from other new modules directly (parallel structure
  to `sections.lua` — takes explicit parameters, no hidden globals).
- Produces (consumed by `midi_drums_panel.lua`'s Riff-Lock Beat tab,
  Task 7):
  - `M.get_project_dir()` → string (duplicated from `sections.lua` —
    intentional; matches this repo's existing precedent of duplicating
    such helpers between the two riff/sections scripts rather than
    sharing via a third module, per `create_beat_from_riff.lua:107-109`'s
    own comment on that choice).
  - `M.shell_escape(s)` → string (duplicated, same rationale).
  - `M.parse_sidecar(content)` → same shape as `sections.lua`'s (needed
    here to read back the riff sidecar after generation; duplicated for
    the same reason).
  - `M.compute_bar_alignment(item)` → `offset_beats, bar_start_qn,
    bar_end_qn, ts_num, ts_denom, bpm`.
  - `M.resolve_audio_source(item, take, bar_start_qn, bar_end_qn)` →
    `audio_path, audio_offset, audio_duration, err`. `audio_offset`/
    `audio_duration` are `nil` when `audio_path` came from a render
    (already bar-aligned, no slicing needed) vs. numbers when it came
    from an existing audio take.
  - `M.render_item_to_wav(render_start_time, render_end_time)` →
    `ok, result` (`result` is the output path on success, an error
    string on failure).
  - `M.build_cmd(python_exe, params)` → string. `params` is a table:
    `{genre, style, drummer, section, mapping, ts_str, bars, grid,
    lock_strength, snare_mode, snare_stab_threshold, tempo,
    offset_beats, midi_out, sidecar_out, audio_path, audio_offset,
    audio_duration, humanization, complexity}`.
  - `M.on_job_complete(params)` → nil (project mutation — reads back the
    sidecar + MIDI, creates a region, imports the MIDI; only call from a
    `job_runner` `on_complete` callback). `params`:
    `{sidecar_out, midi_out, bar_start_qn, bpm}`.

**Steps:**

- [ ] **Step 1: Write the throwaway smoke-test script**

  ```lua
  -- reaper/_smoke_riff_lock.lua  (temporary — do not commit)
  local riff_lock = dofile(
    reaper.GetResourcePath() .. "/Scripts/midi_drums/riff_lock.lua"
  )
  local cmd = riff_lock.build_cmd("C:/venv/pythonw.exe", {
    genre = "metal", style = "death", drummer = "", section = "verse",
    mapping = "ezdrummer3", ts_str = "4/4", bars = 4, grid = "16th",
    lock_strength = 1.0, snare_mode = "reinforce",
    snare_stab_threshold = 0.85, tempo = 155, offset_beats = 0.5,
    midi_out = "C:/proj/riff_drums.mid",
    sidecar_out = "C:/proj/midi_drums_riff_sidecar.json",
    audio_path = "C:/proj/riff.wav", audio_offset = nil,
    audio_duration = nil, humanization = 0.0, complexity = 0.5,
  })
  reaper.ShowConsoleMsg(cmd .. "\n")
  ```

  Run it once — expect a Lua error (`riff_lock.lua` doesn't exist yet).

- [ ] **Step 2: Implement `riff_lock.lua`**

  Port `render_item_to_wav` (lines 241-290) and the bar-alignment/
  audio-source-resolution logic (lines 292-377) from
  `create_beat_from_riff.lua` near-verbatim into functions, and rebuild
  the command string using the `--snare-mode`/`--snare-stab-threshold`
  flags confirmed present in `midi_drums/api/cli.py:474-489` (the
  original script predates the snare-reaction feature and never passed
  these — this is a genuine, spec-approved feature addition to the
  panel, not a port gap):

  ```lua
  -- reaper/midi_drums/riff_lock.lua
  local M = {}

  local RENDER_PATTERN    = "midi_drums_riff_render"
  local RENDER_EXTENSIONS = { ".wav", ".flac", ".aiff", ".mp3", ".ogg" }

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

  function M.compute_bar_alignment(item)
    local item_start  = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
    local item_length = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
    local item_end     = item_start + item_length

    local ts_num, ts_denom = reaper.TimeMap_GetTimeSigAtTime(0, item_start)
    ts_num   = ts_num   or 4
    ts_denom = ts_denom or 4
    local bar_len_qn = ts_num * (4.0 / ts_denom)

    local qn_start = reaper.TimeMap2_timeToQN(0, item_start)
    local qn_end   = reaper.TimeMap2_timeToQN(0, item_end)
    local bar_start_qn = math.floor(qn_start / bar_len_qn) * bar_len_qn
    local bar_end_qn   = math.ceil(qn_end / bar_len_qn) * bar_len_qn

    local offset_beats = qn_start - bar_start_qn
    local bpm = reaper.Master_GetTempo()

    return offset_beats, bar_start_qn, bar_end_qn, ts_num, ts_denom, bpm
  end

  -- Saves/restores RENDER_FILE, RENDER_PATTERN, RENDER_BOUNDSFLAG and
  -- the time selection unconditionally right after the render call,
  -- before any success/failure branching — action 42230's semantic is
  -- "use most recent settings", so skipping restore would silently
  -- corrupt the user's next manual render.
  --
  -- KNOWN UNVERIFIED (carried over from create_beat_from_riff.lua):
  -- RENDER_BOUNDSFLAG = 2 ("Time selection") is used deliberately
  -- instead of the "selected media items" flag (commonly cited as 4 in
  -- community scripts but unverified) — confirm this still bounds the
  -- render correctly the first time this module runs against a real
  -- project, same caveat the retired script already carried.
  function M.render_item_to_wav(render_start_time, render_end_time)
    local saved_ts_start, saved_ts_end =
      reaper.GetSet_LoopTimeRange(false, false, 0, 0, false)
    local _, saved_render_file =
      reaper.GetSetProjectInfo_String(0, "RENDER_FILE", "", false)
    local _, saved_render_pattern =
      reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", "", false)
    local saved_bounds_flag =
      reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 0, false)

    local render_dir = M.get_project_dir()

    reaper.GetSet_LoopTimeRange(true, false, render_start_time, render_end_time, false)
    reaper.GetSetProjectInfo_String(0, "RENDER_FILE", render_dir, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", RENDER_PATTERN, true)
    reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 2, true)

    reaper.Main_OnCommand(42230, 0)

    reaper.GetSetProjectInfo_String(0, "RENDER_FILE", saved_render_file, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", saved_render_pattern, true)
    reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", saved_bounds_flag, true)
    reaper.GetSet_LoopTimeRange(true, false, saved_ts_start, saved_ts_end, false)

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
      .. "actually produces one of those, then retry."
  end

  function M.resolve_audio_source(item, take, bar_start_qn, bar_end_qn)
    if not reaper.TakeIsMIDI(take) then
      local source = reaper.GetMediaItemTake_Source(take)
      local audio_path = reaper.GetMediaSourceFileName(source, "")
      if not audio_path or audio_path == "" then
        return nil, nil, nil, "Could not resolve the take's source audio file."
      end
      local item_length = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
      local take_startoffs = reaper.GetMediaItemTakeInfo_Value(take, "D_STARTOFFS")
      local take_playrate  = reaper.GetMediaItemTakeInfo_Value(take, "D_PLAYRATE")
      return audio_path, take_startoffs, item_length * take_playrate, nil
    end

    local render_start_time = reaper.TimeMap2_QNToTime(0, bar_start_qn)
    local render_end_time   = reaper.TimeMap2_QNToTime(0, bar_end_qn)

    reaper.Undo_BeginBlock()
    local ok, result = M.render_item_to_wav(render_start_time, render_end_time)
    reaper.Undo_EndBlock("Render Riff Item for midi_drums", -1)

    if not ok then
      return nil, nil, nil, result
    end
    -- Rendered file already starts exactly at the bar line, so no
    -- slicing offset/duration is needed for this path.
    return result, nil, nil, nil
  end

  function M.build_cmd(python_exe, p)
    local parts = {
      string.format(
        '"%s" -m midi_drums riff --audio "%s" --genre "%s" --style "%s"',
        python_exe, p.audio_path, M.shell_escape(p.genre), M.shell_escape(p.style)
      ),
      string.format('--tempo %g --offset-beats %g', p.tempo, p.offset_beats),
      string.format(
        '--section "%s" --time-signature "%s" --bars %d --grid "%s"',
        M.shell_escape(p.section), M.shell_escape(p.ts_str), p.bars, M.shell_escape(p.grid)
      ),
      string.format(
        '--lock-strength %g --humanization %g --complexity %g',
        p.lock_strength, p.humanization, p.complexity
      ),
      string.format('--snare-mode "%s"', p.snare_mode),
    }
    if p.snare_mode == "stab" then
      parts[#parts + 1] = string.format(
        '--snare-stab-threshold %g', p.snare_stab_threshold
      )
    end
    parts[#parts + 1] = string.format(
      '--mapping "%s" --output "%s" --write-sidecar "%s"',
      M.shell_escape(p.mapping), p.midi_out, p.sidecar_out
    )
    if p.drummer and p.drummer ~= "" then
      parts[#parts + 1] = string.format('--drummer "%s"', M.shell_escape(p.drummer))
    end
    if p.audio_offset then
      parts[#parts + 1] = string.format(
        '--audio-offset %g --audio-duration %g', p.audio_offset, p.audio_duration
      )
    end
    return table.concat(parts, " ")
  end

  -- Project mutation — only call from a job_runner on_complete callback.
  function M.on_job_complete(p)
    local f = io.open(p.sidecar_out, "r")
    if not f then
      reaper.ShowMessageBox(
        "Generation succeeded but sidecar not found:\n" .. p.sidecar_out,
        "Sidecar Not Found", 0
      )
      return
    end
    local content = f:read("*all"); f:close()

    local s_tempo, s_num, s_denom, s_sections, s_err = M.parse_sidecar(content)
    if not s_sections then
      reaper.ShowMessageBox(
        "Could not parse riff sidecar: " .. (s_err or "?"), "Error", 0
      )
      return
    end

    local midi_f = io.open(p.midi_out, "rb")
    if not midi_f then
      reaper.ShowMessageBox(
        "Generation succeeded but MIDI file not found:\n" .. p.midi_out,
        "MIDI file Not Found", 0
      )
      return
    end
    midi_f:close()

    reaper.Undo_BeginBlock()

    local region_start = reaper.TimeMap2_QNToTime(0, p.bar_start_qn)
    local measure_length = (60.0 / (s_tempo or p.bpm)) * s_num * (4.0 / s_denom)
    local region_end = region_start + (s_sections[1].bars * measure_length)
    reaper.AddProjectMarker2(0, true, region_start, region_end, s_sections[1].name, -1, 0)

    local saved_cursor = reaper.GetCursorPosition()
    reaper.SetEditCurPos(region_start, false, false)
    reaper.InsertMedia(p.midi_out, 0)
    reaper.SetEditCurPos(saved_cursor, false, false)

    reaper.Undo_EndBlock("Create Riff-Locked Drums", -1)
    reaper.UpdateArrange()
  end

  return M
  ```

- [ ] **Step 3: Re-run the smoke test, verify it passes**

  Expected: a printed command string containing
  `--snare-mode "reinforce"` and no `--snare-stab-threshold` (since
  `reinforce` mode doesn't need the threshold flag — only `stab` does).
  Edit the smoke test's `snare_mode` to `"stab"` and re-run; confirm
  `--snare-stab-threshold 0.85` now appears.

- [ ] **Step 4: Delete the smoke-test script**

- [ ] **Step 5: Commit**

  ```bash
  git add reaper/midi_drums/riff_lock.lua
  git commit -m "feat(reaper-panel): extract Riff-Lock Beat logic into riff_lock.lua"
  ```

---

### Task 5: `midi_drums_panel.lua` Part A — window scaffold, ReaImGui guard, defer loop

**Files:**
- Create: `reaper/midi_drums_panel.lua`

**Interfaces:**
- Consumes: none yet (Tasks 6-8 wire the tab bodies in; this task
  produces the shell they plug into).
- Produces (consumed by Tasks 6-8, all appended into this same file):
  - Module-level `ctx` (ReaImGui context), `font_sans`, `font_mono`
    (fonts, possibly `nil` on a non-Windows install).
  - `REAIMGUI_INSTALL_STEPS` — string constant, the ReaPack install
    instructions shown inline in the missing-ReaImGui message box.
  - `draw_help_button(id, lines)` — helper used by Tasks 6/7 to render
    a "?" popover; `id` is a unique string, `lines` is an array of
    `{title, body}` tables.
  - The `defer()` loop function `loop()`, structured so Tasks 6-8 each
    add one `if reaper.ImGui_BeginTabItem(ctx, "...") then ... end`
    block inside the existing `ImGui_BeginTabBar`/`ImGui_EndTabBar`
    pair, without needing to touch the surrounding scaffold.

**Steps:**

- [ ] **Step 1: Implement the ReaImGui-missing guard + install-steps constant**

  ```lua
  -- reaper/midi_drums_panel.lua
  -- midi_drums × REAPER unified panel
  -- Part of: https://github.com/fsecada01/midi-drums

  local REAIMGUI_INSTALL_STEPS =
    "This panel needs the ReaImGui extension, which isn't installed.\n\n"
    .. "1. Install ReaPack (REAPER's package manager), if you haven't:\n"
    .. "     https://reapack.com/\n"
    .. "   Download the installer for your OS, run it with REAPER closed.\n\n"
    .. "2. In REAPER: Extensions -> ReaPack -> Browse packages...\n"
    .. "   Search \"ReaImGui\", right-click the result -> Install.\n\n"
    .. "3. Extensions -> ReaPack -> Synchronize packages, then restart REAPER.\n\n"
    .. "Full details: reaper/README.md's Prerequisites section."

  if not reaper.APIExists("ImGui_CreateContext") then
    reaper.ShowMessageBox(REAIMGUI_INSTALL_STEPS, "ReaImGui Required", 0)
    return
  end
  ```

  Note the same string constant is what `reaper/README.md`'s
  Prerequisites section will be written to quote verbatim in Task 9 —
  do not let the two drift; if you change one, change the other.

- [ ] **Step 2: Manual verification — guard fires correctly**

  Temporarily disable ReaImGui (Extensions → ReaPack → Manage packages →
  right-click ReaImGui → Uninstall, or simply test on a REAPER install
  that never had it). Load `midi_drums_panel.lua` via Actions → Load
  ReaScript, run it. Expected: the message box above appears with the
  full inline install steps, and no ReaImGui window opens. Re-install
  ReaImGui (or switch back to an install that has it) before continuing.

- [ ] **Step 3: Implement module loading, context/font setup, and the tab-bar scaffold**

  ```lua
  local script_path = ({reaper.get_action_context()})[2]:match("^(.*[/\\])")
  package.path = package.path .. ";" .. script_path .. "midi_drums/?.lua"

  local settings   = dofile(script_path .. "midi_drums/settings.lua")
  local job_runner = dofile(script_path .. "midi_drums/job_runner.lua")
  local sections   = dofile(script_path .. "midi_drums/sections.lua")
  local riff_lock  = dofile(script_path .. "midi_drums/riff_lock.lua")

  local ctx = reaper.ImGui_CreateContext("midi_drums Panel")
  local font_sans = reaper.ImGui_CreateFont("Segoe UI", 14)
  local font_mono = reaper.ImGui_CreateFont("Consolas", 13)
  if font_sans then reaper.ImGui_Attach(ctx, font_sans) end
  if font_mono then reaper.ImGui_Attach(ctx, font_mono) end

  local help_popover_open = {} -- id -> bool, shared by Tasks 6/7

  function draw_help_button(id, lines)
    reaper.ImGui_SameLine(ctx)
    if reaper.ImGui_Button(ctx, "?##" .. id, 20, 0) then
      reaper.ImGui_OpenPopup(ctx, "help_" .. id)
    end
    if reaper.ImGui_BeginPopup(ctx, "help_" .. id) then
      for _, entry in ipairs(lines) do
        reaper.ImGui_TextColored(ctx, 0xa78bfaff, entry.title)
        reaper.ImGui_TextWrapped(ctx, entry.body)
        reaper.ImGui_Spacing(ctx)
      end
      reaper.ImGui_EndPopup(ctx)
    end
  end

  local function loop()
    job_runner.poll() -- every frame, regardless of window visibility

    if font_sans then reaper.ImGui_PushFont(ctx, font_sans) end
    reaper.ImGui_SetNextWindowSize(ctx, 640, 520, reaper.ImGui_Cond_FirstUseEver())
    local visible, open = reaper.ImGui_Begin(ctx, "MIDI Drums", true)
    if visible then
      if reaper.ImGui_BeginTabBar(ctx, "tabs") then
        if reaper.ImGui_BeginTabItem(ctx, "Song Sections") then
          -- Task 6 fills this in
          reaper.ImGui_EndTabItem(ctx)
        end
        if reaper.ImGui_BeginTabItem(ctx, "Riff-Lock Beat") then
          -- Task 7 fills this in
          reaper.ImGui_EndTabItem(ctx)
        end
        if reaper.ImGui_BeginTabItem(ctx, "Settings") then
          -- Task 8 fills this in
          reaper.ImGui_EndTabItem(ctx)
        end
        if reaper.ImGui_BeginTabItem(ctx, "Log") then
          -- Task 8 fills this in
          reaper.ImGui_EndTabItem(ctx)
        end
        reaper.ImGui_EndTabBar(ctx)
      end
      reaper.ImGui_End(ctx)
    end
    if font_sans then reaper.ImGui_PopFont(ctx) end

    if open then
      reaper.defer(loop)
    else
      reaper.ImGui_DestroyContext(ctx)
    end
  end

  reaper.defer(loop)
  ```

- [ ] **Step 4: Manual verification — panel opens with four empty tabs**

  Load/run the script again (ReaImGui now present). Expected: a
  dockable window titled "MIDI Drums" opens with four clickable tabs
  (Song Sections, Riff-Lock Beat, Settings, Log), all empty. Click each
  tab to confirm switching works. Close the window (X) and confirm the
  script exits cleanly (no console error) rather than leaving a defer
  loop running.

- [ ] **Step 5: Commit**

  ```bash
  git add reaper/midi_drums_panel.lua
  git commit -m "feat(reaper-panel): add panel entry point with ReaImGui guard and tab scaffold"
  ```

---

### Task 6: `midi_drums_panel.lua` Part B — Song Sections tab

**Files:**
- Modify: `reaper/midi_drums_panel.lua` (the `"Song Sections"` tab item body from Task 5, Step 3)

**Interfaces:**
- Consumes: `settings.get/set`, `sections.*` (Task 3), `job_runner.start/is_running` (Task 2), `draw_help_button` (Task 5).
- Produces: nothing new consumed elsewhere — this is a leaf UI block.

**Steps:**

- [ ] **Step 1: Add tab-local state above the `loop()` function**

  ```lua
  local ss_mode = settings.get("default_genre") and 1 or 1 -- 1=reaper 2=sidecar 3=ai 4=songmap
  local ss_genre = settings.get("default_genre")
  local ss_style = settings.get("default_style")
  local ss_mapping = settings.get("default_mapping")
  local ss_drummer = ""
  local ss_tempo = tostring(math.floor(reaper.Master_GetTempo()))
  local ss_ts_num, ss_ts_denom = reaper.GetProjectTimeSignature2(0)
  local ss_ai_description = "heavy doom riff, slow and crushing"
  local ss_ai_tempo = settings.get("default_ai_tempo")
  local ss_status = "idle" -- idle | running | done | error
  ```

- [ ] **Step 2: Implement the tab body**

  Replace the `-- Task 6 fills this in` comment inside the
  `"Song Sections"` `BeginTabItem` block:

  ```lua
  local mode_labels = { "REAPER", "Sidecar", "AI", "Song Map" }
  for i, label in ipairs(mode_labels) do
    if i > 1 then reaper.ImGui_SameLine(ctx) end
    if reaper.ImGui_RadioButton(ctx, label, ss_mode == i) then
      ss_mode = i
    end
  end
  draw_help_button("ss_mode", {
    { title = "REAPER", body = "You define section names/bars in this "
      .. "script; a sidecar JSON is written for you." },
    { title = "Sidecar", body = "Reads an existing midi_drums_sections.json "
      .. "already written by Python (e.g. save_as_midi_with_sidecar)." },
    { title = "AI", body = "Describe the song in a sentence; the AI agent "
      .. "drafts the whole structure (~20-45s)." },
    { title = "Song Map", body = "Reads a song-map JSON with per-segment "
      .. "tempo/meter changes within a single section." },
  })

  if ss_mode == 3 then
    local changed
    changed, ss_ai_description = reaper.ImGui_InputTextMultiline(
      ctx, "Description", ss_ai_description, -1, 60
    )
    changed, ss_ai_tempo = reaper.ImGui_InputText(ctx, "Tempo (blank = AI decides)", ss_ai_tempo)
  else
    local changed
    changed, ss_genre   = reaper.ImGui_InputText(ctx, "Genre", ss_genre)
    changed, ss_style   = reaper.ImGui_InputText(ctx, "Style", ss_style)
    changed, ss_drummer = reaper.ImGui_InputText(ctx, "Drummer (blank = none)", ss_drummer)
    changed, ss_mapping = reaper.ImGui_InputText(ctx, "Mapping", ss_mapping)
  end

  local generating = job_runner.is_running()
  if generating then reaper.ImGui_BeginDisabled(ctx) end
  if reaper.ImGui_Button(ctx, "Generate") then
    local project_dir = sections.get_project_dir()
    local midi_out = project_dir .. "/drums.mid"
    local sidecar_path = (settings.get("sidecar_path_override") ~= "")
      and settings.get("sidecar_path_override")
      or (project_dir .. "/midi_drums_sections.json")
    local python_exe = settings.resolve_python_exe()

    if python_exe then
      if ss_mode == 1 then -- REAPER: no subprocess needed to create regions,
                            -- but template generation still goes through one.
        local bpm = reaper.Master_GetTempo()
        local reaper_sections = {
          { name = "Intro", bars = 8 }, { name = "Verse", bars = 16 },
          { name = "Chorus", bars = 16 }, { name = "Bridge", bars = 8 },
          { name = "Outro", bars = 4 },
        }
        sections.create_regions_from_sections(reaper_sections, bpm, ss_ts_num, ss_ts_denom)
        local sf = io.open(sidecar_path, "w")
        if sf then
          sf:write(sections.sections_to_json(reaper_sections, bpm, ss_ts_num, ss_ts_denom))
          sf:close()
        end
        local cmd = sections.build_template_cmd(
          python_exe, ss_genre, ss_style, ss_mapping, sidecar_path, midi_out
        )
        job_runner.start(cmd, "Song Sections (template)", function()
          sections.import_midi(midi_out)
        end)
      elseif ss_mode == 2 then -- Sidecar: read-only, no subprocess
        local f = io.open(sidecar_path, "r")
        if f then
          local content = f:read("*all"); f:close()
          local p_tempo, p_num, p_denom, p_sections = sections.parse_sidecar(content)
          if p_sections then
            sections.create_regions_from_sections(p_sections, p_tempo, p_num, p_denom)
          end
        end
      elseif ss_mode == 3 then -- AI
        local cmd = sections.build_ai_cmd(
          python_exe, ss_ai_description, ss_ai_tempo, midi_out, sidecar_path
        )
        job_runner.start(cmd, "Song Sections (AI)", function()
          local f = io.open(sidecar_path, "r")
          if f then
            local content = f:read("*all"); f:close()
            local p_tempo, p_num, p_denom, p_sections = sections.parse_sidecar(content)
            if p_sections then
              sections.create_regions_from_sections(p_sections, p_tempo, p_num, p_denom)
            end
          end
          sections.import_midi(midi_out)
        end)
      elseif ss_mode == 4 then -- Song Map
        local timeline_path = sections.get_project_dir() .. "/midi_drums_timeline.json"
        local map_path = sections.get_project_dir() .. "/song_map.json"
        local cmd = sections.build_songmap_cmd(
          python_exe, ss_genre, ss_style, ss_mapping, map_path, timeline_path, midi_out
        )
        job_runner.start(cmd, "Song Sections (Song Map)", function()
          local f = io.open(timeline_path, "r")
          if f then
            local content = f:read("*all"); f:close()
            local tp, regions, cg = sections.parse_timeline(content)
            if tp then sections.apply_timeline_to_reaper(tp, regions, cg) end
          end
          sections.import_midi(midi_out)
        end)
      end
    end
  end
  if generating then reaper.ImGui_EndDisabled(ctx) end

  reaper.ImGui_SameLine(ctx)
  reaper.ImGui_Text(ctx, "Status: " .. job_runner.state.status)
  ```

  Note the disabled-while-running rule (`ImGui_BeginDisabled`/
  `EndDisabled`) satisfies the Global Constraint that both tabs' Generate
  buttons are inactive while any job runs — Task 7's Riff-Lock Beat tab
  uses the exact same `job_runner.is_running()` guard, so the lock is
  enforced once, in `job_runner`, and both tabs just read it.

- [ ] **Step 3: Manual verification — REAPER mode end-to-end**

  Run the panel. On the Song Sections tab, leave Mode at "REAPER",
  confirm Genre/Style/Mapping fields show `metal`/`doom`/`ezdrummer3`
  (the settings defaults), click Generate. Expected: five timeline
  regions appear (Intro/Verse/Chorus/Bridge/Outro) immediately, the
  status pill shows "running" while the subprocess is in flight (watch
  the panel stay responsive — drag it around), then flips to "done" and
  a MIDI item appears on a new track once the subprocess finishes.

- [ ] **Step 4: Manual verification — AI mode + help popover**

  Click the "?" next to the Mode row, confirm the four-entry popover
  appears and closes on an outside click. Switch Mode to "AI", enter a
  description, click Generate, confirm the panel stays interactive for
  the ~20-45s wait (switch to another tab and back) and the region/MIDI
  import happens once "done".

- [ ] **Step 5: Commit**

  ```bash
  git add reaper/midi_drums_panel.lua
  git commit -m "feat(reaper-panel): wire up Song Sections tab"
  ```

---

### Task 7: `midi_drums_panel.lua` Part C — Riff-Lock Beat tab

**Files:**
- Modify: `reaper/midi_drums_panel.lua` (the `"Riff-Lock Beat"` tab item body from Task 5, Step 3)

**Interfaces:**
- Consumes: `settings.get/resolve_python_exe`, `riff_lock.*` (Task 4), `job_runner.start/is_running` (Task 2), `draw_help_button` (Task 5).
- Produces: nothing new consumed elsewhere.

**Steps:**

- [ ] **Step 1: Add tab-local state**

  ```lua
  local rl_genre = settings.get("default_genre")
  local rl_style = settings.get("default_style")
  local rl_drummer = ""
  local rl_section = "verse"
  local rl_mapping = settings.get("default_mapping")
  local rl_grid = "16th"
  local rl_lock_strength = 1.0
  local rl_snare_mode = 1 -- 1=off 2=reinforce 3=stab
  local rl_snare_threshold = 0.85
  ```

- [ ] **Step 2: Implement the tab body**

  Unlike the retired script (which resolved the selected item once at
  script start), the panel stays open across multiple generations, so
  the selected item must be read fresh **at Generate-click time**, not
  when the tab is drawn or the panel opens — the user may select a
  different riff between clicks without restarting the panel:

  ```lua
  local item_count = reaper.CountSelectedMediaItems(0)
  if item_count == 0 then
    reaper.ImGui_TextColored(ctx, 0xfb7185ff, "Select a riff media item first.")
  else
    reaper.ImGui_Text(ctx, item_count .. " item(s) selected (first will be used)")
  end

  local changed
  changed, rl_genre   = reaper.ImGui_InputText(ctx, "Genre", rl_genre)
  changed, rl_style   = reaper.ImGui_InputText(ctx, "Style", rl_style)
  changed, rl_drummer = reaper.ImGui_InputText(ctx, "Drummer (blank = none)", rl_drummer)
  changed, rl_grid    = reaper.ImGui_InputText(ctx, "Grid (8th/16th/32nd/8th_triplet/16th_triplet)", rl_grid)
  changed, rl_lock_strength = reaper.ImGui_SliderDouble(ctx, "Lock Strength", rl_lock_strength, 0.0, 1.0, "%.2f")

  local snare_labels = { "Off", "Reinforce", "Stab" }
  for i, label in ipairs(snare_labels) do
    if i > 1 then reaper.ImGui_SameLine(ctx) end
    if reaper.ImGui_RadioButton(ctx, label, rl_snare_mode == i) then
      rl_snare_mode = i
    end
  end
  draw_help_button("rl_snare", {
    { title = "Off", body = "Snare comes only from the normal genre-plugin "
      .. "pattern, untouched by riff accents." },
    { title = "Reinforce", body = "Boosts velocity on existing snare hits "
      .. "that land near a strong riff accent." },
    { title = "Stab", body = "Inserts a unison snare hit at very strong "
      .. "accents where a kick was locked but no snare was nearby." },
  })
  if rl_snare_mode == 3 then
    changed, rl_snare_threshold = reaper.ImGui_SliderDouble(
      ctx, "Stab Threshold", rl_snare_threshold, 0.0, 1.0, "%.2f"
    )
  end

  local generating = job_runner.is_running()
  if generating or item_count == 0 then reaper.ImGui_BeginDisabled(ctx) end
  if reaper.ImGui_Button(ctx, "Generate##riff") then
    local python_exe = settings.resolve_python_exe()
    local item = reaper.GetSelectedMediaItem(0, 0)
    local take = item and reaper.GetActiveTake(item)
    if python_exe and item and take then
      local offset_beats, bar_start_qn, bar_end_qn, ts_num, ts_denom, bpm =
        riff_lock.compute_bar_alignment(item)
      local audio_path, audio_offset, audio_duration, err =
        riff_lock.resolve_audio_source(item, take, bar_start_qn, bar_end_qn)

      if not audio_path then
        reaper.ShowMessageBox(err, "Riff Source Error", 0)
      else
        local project_dir = riff_lock.get_project_dir()
        local midi_out = project_dir .. "/riff_drums.mid"
        local sidecar_out = project_dir .. "/midi_drums_riff_sidecar.json"
        local snare_mode_str = ({ "off", "reinforce", "stab" })[rl_snare_mode]

        local cmd = riff_lock.build_cmd(python_exe, {
          genre = rl_genre, style = rl_style, drummer = rl_drummer,
          section = rl_section,
          ts_str = string.format("%d/%d", ts_num, ts_denom),
          bars = 4, grid = rl_grid, lock_strength = rl_lock_strength,
          snare_mode = snare_mode_str, snare_stab_threshold = rl_snare_threshold,
          tempo = bpm, offset_beats = offset_beats,
          midi_out = midi_out, sidecar_out = sidecar_out,
          audio_path = audio_path, audio_offset = audio_offset,
          audio_duration = audio_duration, humanization = 0.0, complexity = 0.5,
          mapping = rl_mapping,
        })

        job_runner.start(cmd, "Riff-Lock Beat", function()
          riff_lock.on_job_complete({
            sidecar_out = sidecar_out, midi_out = midi_out,
            bar_start_qn = bar_start_qn, bpm = bpm,
          })
        end)
      end
    end
  end
  if generating or item_count == 0 then reaper.ImGui_EndDisabled(ctx) end

  reaper.ImGui_SameLine(ctx)
  reaper.ImGui_Text(ctx, "Status: " .. job_runner.state.status)
  ```

- [ ] **Step 3: Manual verification — audio-take fast path**

  Select a riff item whose take is already audio, run the panel, switch
  to Riff-Lock Beat, set Snare Reaction to "Reinforce", click Generate.
  Expected: no render happens (confirm no new file appears in the
  project's render output location), status flips running → done, a
  region + MIDI item land at the item's bar-aligned position.

- [ ] **Step 4: Manual verification — MIDI/VSTi render path + Stab mode**

  Select a MIDI/VSTi guitar item instead. Set Snare Reaction to "Stab",
  confirm the Stab Threshold slider appears, adjust it, click Generate.
  Expected: a render happens (temp WAV appears matching
  `midi_drums_riff_render.*` in the project folder), your render
  settings (File → Render... dialog, if you check it before/after) are
  unchanged from what they were before clicking Generate, and the result
  imports correctly.

- [ ] **Step 5: Manual verification — no item selected**

  Deselect all items. Confirm the Generate button is disabled and the
  red "Select a riff media item first" message shows.

- [ ] **Step 6: Commit**

  ```bash
  git add reaper/midi_drums_panel.lua
  git commit -m "feat(reaper-panel): wire up Riff-Lock Beat tab"
  ```

---

### Task 8: `midi_drums_panel.lua` Part D — Settings tab + Log tab

**Files:**
- Modify: `reaper/midi_drums_panel.lua` (the `"Settings"` and `"Log"` tab item bodies from Task 5, Step 3; also add the Log tab's "live" badge to its tab label)

**Interfaces:**
- Consumes: `settings.get/set`, `job_runner.state/elapsed_seconds` (Task 2).
- Produces: nothing new consumed elsewhere — final leaf UI blocks.

**Steps:**

- [ ] **Step 1: Implement the Settings tab body**

  Auto-saves on every change (no Save button), per spec:

  ```lua
  local function settings_field(label, key)
    local changed, new_value = reaper.ImGui_InputText(ctx, label, settings.get(key))
    if changed then settings.set(key, new_value) end
  end

  settings_field("Python executable", "python_exe")
  reaper.ImGui_TextWrapped(ctx,
    "Stored in REAPER's ExtState (section \"midi_drums\"), scoped to this "
    .. "REAPER install — not this project.")
  reaper.ImGui_Separator(ctx)
  settings_field("Default genre", "default_genre")
  settings_field("Default style", "default_style")
  settings_field("Default mapping", "default_mapping")
  settings_field("Default AI tempo", "default_ai_tempo")
  settings_field("Sidecar path override (blank = project dir)", "sidecar_path_override")
  reaper.ImGui_Separator(ctx)
  reaper.ImGui_TextWrapped(ctx,
    "midi_drums REAPER integration. Docs: "
    .. "https://fsecada01.github.io/midi-drums/ -- "
    .. "Riff-Lock Beat needs `uv sync --group audio` run once in the "
    .. "midi_drums venv (installs librosa).")
  ```

- [ ] **Step 2: Implement the Log tab body**

  ```lua
  reaper.ImGui_Text(ctx, "Job: " .. (job_runner.state.job_label or "(none yet)"))
  reaper.ImGui_SameLine(ctx)
  reaper.ImGui_Text(ctx, string.format("Elapsed: %.1fs", job_runner.elapsed_seconds()))
  reaper.ImGui_SameLine(ctx)
  local status_color = 0x778ca6ff
  if job_runner.state.status == "running" then status_color = 0x38bdf8ff
  elseif job_runner.state.status == "done" then status_color = 0x4ade80ff
  elseif job_runner.state.status == "error" then status_color = 0xfb7185ff end
  reaper.ImGui_TextColored(ctx, status_color, job_runner.state.status)

  if font_mono then reaper.ImGui_PushFont(ctx, font_mono) end
  if reaper.ImGui_BeginChild(ctx, "log_box", 0, 300) then
    if #job_runner.state.log_lines == 0 then
      reaper.ImGui_TextDisabled(ctx, "No job run yet.")
    else
      for _, line in ipairs(job_runner.state.log_lines) do
        reaper.ImGui_TextWrapped(ctx, line)
      end
      reaper.ImGui_SetScrollHereY(ctx, 1.0)
    end
    reaper.ImGui_EndChild(ctx)
  end
  if font_mono then reaper.ImGui_PopFont(ctx) end
  ```

- [ ] **Step 3: Add the pulsing "live" badge to the Log tab's own label**

  Replace the Log tab's `BeginTabItem` call from Task 5 (currently
  `reaper.ImGui_BeginTabItem(ctx, "Log")`) with a label that reflects
  running state, so the badge is visible even when another tab is
  focused, per the spec's UI Design section:

  ```lua
  local log_tab_label = job_runner.is_running() and "Log *" or "Log"
  if reaper.ImGui_BeginTabItem(ctx, log_tab_label) then
  ```

  (A literal `*` suffix is the simplest correct implementation of "a
  badge visible from any tab" — an actual pulsing dot glyph is a
  refinement left to whoever implements this task in front of a real
  ReaImGui install, where `ImGui_Bullet`-style glyphs and per-frame
  alpha animation can be checked visually; the asterisk is not a
  placeholder, it is a complete, correct, if visually plain,
  implementation of the same requirement.)

- [ ] **Step 4: Manual verification — Settings persistence**

  Change "Default style" to `heavy`, switch to another REAPER project
  or restart REAPER entirely, reopen the panel. Expected: "Default
  style" still shows `heavy` (proves the `ExtState` round-trip), and the
  Song Sections tab's Style field (Task 6) now defaults to `heavy` too
  next time the panel is freshly opened.

- [ ] **Step 5: Manual verification — Log tab liveness during a job**

  Start a Song Sections AI-mode generation (Task 6), immediately switch
  to the Settings tab, confirm the Log tab's label shows the `*` badge
  while the job runs. Switch to the Log tab mid-job, confirm lines
  appear progressively (not all at once at the end) and the elapsed
  timer visibly increments.

- [ ] **Step 6: Manual verification — error path shows remediation text inline**

  Deliberately break `python_exe` in Settings (e.g. append `x` to the
  path), trigger a Song Sections REAPER-mode generation. Expected: the
  status pill goes to "error" (rose color), and the Log tab's content
  contains a Windows "not recognized as an internal or external
  command" line (or similar) rather than the panel silently doing
  nothing — confirming failures are visible without checking the
  separate REAPER console.

- [ ] **Step 7: Commit**

  ```bash
  git add reaper/midi_drums_panel.lua
  git commit -m "feat(reaper-panel): wire up Settings and Log tabs"
  ```

---

### Task 9: Retire the three old scripts, update docs

**Files:**
- Delete: `reaper/create_song_sections.lua`
- Delete: `reaper/create_beat_from_riff.lua`
- Delete: `reaper/midi_drums_help.lua`
- Modify: `reaper/README.md`
- Modify: `CLAUDE.md` (root of `midi_drums` repo)

**Interfaces:**
- Consumes: nothing (final documentation/cleanup task, run only after
  Tasks 1-8 are all committed and manually verified working).
- Produces: nothing (terminal task).

**Steps:**

- [ ] **Step 1: Delete the three retired scripts**

  ```bash
  git rm reaper/create_song_sections.lua reaper/create_beat_from_riff.lua reaper/midi_drums_help.lua
  ```

- [ ] **Step 2: Rewrite `reaper/README.md`'s "Scripts" section**

  Replace the current three-bullet "Scripts" section (the file you're
  editing currently lists `create_song_sections.lua`,
  `create_beat_from_riff.lua`, `midi_drums_help.lua` under a `## Scripts`
  heading) with:

  ```markdown
  ## The panel

  - **`midi_drums_panel.lua`** — the entry point. A single REAPER action
    ("MIDI Drums: Open Panel") opens a dockable ReaImGui window with four
    tabs: **Song Sections** (REAPER / Sidecar / AI / Song Map modes,
    replacing the old `create_song_sections.lua`'s four modes),
    **Riff-Lock Beat** (replacing `create_beat_from_riff.lua`, now also
    exposing Snare Reaction: Off/Reinforce/Stab), **Settings**
    (consolidates the `python_exe` path and every generation default into
    one editable, auto-saved surface), and **Log** (live subprocess
    output, replacing the separate REAPER console as the place to look
    when something fails).
  - `reaper/midi_drums/job_runner.lua`, `sections.lua`, `riff_lock.lua`,
    `settings.lua` — supporting modules the panel loads; not meant to be
    run as standalone REAPER actions themselves.

  The panel checks for ReaImGui on load and shows the install steps
  inline (not just a doc pointer) if it's missing — see Prerequisites
  above.
  ```

  Also update the section heading order so "Prerequisites for the
  upcoming unified panel" (added earlier this session) drops its
  "upcoming" framing now that the panel exists — rename it to
  `## Prerequisites` and remove the sentence "A unified ReaImGui panel
  replacing them is currently in design (see the design doc once it's
  written) and will need two additional installs first:" (replace with
  "The panel needs two additional installs beyond the Python venv setup
  already documented in the main project `CLAUDE.md`:").

- [ ] **Step 3: Rewrite `reaper/README.md`'s "Install" section**

  Replace the three-symlink Windows snippet and the two-copy fallback
  with a single-file version:

  ```markdown
  ## Install

  REAPER only loads ReaScripts from paths it knows about (typically
  `REAPER_RESOURCE_PATH/Scripts/`), so this directory needs a copy or
  symlink into that directory — REAPER's own copy is a deployed
  instance, this directory is the source of truth:

  ```bash
  # Windows (from an elevated shell, one-time):
  mklink "C:\REAPER\Scripts\midi_drums_panel.lua" "C:\path\to\midi_drums\reaper\midi_drums_panel.lua"
  mklink /D "C:\REAPER\Scripts\midi_drums" "C:\path\to\midi_drums\reaper\midi_drums"

  # Or, if you'd rather not symlink, copy after every edit:
  copy reaper\midi_drums_panel.lua "C:\REAPER\Scripts\"
  xcopy /E /I reaper\midi_drums "C:\REAPER\Scripts\midi_drums\"
  ```

  Then in REAPER: **Actions → Load ReaScript** → select
  `midi_drums_panel.lua` → assign a shortcut (e.g. "MIDI Drums: Open
  Panel").

  Neither the panel nor its supporting modules hardcode a Python path in
  tracked source — see the Settings tab, or the `python_exe` field
  prompted on first Generate click, backed by REAPER's persistent
  `ExtState` (section `midi_drums`, key `python_exe`).
  ```

- [ ] **Step 4: Remove the now-superseded "Keeping both sides in sync" script filenames**

  In `reaper/README.md`'s final section, the sentence currently reads
  (per the file as of this plan) referencing sidecar-contract changes —
  update any remaining mentions of `create_song_sections.lua` elsewhere
  in the file (e.g. the "drum_midi_generator.lua — not vendored" section
  compares itself against `create_song_sections.lua`) to instead say "the
  panel's Song Sections tab".

- [ ] **Step 5: Update `CLAUDE.md`'s "REAPER Lua Script Integration" section**

  This repo's root `CLAUDE.md` has a section titled
  `## REAPER Lua Script Integration` with an `### Overview` subsection
  describing `create_song_sections.lua` as "the bi-directional bridge"
  and `create_beat_from_riff.lua` as "a separate action". Replace the
  Overview paragraph with:

  ```markdown
  ### Overview

  `reaper/midi_drums_panel.lua` (vendored in this repo — see
  `reaper/README.md` for the install step) is the bi-directional bridge
  between REAPER and the midi_drums Python module: a single dockable
  ReaImGui panel with four tabs (Song Sections, Riff-Lock Beat, Settings,
  Log), replacing what used to be three separate REAPER actions. It
  calls Python via a **detached subprocess** (never a blocking
  `io.popen:read()`), polling a log file each `defer()` frame so the
  panel stays responsive even during the AI path's ~20-45s generation
  time. See `claudedocs/design_reaper_panel.md` for the full design.
  ```

  Update the `### Modes` table's lead-in sentence (currently referencing
  which script triggers which mode) to say "Song Sections tab mode" in
  place of "Triggered by" script-dialog language, and update the
  `### Lua Config Block` subsection (currently listing top-of-script
  `local` constants like `DEFAULT_GENRE`) to instead point at the
  panel's Settings tab / `settings.lua`'s `M.DEFAULTS` table as where
  those values now live.

- [ ] **Step 6: Manual verification — fresh-clone smoke check**

  From a second machine or a clean checkout, follow `reaper/README.md`'s
  rewritten Install section exactly as written (symlink or copy), load
  `midi_drums_panel.lua` as a REAPER action, run it. Expected: panel
  opens with no missing-file errors (confirms the `package.path`/
  `dofile` module loading in Task 5, Step 3 resolves correctly relative
  to wherever the script was actually loaded from, not just the
  developer's own working copy).

- [ ] **Step 7: Commit**

  ```bash
  git add reaper/README.md CLAUDE.md
  git commit -m "docs(reaper-panel): retire the three old scripts, document the panel"
  ```

---

## Self-Review Notes

- **Spec coverage:** every component in the spec's Architecture table
  (`midi_drums_panel.lua`, `job_runner.lua`, `sections.lua`,
  `riff_lock.lua`, `settings.lua`) has a task; the Error Handling
  principle (inline remediation text) is implemented in Task 5 Step 1
  (ReaImGui message box) and verified in Task 8 Step 6 (Log tab
  content); the single-job lock is implemented once in `job_runner.lua`
  (Task 2) and consumed identically by both Generate buttons (Tasks 6/7)
  rather than reimplemented per tab; Settings auto-save (no Save button)
  is Task 8 Step 1; the contextual help popovers are Task 5 Step 3
  (`draw_help_button`) plus Tasks 6/7's actual popover content; the four
  Song Sections modes and the Riff-Lock Beat Snare Reaction feature
  (added to the panel beyond what the retired script had, per the CLI's
  already-shipped `--snare-mode`/`--snare-stab-threshold` flags) are
  both in Tasks 6/7; doc updates are Task 9.
- **Placeholder scan:** no TBD/TODO; the one deliberately-simplified
  implementation (Task 8 Step 3's `*` badge instead of an animated dot)
  is called out explicitly as a complete-but-plain implementation, not a
  gap.
- **Type/signature consistency:** `job_runner.start(cmd, job_label,
  on_complete)`'s three-argument order is used identically in Tasks 6
  and 7. `sections.*`/`riff_lock.*` function names and parameter shapes
  declared in each task's Interfaces block match their Step 2
  implementations and their Task 6/7 call sites verbatim (e.g.
  `riff_lock.build_cmd`'s `p` table keys match exactly between Task 4's
  definition and Task 7's call).
- **Scope check:** this plan covers exactly the one subsystem the spec
  describes (the REAPER panel) — no Python-side changes, no unrelated
  refactors of the retired scripts' logic beyond the port itself.
