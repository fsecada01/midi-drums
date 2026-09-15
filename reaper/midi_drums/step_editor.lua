-- reaper/midi_drums/step_editor.lua
-- Data model for the unified Step Editor panel (ADR 0009, see
-- claudedocs/design_step_editor_grid.md's "Component design reference").
--
-- Source of truth is the live REAPER MIDI item, not a parallel pattern
-- format: `read_pattern_from_item` builds `data` from `MIDI_GetNote`
-- output and `commit` is the only function that writes it back via
-- `MIDI_InsertNote`/`MIDI_SetNote`/`MIDI_DeleteNote`/`MIDI_Sort`, wrapped
-- in one `Undo_BeginBlock`/`Undo_EndBlock` pair - matching the
-- Undo_BeginBlock/EndBlock pairing convention already used by
-- riff_lock.lua. Every other function here only mutates the in-memory
-- `data` table and marks affected notes dirty; nothing but `commit`
-- touches the REAPER MIDI API. This mirrors the established convention
-- (see sections.lua/riff_lock.lua/additive_rhythm.lua) that business-logic
-- modules build/mutate state and the panel decides when to act on it -
-- job_runner.start() is likewise only ever called from
-- midi_drums_panel.lua, never from this module.
--
-- A note's `ppqpos` is its exact, real position; `bar`/`step` are a
-- derived display projection recomputed from `ppqpos` at read time. A
-- macro operation (reassign/swap/scale/style) never touches `ppqpos` -
-- only a direct grid click (toggle_step), which by definition targets a
-- specific step, assigns a new one.
--
-- Historical note: the panel tab and ADR 0011's Apply Drummer round-trip
-- (serialize_pattern_json/parse_pattern_json/replace_pattern below) have
-- since shipped. Still not wired up: ADR 0010's Amount slider - the
-- Python side (density_control.py, the `adjust-density` CLI verb) exists,
-- but nothing here calls it yet.
local M = {}

-- Mirrors riff-lock's --grid choices (cli.py) - a genuinely fixed set,
-- not plugin-discovered data (see options.lua's own header comment on
-- this distinction).
M.GRID_RESOLUTIONS = { "8th", "16th", "32nd", "8th_triplet", "16th_triplet" }

-- Steps per quarter note for each resolution - e.g. "8th_triplet" packs
-- 3 into the time normally held by 2 "8th" steps (i.e. one quarter note).
local STEPS_PER_QUARTER = {
  ["8th"] = 2,
  ["16th"] = 4,
  ["32nd"] = 8,
  ["8th_triplet"] = 3,
  ["16th_triplet"] = 6,
}

-- MIDI channel 10 (0-indexed) - matches DrumKit.channel in kit.py; REAPER's
-- MIDI_GetNote/InsertNote/SetNote `chan` parameter is likewise 0-based.
local DRUM_CHANNEL = 9

-- Fraction of a step (in quarter notes) a note is allowed to sit off a
-- grid line before read_pattern_from_item flags it `off_grid`.
local OFF_GRID_TOLERANCE_STEPS = 0.15

-- Default sounding length for a newly toggled-on note, as a fraction of
-- one grid step - short, percussive, independent of the Python MIDI
-- engine's own duration convention (export/midi/engine.py works in
-- seconds; this module works in take-local PPQ ticks).
local NEW_NOTE_LENGTH_STEP_FRACTION = 0.5

function M.steps_per_bar(grid_resolution, ts_num, ts_denom)
  local steps_per_quarter = STEPS_PER_QUARTER[grid_resolution]
  if not steps_per_quarter then
    return nil, "Unknown grid_resolution: " .. tostring(grid_resolution)
  end
  local qn_per_bar = ts_num * (4.0 / ts_denom)
  return math.floor(qn_per_bar * steps_per_quarter + 0.5)
end

-- Clears any existing dirty entry for `note` (by identity), then records
-- `action` unless it's nil (nil just clears - used when a pending,
-- not-yet-committed "add" is toggled back off before ever being
-- committed, so there's nothing left for commit() to do for that note).
local function mark_dirty(data, note, action)
  for i = #data.dirty, 1, -1 do
    if data.dirty[i].note == note then
      table.remove(data.dirty, i)
    end
  end
  if action then
    data.dirty[#data.dirty + 1] = { note = note, action = action }
  end
end

-- qn (quarter-notes from item start) -> take-local ppq, using the
-- conversion factors read_pattern_from_item cached on `data` -
-- arithmetic-only (no REAPER API calls) so callers stay pure over `data`
-- alone, matching the design's separation between mutation and the
-- REAPER-touching read/commit functions. Public since ADR 0011's
-- replace_pattern (and the panel's Apply Drummer round-trip) needs it to
-- resolve a Python-side `position_qn` back to a real take-local ppqpos,
-- not just this module's own bar/step grid math.
function M.qn_to_ppq(data, qn)
  return data.item_start_ppq + math.floor(qn * data.ppq_per_qn + 0.5)
end

-- Inverse of qn_to_ppq - only needed internally (serialize_pattern_json),
-- so it stays private.
local function ppq_to_qn(data, ppq)
  return (ppq - data.item_start_ppq) / data.ppq_per_qn
end

-- bar/step -> take-local ppq. Kept private/grid-specific, unlike
-- qn_to_ppq above which works on an exact qn offset.
local function step_to_ppq(data, bar, step)
  local qn_offset = bar * data.qn_per_bar + step * data.qn_per_step
  return M.qn_to_ppq(data, qn_offset)
end

local function new_note_length_ppq(data)
  return math.max(
    1,
    math.floor(data.qn_per_step * NEW_NOTE_LENGTH_STEP_FRACTION * data.ppq_per_qn + 0.5)
  )
end

-- Builds `data` (see the design doc's "Unified data model") from the
-- selected item's active MIDI take, filtered to the drum channel and
-- bucketed against `grid_resolution`. Unmapped pitches (not present in
-- `kit_map`) become an "Unmapped (note N)" lane rather than being
-- dropped from view.
function M.read_pattern_from_item(item, kit_map, grid_resolution)
  local steps_per_quarter = STEPS_PER_QUARTER[grid_resolution]
  if not steps_per_quarter then
    return nil, "Unknown grid_resolution: " .. tostring(grid_resolution)
  end

  local take = reaper.GetActiveTake(item)
  if not take or not reaper.TakeIsMIDI(take) then
    return nil, "Selected item has no active MIDI take."
  end

  local item_start = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
  local item_len = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
  local item_start_qn = reaper.TimeMap2_timeToQN(0, item_start)
  local item_end_qn = reaper.TimeMap2_timeToQN(0, item_start + item_len)

  local ts_num, ts_denom = reaper.TimeMap_GetTimeSigAtTime(0, item_start)
  if not ts_num or ts_num == 0 then
    ts_num, ts_denom = 4, 4
  end

  local qn_per_bar = ts_num * (4.0 / ts_denom)
  local qn_per_step = 1.0 / steps_per_quarter
  local bars = math.max(1, math.floor((item_end_qn - item_start_qn) / qn_per_bar + 0.5))

  -- take-local ppq per project quarter-note, derived from two known QN
  -- points rather than assuming a fixed ticks-per-quarter constant.
  local ppq_at_0 = reaper.MIDI_GetPPQPosFromProjQN(take, item_start_qn)
  local ppq_at_1 = reaper.MIDI_GetPPQPosFromProjQN(take, item_start_qn + 1.0)
  local ppq_per_qn = ppq_at_1 - ppq_at_0

  local kit_map_by_key = {}
  local note_by_pitch = {}
  for _, entry in ipairs(kit_map) do
    kit_map_by_key[entry.instrument] = entry
    note_by_pitch[entry.note] = entry
  end

  local lanes = {}
  local _, note_count = reaper.MIDI_CountEvts(take)
  for i = 0, note_count - 1 do
    local ok, _, _, startppqpos, _, chan, pitch, vel = reaper.MIDI_GetNote(take, i)
    if ok and chan == DRUM_CHANNEL then
      local mapped = note_by_pitch[pitch]
      local lane_key, label, group, family, note_pitch
      if mapped then
        lane_key, label, group, family, note_pitch =
          mapped.instrument, mapped.label, mapped.group, mapped.family, mapped.note
      else
        lane_key = string.format("unmapped_%d", pitch)
        label = string.format("Unmapped (note %d)", pitch)
        group, family, note_pitch = "unmapped", "unmapped", pitch
      end

      local lane = lanes[lane_key]
      if not lane then
        lane = { label = label, note = note_pitch, group = group, family = family, notes = {} }
        lanes[lane_key] = lane
      end

      local note_qn = reaper.MIDI_GetProjQNFromPPQPos(take, startppqpos)
      local step_float = (note_qn - item_start_qn) / qn_per_step
      local step_round = math.floor(step_float + 0.5)
      local off_grid = math.abs(step_float - step_round) > OFF_GRID_TOLERANCE_STEPS
      local steps_per_bar_n = math.floor(qn_per_bar / qn_per_step + 0.5)
      local bar = math.floor(step_round / steps_per_bar_n)
      local step = step_round % steps_per_bar_n

      lane.notes[#lane.notes + 1] = {
        bar = bar,
        step = step,
        ppqpos = startppqpos,
        velocity = vel,
        off_grid = off_grid,
        _idx = i,
      }
    end
  end

  return {
    bars = bars,
    grid_resolution = grid_resolution,
    lanes = lanes,
    dirty = {},
    ts_num = ts_num,
    ts_denom = ts_denom,
    qn_per_bar = qn_per_bar,
    qn_per_step = qn_per_step,
    item_start_ppq = ppq_at_0,
    ppq_per_qn = ppq_per_qn,
    kit_map_by_key = kit_map_by_key,
  }
end

-- Direct-grid mutation: toggles a note at lane/bar/step. Marks the
-- affected note dirty ("remove" for a real REAPER note, or simply
-- untracked if it was itself an uncommitted pending "add").
function M.toggle_step(data, lane, bar, step, velocity)
  local l = data.lanes[lane]
  if not l then
    return false, "Unknown lane: " .. tostring(lane)
  end

  for i, note in ipairs(l.notes) do
    if note.bar == bar and note.step == step then
      table.remove(l.notes, i)
      mark_dirty(data, note, note._idx and "remove" or nil)
      return true
    end
  end

  local note = {
    bar = bar,
    step = step,
    ppqpos = step_to_ppq(data, bar, step),
    velocity = velocity,
    off_grid = false,
  }
  l.notes[#l.notes + 1] = note
  mark_dirty(data, note, "add")
  return true
end

-- Moves every note in `from_lanes` onto `to_lane` (must be a lane present
-- in the current kit-map). `ppqpos`/`velocity` are untouched - only lane
-- membership (and therefore resolved MIDI pitch) changes.
function M.reassign_lane(data, from_lanes, to_lane)
  local target_entry = data.kit_map_by_key[to_lane]
  if not target_entry then
    return false, "Unknown target lane: " .. tostring(to_lane)
  end

  local target = data.lanes[to_lane]
  if not target then
    target = {
      label = target_entry.label,
      note = target_entry.note,
      group = target_entry.group,
      family = target_entry.family,
      notes = {},
    }
    data.lanes[to_lane] = target
  end

  for _, from_lane in ipairs(from_lanes) do
    local source = data.lanes[from_lane]
    if source and source ~= target then
      for _, note in ipairs(source.notes) do
        target.notes[#target.notes + 1] = note
        mark_dirty(data, note, note._idx and "move" or "add")
      end
      source.notes = {}
    end
  end

  return true
end

-- Same mutation shape as reassign_lane, constrained to siblings sharing
-- `lanes`' articulation family - the UI only ever offers siblings in the
-- dropdown, but this re-checks rather than trusting the caller blindly.
function M.swap_articulation(data, lanes, sibling_note)
  local target_entry = data.kit_map_by_key[sibling_note]
  if not target_entry then
    return false, "Unknown target articulation: " .. tostring(sibling_note)
  end

  for _, lane_key in ipairs(lanes) do
    local source = data.lanes[lane_key]
    if source and source.family ~= target_entry.family then
      return false, "swap_articulation requires a sibling within the same articulation family."
    end
  end

  return M.reassign_lane(data, lanes, sibling_note)
end

-- Scales velocity for every note in the given lanes by `factor`, clamped
-- to the valid MIDI range.
function M.scale_velocity(data, lanes, factor)
  for _, lane_key in ipairs(lanes) do
    local lane = data.lanes[lane_key]
    if lane then
      for _, note in ipairs(lane.notes) do
        local scaled = math.floor(note.velocity * factor + 0.5)
        note.velocity = math.max(1, math.min(127, scaled))
        mark_dirty(data, note, note._idx and "move" or "add")
      end
    end
  end
  return true
end

-- Fixed content library (Fork 4 - mechanism only, exact presets are a
-- content decision). Each curve maps (step-within-bar, steps-per-bar) to
-- a velocity multiplier. Unlike the drum-note map this is genuinely
-- static, original stylistic content with no Python-side source of
-- truth - see the design doc's "Why not a hardcoded Lua drum-note table"
-- section for why that distinction matters here.
M.VELOCITY_STYLE_PRESETS = {
  flat = function(_step, _steps_per_bar)
    return 1.0
  end,
  crescendo = function(step, steps_per_bar)
    return 0.6 + 0.4 * (step / math.max(1, steps_per_bar - 1))
  end,
  halftime_accent = function(step, steps_per_bar)
    local half = math.max(1, math.floor(steps_per_bar / 2))
    return (step % half == 0) and 1.15 or 0.85
  end,
  backbeat_emphasis = function(step, steps_per_bar)
    local quarter = math.max(1, math.floor(steps_per_bar / 4))
    return (step % (quarter * 2) == quarter) and 1.2 or 0.9
  end,
}

function M.apply_velocity_style(data, lanes, preset_name)
  local curve = M.VELOCITY_STYLE_PRESETS[preset_name]
  if not curve then
    return false, "Unknown velocity style preset: " .. tostring(preset_name)
  end

  local steps_per_bar = M.steps_per_bar(data.grid_resolution, data.ts_num, data.ts_denom)

  for _, lane_key in ipairs(lanes) do
    local lane = data.lanes[lane_key]
    if lane then
      for _, note in ipairs(lane.notes) do
        local scaled = math.floor(note.velocity * curve(note.step, steps_per_bar) + 0.5)
        note.velocity = math.max(1, math.min(127, scaled))
        mark_dirty(data, note, note._idx and "move" or "add")
      end
    end
  end
  return true
end

-- Overwrites every bar after `source_bar` (through the end of the
-- pattern) with `source_bar`'s pattern, across every lane - "establish a
-- groove in bar 1, then repeat it" rather than a single-bar copy. Notes
-- in a target bar are fully replaced (deleted if already committed, or
-- simply dropped if still a pending "add"), not merged with whatever was
-- already there.
function M.duplicate_bar_forward(data, source_bar)
  if source_bar < 0 or source_bar >= data.bars then
    return false, "source_bar out of range: " .. tostring(source_bar)
  end
  if source_bar >= data.bars - 1 then
    return false, "No bars after the source bar to duplicate into."
  end

  for _, lane in pairs(data.lanes) do
    local template = {}
    for _, note in ipairs(lane.notes) do
      if note.bar == source_bar then
        template[#template + 1] = { step = note.step, velocity = note.velocity }
      end
    end

    for i = #lane.notes, 1, -1 do
      local note = lane.notes[i]
      if note.bar > source_bar then
        table.remove(lane.notes, i)
        mark_dirty(data, note, note._idx and "remove" or nil)
      end
    end

    for target_bar = source_bar + 1, data.bars - 1 do
      for _, t in ipairs(template) do
        local note = {
          bar = target_bar,
          step = t.step,
          ppqpos = step_to_ppq(data, target_bar, t.step),
          velocity = t.velocity,
          off_grid = false,
        }
        lane.notes[#lane.notes + 1] = note
        mark_dirty(data, note, "add")
      end
    end
  end

  return true
end

-- ===== ADR 0011 (Apply Drummer round-trip) =====
-- Small helpers duplicated from sections.lua/additive_rhythm.lua rather
-- than shared via a common util module, matching additive_rhythm.lua's
-- own precedent for why a third shared-util module isn't worth it here.

function M.get_project_dir()
  local p = reaper.GetProjectPath("")
  return (p ~= "") and p or reaper.GetResourcePath()
end

local function shell_escape(s)
  s = s:gsub("[\r\n]", " ")
  s = s:gsub('"', "'")
  s = s:gsub("[&|^<>%%]", "")
  return s
end

-- Flattens the whole loaded pattern (every lane, not just checked ones -
-- Apply Drummer always acts on the whole pattern per ADR 0011) into the
-- JSON array `apply-drummer-style --input` expects: one object per note
-- with `instrument` (the lane key) and `position_qn` (exact quarter-notes
-- from item start, via ppq_to_qn rather than bar*qn_per_bar+step*qn_per_step
-- so an already off-grid note's precise position round-trips instead of
-- being snapped onto the grid before it even reaches Python).
function M.serialize_pattern_json(data)
  local parts = {}
  for lane_key, lane in pairs(data.lanes) do
    for _, note in ipairs(lane.notes) do
      local qn = ppq_to_qn(data, note.ppqpos)
      parts[#parts + 1] = string.format(
        '  {"instrument": "%s", "position_qn": %.6f, "velocity": %d}',
        lane_key, qn, note.velocity
      )
    end
  end
  return "[\n" .. table.concat(parts, ",\n") .. "\n]"
end

-- Flattens the whole loaded pattern into the same shape M.parse_pattern_
-- json returns (a plain Lua table, not JSON - no serialize/parse round-trip
-- needed since this never leaves the Lua process). Used to snapshot the
-- pattern immediately before an Apply Drummer run so a later "Revert
-- Apply Drummer" click has something to hand back to M.replace_pattern -
-- see midi_drums_panel.lua's se_apply_drummer_snapshot.
function M.snapshot_pattern(data)
  local notes = {}
  for lane_key, lane in pairs(data.lanes) do
    for _, note in ipairs(lane.notes) do
      notes[#notes + 1] = {
        instrument = lane_key,
        position_qn = ppq_to_qn(data, note.ppqpos),
        velocity = note.velocity,
      }
    end
  end
  return notes
end

-- Parses the flat note-list JSON `apply-drummer-style --output` writes
-- (midi_drums/api/cli.py:handle_apply_drummer_style_command). Only pulls
-- out instrument/position_qn/velocity - `ghost_note`/`accent` are part of
-- the Python round-trip's shape but have no equivalent field on this
-- module's note table yet (it only distinguishes velocity), the same
-- limitation every other macro operation here already has. An empty `[]`
-- (a totally silent pattern) is not an error - it legitimately parses to
-- an empty list, same as read_pattern_from_item finding zero notes.
function M.parse_pattern_json(content)
  local notes = {}
  for instrument, position_qn, velocity in content:gmatch(
    '"instrument"%s*:%s*"([^"]*)"%s*,%s*"position_qn"%s*:%s*([%-%d%.eE]+)%s*,'
    .. '%s*"velocity"%s*:%s*(%d+)'
  ) do
    notes[#notes + 1] = {
      instrument = instrument,
      position_qn = tonumber(position_qn),
      velocity = tonumber(velocity),
    }
  end
  return notes
end

function M.build_apply_drummer_cmd(python_exe, p)
  local drummer_flag = ""
  if p.drummer and p.drummer ~= "" then
    drummer_flag = string.format(' --drummer "%s"', shell_escape(p.drummer))
  end
  return string.format(
    '"%s" -m midi_drums apply-drummer-style --input "%s" --output "%s"'
    .. ' --drummer-intensity %g --timing-variance %g --velocity-variance %g'
    .. ' --ts-num %d --ts-denom %d%s',
    python_exe, p.input_path, p.output_path,
    p.drummer_intensity, p.timing_variance, p.velocity_variance,
    p.ts_num, p.ts_denom, drummer_flag
  )
end

-- Replaces the entire loaded pattern (every lane) with `notes` - a flat
-- list of {instrument, position_qn, velocity} as returned by
-- parse_pattern_json. Every existing note is dirty-marked "remove" (or
-- dropped if a pending "add") and every returned note is dirty-marked
-- "add", mirroring duplicate_bar_forward's replace-not-merge approach but
-- applied to the whole pattern at once - drummer style application and
-- humanization return a fundamentally new note list with no reliable
-- identity mapping back to original note indices (ADR 0011's Decision).
-- A lane absent from `data.lanes` (e.g. GhostNoteLayer inserting into a
-- previously note-less lane) is created on demand from
-- `data.kit_map_by_key`, matching reassign_lane's own lane creation.
function M.replace_pattern(data, notes)
  for _, lane in pairs(data.lanes) do
    for _, note in ipairs(lane.notes) do
      mark_dirty(data, note, note._idx and "remove" or nil)
    end
    lane.notes = {}
  end

  local steps_per_bar_n = math.floor(data.qn_per_bar / data.qn_per_step + 0.5)

  for _, n in ipairs(notes) do
    local lane = data.lanes[n.instrument]
    if not lane then
      local entry = data.kit_map_by_key[n.instrument]
      if entry then
        lane = {
          label = entry.label, note = entry.note,
          group = entry.group, family = entry.family, notes = {},
        }
        data.lanes[n.instrument] = lane
      end
    end

    if lane then
      local step_float = n.position_qn / data.qn_per_step
      local step_round = math.floor(step_float + 0.5)
      local off_grid = math.abs(step_float - step_round) > OFF_GRID_TOLERANCE_STEPS
      local bar = math.floor(step_round / steps_per_bar_n)
      local step = step_round % steps_per_bar_n
      local velocity = math.max(1, math.min(127, math.floor(n.velocity + 0.5)))

      local note = {
        bar = bar,
        step = step,
        ppqpos = M.qn_to_ppq(data, n.position_qn),
        velocity = velocity,
        off_grid = off_grid,
      }
      lane.notes[#lane.notes + 1] = note
      mark_dirty(data, note, "add")
    end
  end

  return true
end

-- Re-resolves each live note's `_idx` after a commit's inserts/deletes
-- have shifted the take's event indices, by matching (pitch, ppqpos)
-- against a fresh MIDI_GetNote scan. Known limitation: two notes sharing
-- an exact (pitch, ppqpos) - i.e. a true duplicate hit - aren't
-- distinguished; the last one scanned wins. Acceptable for v1: such
-- duplicates are degenerate input this editor has no reason to produce.
local function reindex_notes(take, data)
  local idx_by_key = {}
  local _, note_count = reaper.MIDI_CountEvts(take)
  for i = 0, note_count - 1 do
    local ok, _, _, startppqpos, _, chan, pitch = reaper.MIDI_GetNote(take, i)
    if ok and chan == DRUM_CHANNEL then
      idx_by_key[pitch .. ":" .. startppqpos] = i
    end
  end

  for _, lane in pairs(data.lanes) do
    for _, note in ipairs(lane.notes) do
      note._idx = idx_by_key[lane.note .. ":" .. note.ppqpos]
    end
  end
end

-- The single REAPER-mutating function: applies data.dirty to the item's
-- take via MIDI_InsertNote/MIDI_SetNote/MIDI_DeleteNote/MIDI_Sort, all
-- inside one Undo_BeginBlock/Undo_EndBlock pair, regardless of whether
-- `dirty` holds one grid click's worth of change or a whole macro
-- operation's worth.
function M.commit(item, data)
  local take = reaper.GetActiveTake(item)
  if not take then
    return false, "Item has no active take."
  end

  if #data.dirty == 0 then
    return true
  end

  local pitch_of = {}
  for _, lane in pairs(data.lanes) do
    for _, note in ipairs(lane.notes) do
      pitch_of[note] = lane.note
    end
  end

  local deletes, moves, adds = {}, {}, {}
  for _, d in ipairs(data.dirty) do
    if d.action == "remove" then
      deletes[#deletes + 1] = d.note
    elseif d.action == "move" then
      moves[#moves + 1] = d.note
    elseif d.action == "add" then
      adds[#adds + 1] = d.note
    end
  end

  reaper.Undo_BeginBlock()

  -- Highest index first, so deleting one doesn't invalidate the
  -- not-yet-processed indices below it; any pending move whose index
  -- sits above a just-deleted note is shifted down to match.
  table.sort(deletes, function(a, b) return a._idx > b._idx end)
  for _, note in ipairs(deletes) do
    reaper.MIDI_DeleteNote(take, note._idx)
    for _, other in ipairs(moves) do
      if other._idx and other._idx > note._idx then
        other._idx = other._idx - 1
      end
    end
  end

  for _, note in ipairs(moves) do
    local pitch = pitch_of[note]
    if pitch and note._idx then
      local end_ppq = note.ppqpos + new_note_length_ppq(data)
      reaper.MIDI_SetNote(
        take, note._idx, true, false, note.ppqpos, end_ppq,
        DRUM_CHANNEL, pitch, note.velocity, true
      )
    end
  end

  for _, note in ipairs(adds) do
    local pitch = pitch_of[note]
    if pitch then
      local end_ppq = note.ppqpos + new_note_length_ppq(data)
      reaper.MIDI_InsertNote(
        take, false, false, note.ppqpos, end_ppq,
        DRUM_CHANNEL, pitch, note.velocity, true
      )
    end
  end

  reaper.MIDI_Sort(take)
  reaper.Undo_EndBlock("Edit Step Pattern", -1)

  reindex_notes(take, data)
  data.dirty = {}
  return true
end

return M
