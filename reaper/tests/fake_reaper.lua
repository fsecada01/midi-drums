-- reaper/tests/fake_reaper.lua
-- Minimal in-memory stand-in for the slice of the REAPER ReaScript API
-- that step_editor.lua touches (MIDI_GetNote/InsertNote/SetNote/
-- DeleteNote/Sort/CountEvts, the TimeMap/QN<->PPQ conversions,
-- GetActiveTake/TakeIsMIDI/GetMediaItemInfo_Value, Undo_BeginBlock/
-- EndBlock), so the module's actual mutation logic can run under a real
-- Lua interpreter instead of only being checked for syntax balance (see
-- ADR 0001's "no automated Lua test runner exists" caveat - this is the
-- first one, deliberately scoped to just what step_editor.lua needs
-- rather than the whole ReaScript surface).
--
-- Assumes a constant-tempo, constant-time-signature project - enough to
-- exercise step_editor's bar/step/ppq math without reimplementing
-- REAPER's actual tempo-map engine.
local M = {}

-- Take-local ticks per quarter note - matches REAPER's real internal
-- MIDI resolution. step_editor.lua never hardcodes this itself (it
-- derives ppq_per_qn from two MIDI_GetPPQPosFromProjQN calls), so this
-- constant only needs to be internally consistent within the fake, not
-- equal to any particular real value.
local PPQ_PER_QN = 960

-- Builds a fresh fake REAPER environment, installs it as the global
-- `reaper`, and returns handles the test can use to seed/inspect state.
-- Each call is fully isolated - no state leaks between tests.
function M.new(opts)
  opts = opts or {}
  local bpm = opts.bpm or 120
  local ts_num = opts.ts_num or 4
  local ts_denom = opts.ts_denom or 4
  local item_position = opts.item_position or 0.0
  local item_length_bars = opts.item_length_bars or 2

  local sec_per_qn = 60.0 / bpm
  local qn_per_bar = ts_num * (4.0 / ts_denom)
  local item_length = item_length_bars * qn_per_bar * sec_per_qn

  local take = { notes = {}, is_midi = true }
  local item = { take = take, position = item_position, length = item_length }
  local calls = { undo_begin = 0, undo_end = 0 }

  local env = {}

  function env.GetActiveTake(it) return it.take end
  function env.TakeIsMIDI(t) return t.is_midi end

  function env.GetMediaItemInfo_Value(it, param)
    if param == "D_POSITION" then return it.position end
    if param == "D_LENGTH" then return it.length end
    error("fake_reaper: unsupported item param " .. tostring(param))
  end

  function env.TimeMap2_timeToQN(_proj, time) return time / sec_per_qn end
  function env.TimeMap2_QNToTime(_proj, qn) return qn * sec_per_qn end
  function env.TimeMap_GetTimeSigAtTime(_proj, _time) return ts_num, ts_denom, bpm end
  function env.Master_GetTempo() return bpm end

  function env.MIDI_GetProjQNFromPPQPos(_take, ppqpos) return ppqpos / PPQ_PER_QN end
  function env.MIDI_GetPPQPosFromProjQN(_take, projqn) return projqn * PPQ_PER_QN end

  function env.MIDI_CountEvts(t)
    return true, #t.notes, 0, 0
  end

  function env.MIDI_GetNote(t, idx)
    local n = t.notes[idx + 1]
    if not n then return false end
    return true, n.selected or false, n.muted or false,
      n.startppqpos, n.endppqpos, n.chan, n.pitch, n.vel
  end

  function env.MIDI_InsertNote(t, selected, muted, startppqpos, endppqpos, chan, pitch, vel, _noSort)
    t.notes[#t.notes + 1] = {
      selected = selected, muted = muted, startppqpos = startppqpos,
      endppqpos = endppqpos, chan = chan, pitch = pitch, vel = vel,
    }
    return true
  end

  function env.MIDI_SetNote(t, idx, selected, muted, startppqpos, endppqpos, chan, pitch, vel, _noSort)
    local n = t.notes[idx + 1]
    if not n then return false end
    n.selected, n.muted = selected, muted
    n.startppqpos, n.endppqpos = startppqpos, endppqpos
    n.chan, n.pitch, n.vel = chan, pitch, vel
    return true
  end

  function env.MIDI_DeleteNote(t, idx)
    if not t.notes[idx + 1] then return false end
    table.remove(t.notes, idx + 1)
    return true
  end

  function env.MIDI_Sort(t)
    table.sort(t.notes, function(a, b) return a.startppqpos < b.startppqpos end)
  end

  function env.Undo_BeginBlock() calls.undo_begin = calls.undo_begin + 1 end
  function env.Undo_EndBlock(_label, _flags) calls.undo_end = calls.undo_end + 1 end

  _G.reaper = env

  return {
    item = item, take = take, calls = calls,
    bpm = bpm, ts_num = ts_num, ts_denom = ts_denom,
    ppq_per_qn = PPQ_PER_QN, sec_per_qn = sec_per_qn,
  }
end

return M
