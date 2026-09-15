-- reaper/tests/test_step_editor.lua
-- Real-interpreter regression suite for step_editor.lua (ADR 0009),
-- run against fake_reaper.lua instead of a live REAPER install. See
-- reaper/tests/README.md for how to run this.
local script_dir = (arg[0] or ""):match("^(.*[/\\])") or "./"

local fake_reaper = dofile(script_dir .. "fake_reaper.lua")
local helpers = dofile(script_dir .. "test_helpers.lua")
local step_editor = dofile(script_dir .. "../midi_drums/step_editor.lua")

-- Small fixed kit-map, matching the shape of DrumKit.kit_map()/
-- options.parse_kit_map's `notes` array. CLOSED_HH/PEDAL_HH share a
-- family (for swap_articulation's sibling check); OPEN_HH doesn't.
local KIT_MAP = {
  { note = 36, instrument = "KICK", label = "Kick", group = "kick", family = "kick", default_velocity = 105 },
  { note = 38, instrument = "SNARE", label = "Snare", group = "snare", family = "snare", default_velocity = 100 },
  { note = 42, instrument = "CLOSED_HH", label = "Closed HH", group = "hihat", family = "hihat_closed", default_velocity = 90 },
  { note = 44, instrument = "PEDAL_HH", label = "Pedal HH", group = "hihat", family = "hihat_closed", default_velocity = 80 },
  { note = 46, instrument = "OPEN_HH", label = "Open HH", group = "hihat", family = "hihat_open", default_velocity = 90 },
}

local function seed_note_ppq(fx, pitch, ppq, chan)
  fx.take.notes[#fx.take.notes + 1] = {
    startppqpos = ppq, endppqpos = ppq + 100,
    chan = chan or 9, pitch = pitch, vel = 100,
  }
end

local function seed_note_qn(fx, pitch, qn, chan)
  seed_note_ppq(fx, pitch, qn * fx.ppq_per_qn, chan)
end

-- Standard fixture: kick x2, snare x2, closed-hh x2 (all on-grid, 16th
-- grid @ 4/4 @ 120bpm), one off-grid unmapped note, one wrong-channel
-- note that read_pattern_from_item must filter out entirely.
local function build_fixture()
  local fx = fake_reaper.new({ bpm = 120, ts_num = 4, ts_denom = 4, item_length_bars = 2 })
  seed_note_qn(fx, 36, 0.0) -- kick, bar0 step0
  seed_note_qn(fx, 36, 2.0) -- kick, bar0 step8
  seed_note_qn(fx, 38, 1.0) -- snare, bar0 step4
  seed_note_qn(fx, 38, 3.0) -- snare, bar0 step12
  seed_note_qn(fx, 42, 0.0) -- closed hh, bar0 step0
  seed_note_qn(fx, 42, 0.5) -- closed hh, bar0 step2
  seed_note_ppq(fx, 50, 100) -- unmapped pitch, deliberately off-grid
  seed_note_qn(fx, 36, 5.0, 0) -- wrong channel - must be filtered out

  local data, err = step_editor.read_pattern_from_item(fx.item, KIT_MAP, "16th")
  assert(data, "fixture read_pattern_from_item failed: " .. tostring(err))
  return fx, data
end

local function count_notes(lane)
  return lane and #lane.notes or 0
end

-- Only channel 9 (DRUM_CHANNEL) notes - the fixture deliberately seeds a
-- channel-0 note at pitch 36 that read_pattern_from_item/commit both
-- ignore forever, so it must not count as "still has the old pitch".
local function pitches_in_take(fx)
  local out = {}
  for _, n in ipairs(fx.take.notes) do
    if n.chan == 9 then
      out[#out + 1] = n.pitch
    end
  end
  table.sort(out)
  return out
end

local t = helpers.new()

t.case("steps_per_bar: common grid resolutions", function()
  helpers.assert_eq(step_editor.steps_per_bar("16th", 4, 4), 16, "16th in 4/4")
  helpers.assert_eq(step_editor.steps_per_bar("8th", 4, 4), 8, "8th in 4/4")
  helpers.assert_eq(step_editor.steps_per_bar("8th_triplet", 4, 4), 12, "8th_triplet in 4/4")
  helpers.assert_eq(step_editor.steps_per_bar("16th_triplet", 4, 4), 24, "16th_triplet in 4/4")
  helpers.assert_eq(step_editor.steps_per_bar("16th", 3, 4), 12, "16th in 3/4")
end)

t.case("steps_per_bar: unknown resolution returns nil + error", function()
  local result, err = step_editor.steps_per_bar("bogus", 4, 4)
  helpers.assert_nil(result, "steps_per_bar result")
  helpers.assert_true(err ~= nil, "steps_per_bar error message")
end)

t.case("read_pattern_from_item: bars, lane counts, bar/step bucketing", function()
  local fx, data = build_fixture()

  helpers.assert_eq(data.bars, 2, "data.bars")
  helpers.assert_eq(count_notes(data.lanes.KICK), 2, "KICK note count")
  helpers.assert_eq(count_notes(data.lanes.SNARE), 2, "SNARE note count")
  helpers.assert_eq(count_notes(data.lanes.CLOSED_HH), 2, "CLOSED_HH note count")

  local total = count_notes(data.lanes.KICK) + count_notes(data.lanes.SNARE)
    + count_notes(data.lanes.CLOSED_HH)
  helpers.assert_eq(total, 6, "on-grid mapped note total (wrong-channel note must be excluded)")

  helpers.assert_eq(data.lanes.KICK.notes[1].bar, 0, "kick[1].bar")
  helpers.assert_eq(data.lanes.KICK.notes[1].step, 0, "kick[1].step")
  helpers.assert_eq(data.lanes.KICK.notes[2].step, 8, "kick[2].step")
  helpers.assert_eq(data.lanes.SNARE.notes[1].step, 4, "snare[1].step")
  helpers.assert_eq(data.lanes.SNARE.notes[2].step, 12, "snare[2].step")

  for _, n in ipairs(data.lanes.KICK.notes) do
    helpers.assert_true(not n.off_grid, "on-grid kick note flagged off_grid")
    helpers.assert_true(n._idx ~= nil, "on-grid kick note missing _idx")
  end
end)

t.case("read_pattern_from_item: unmapped pitch becomes its own lane", function()
  local _fx, data = build_fixture()

  local lane = data.lanes.unmapped_50
  helpers.assert_true(lane ~= nil, "unmapped_50 lane exists")
  helpers.assert_eq(count_notes(lane), 1, "unmapped_50 note count")
  helpers.assert_eq(lane.label, "Unmapped (note 50)", "unmapped_50 label")
end)

t.case("read_pattern_from_item: off-grid tolerance flags the misaligned note", function()
  local _fx, data = build_fixture()

  local note = data.lanes.unmapped_50.notes[1]
  helpers.assert_true(note.off_grid, "deliberately off-grid note not flagged")
end)

t.case("toggle_step: add a new note, commit persists it and reindexes", function()
  local fx, data = build_fixture()
  local before_count = #fx.take.notes

  local ok = step_editor.toggle_step(data, "CLOSED_HH", 1, 0, 77)
  helpers.assert_true(ok, "toggle_step add returned false")

  local ok2 = step_editor.commit(fx.item, data)
  helpers.assert_true(ok2, "commit returned false")

  helpers.assert_eq(#fx.take.notes, before_count + 1, "take note count after add+commit")
  helpers.assert_eq(fx.calls.undo_begin, 1, "Undo_BeginBlock call count")
  helpers.assert_eq(fx.calls.undo_end, 1, "Undo_EndBlock call count")

  local new_note = data.lanes.CLOSED_HH.notes[#data.lanes.CLOSED_HH.notes]
  helpers.assert_true(new_note._idx ~= nil, "newly committed note missing reindexed _idx")

  local _fx2, reread = build_fixture() -- sanity: fixture helper itself still works
  helpers.assert_true(reread ~= nil, "sanity re-read")
end)

t.case("toggle_step: remove an already-committed note, commit deletes it", function()
  local fx, data = build_fixture()
  local before_count = #fx.take.notes

  -- kick's bar0/step0 note is a real, already-committed note (has _idx).
  local ok = step_editor.toggle_step(data, "KICK", 0, 0, 105)
  helpers.assert_true(ok, "toggle_step remove returned false")
  step_editor.commit(fx.item, data)

  helpers.assert_eq(#fx.take.notes, before_count - 1, "take note count after remove+commit")
  helpers.assert_eq(count_notes(data.lanes.KICK), 1, "KICK lane note count after removal")
end)

t.case("toggle_step: add then remove before commit is a true no-op", function()
  local fx, data = build_fixture()
  local before_count = #fx.take.notes

  step_editor.toggle_step(data, "SNARE", 1, 0, 100) -- add (uncommitted)
  step_editor.toggle_step(data, "SNARE", 1, 0, 100) -- toggled back off
  helpers.assert_eq(#data.dirty, 0, "dirty list should be empty after add+remove of the same cell")

  step_editor.commit(fx.item, data)
  helpers.assert_eq(#fx.take.notes, before_count, "take note count must be unchanged")
  helpers.assert_eq(fx.calls.undo_begin, 0, "commit must not open an undo block for a no-op")
end)

t.case("reassign_lane: moves notes and pitch, one undo block", function()
  local fx, data = build_fixture()
  local kick_count = count_notes(data.lanes.KICK)
  local snare_count_before = count_notes(data.lanes.SNARE)

  local ok, err = step_editor.reassign_lane(data, { "KICK" }, "SNARE")
  helpers.assert_true(ok, "reassign_lane failed: " .. tostring(err))
  step_editor.commit(fx.item, data)

  helpers.assert_eq(count_notes(data.lanes.KICK), 0, "KICK lane should be empty after reassign")
  helpers.assert_eq(count_notes(data.lanes.SNARE), snare_count_before + kick_count, "SNARE lane grew by the reassigned count")
  helpers.assert_eq(fx.calls.undo_begin, 1, "reassign_lane commit should be exactly one undo block")

  local pitches = pitches_in_take(fx)
  for _, p in ipairs(pitches) do
    helpers.assert_true(p ~= 36, "no note should still have the old KICK pitch after reassign")
  end
end)

t.case("scale_velocity: scales and clamps to the MIDI range", function()
  local fx, data = build_fixture()

  local ok = step_editor.scale_velocity(data, { "SNARE" }, 2.0)
  helpers.assert_true(ok, "scale_velocity failed")
  for _, note in ipairs(data.lanes.SNARE.notes) do
    helpers.assert_eq(note.velocity, 127, "velocity should clamp to 127 (100 * 2.0)")
  end

  step_editor.commit(fx.item, data)
  for _, n in ipairs(fx.take.notes) do
    if n.pitch == 38 then
      helpers.assert_eq(n.vel, 127, "committed velocity should reflect the clamp")
    end
  end
end)

t.case("apply_velocity_style: 'flat' is a no-op multiplier", function()
  local _fx, data = build_fixture()

  local ok = step_editor.apply_velocity_style(data, { "KICK" }, "flat")
  helpers.assert_true(ok, "apply_velocity_style failed")
  for _, note in ipairs(data.lanes.KICK.notes) do
    helpers.assert_eq(note.velocity, 100, "flat style must not change velocity")
  end
end)

t.case("apply_velocity_style: unknown preset returns an error", function()
  local _fx, data = build_fixture()

  local ok, err = step_editor.apply_velocity_style(data, { "KICK" }, "not_a_real_preset")
  helpers.assert_true(ok == false, "unknown preset should return false")
  helpers.assert_true(err ~= nil, "unknown preset should return an error message")
end)

t.case("swap_articulation: rejects a cross-family target", function()
  local _fx, data = build_fixture()

  local ok, err = step_editor.swap_articulation(data, { "CLOSED_HH" }, "OPEN_HH")
  helpers.assert_true(ok == false, "cross-family swap should fail")
  helpers.assert_true(err ~= nil, "cross-family swap should return an error message")
end)

t.case("duplicate_bar_forward: overwrites every later bar, all lanes", function()
  local fx, data = build_fixture()

  -- Give SNARE a bar-1 note distinct from bar 0's pattern, so we can
  -- verify it gets replaced rather than merged with bar 0's content.
  step_editor.toggle_step(data, "SNARE", 1, 15, 60)
  step_editor.commit(fx.item, data)

  local ok, err = step_editor.duplicate_bar_forward(data, 0)
  helpers.assert_true(ok, "duplicate_bar_forward failed: " .. tostring(err))
  step_editor.commit(fx.item, data)

  -- Bar 0's KICK/SNARE/CLOSED_HH steps should now also appear at bar 1.
  local function has_step(lane, bar, step)
    for _, n in ipairs(lane.notes) do
      if n.bar == bar and n.step == step then return true end
    end
    return false
  end

  helpers.assert_true(has_step(data.lanes.KICK, 1, 0), "bar1 kick step0 missing after duplicate")
  helpers.assert_true(has_step(data.lanes.KICK, 1, 8), "bar1 kick step8 missing after duplicate")
  helpers.assert_true(has_step(data.lanes.SNARE, 1, 4), "bar1 snare step4 missing after duplicate")
  helpers.assert_true(has_step(data.lanes.SNARE, 1, 12), "bar1 snare step12 missing after duplicate")
  helpers.assert_true(not has_step(data.lanes.SNARE, 1, 15), "bar1's own original note15 should have been replaced, not merged")

  -- Bar 0 itself must be untouched.
  helpers.assert_eq(count_notes(data.lanes.KICK), 4, "KICK should have 2 bar0 + 2 bar1 notes")
end)

t.case("duplicate_bar_forward: rejects the last bar as a source", function()
  local _fx, data = build_fixture()
  local ok, err = step_editor.duplicate_bar_forward(data, data.bars - 1)
  helpers.assert_true(ok == false, "duplicating the last bar should fail")
  helpers.assert_true(err ~= nil, "should return an error message")
end)

t.case("swap_articulation: accepts a same-family target and commits the new pitch", function()
  local fx, data = build_fixture()
  local closed_count = count_notes(data.lanes.CLOSED_HH)

  local ok, err = step_editor.swap_articulation(data, { "CLOSED_HH" }, "PEDAL_HH")
  helpers.assert_true(ok, "same-family swap failed: " .. tostring(err))
  step_editor.commit(fx.item, data)

  helpers.assert_eq(count_notes(data.lanes.PEDAL_HH), closed_count, "PEDAL_HH should receive every swapped note")

  local pitches = pitches_in_take(fx)
  local has_44 = false
  for _, p in ipairs(pitches) do
    if p == 44 then has_44 = true end
  end
  helpers.assert_true(has_44, "committed take should contain the new PEDAL_HH pitch (44)")
end)

t.case("qn_to_ppq: converts exact quarter-notes to take-local ppq", function()
  local _fx, data = build_fixture()
  helpers.assert_eq(step_editor.qn_to_ppq(data, 0.0), 0, "qn 0.0")
  helpers.assert_eq(step_editor.qn_to_ppq(data, 2.0), 2.0 * data.ppq_per_qn, "qn 2.0")
end)

t.case("serialize_pattern_json / parse_pattern_json: round-trips the whole pattern", function()
  local _fx, data = build_fixture()

  local json = step_editor.serialize_pattern_json(data)
  local notes = step_editor.parse_pattern_json(json)

  local total = count_notes(data.lanes.KICK) + count_notes(data.lanes.SNARE)
    + count_notes(data.lanes.CLOSED_HH) + count_notes(data.lanes.unmapped_50)
  helpers.assert_eq(#notes, total, "parsed note count should match the whole loaded pattern")

  local found_kick_at_2 = false
  for _, n in ipairs(notes) do
    if n.instrument == "KICK" and math.abs(n.position_qn - 2.0) < 0.001 then
      found_kick_at_2 = true
      helpers.assert_eq(n.velocity, 100, "serialized KICK velocity")
    end
  end
  helpers.assert_true(found_kick_at_2, "KICK note at qn 2.0 missing from round-trip")
end)

t.case("snapshot_pattern: matches parse_pattern_json's shape without a JSON round-trip", function()
  local _fx, data = build_fixture()

  local snapshot = step_editor.snapshot_pattern(data)
  local via_json = step_editor.parse_pattern_json(step_editor.serialize_pattern_json(data))

  helpers.assert_eq(#snapshot, #via_json, "snapshot_pattern note count should match the JSON round-trip")

  local found_kick_at_2 = false
  for _, n in ipairs(snapshot) do
    if n.instrument == "KICK" and math.abs(n.position_qn - 2.0) < 0.001 then
      found_kick_at_2 = true
      helpers.assert_eq(n.velocity, 100, "snapshot KICK velocity")
    end
  end
  helpers.assert_true(found_kick_at_2, "KICK note at qn 2.0 missing from snapshot")
end)

t.case("snapshot_pattern + replace_pattern: round-trips as a revert", function()
  local fx, data = build_fixture()

  local snapshot = step_editor.snapshot_pattern(data)
  local before_kick = count_notes(data.lanes.KICK)
  local before_snare = count_notes(data.lanes.SNARE)

  -- Simulate an Apply Drummer run that changes the pattern...
  step_editor.replace_pattern(data, {
    { instrument = "KICK", position_qn = 0.0, velocity = 90 },
  })
  step_editor.commit(fx.item, data)
  helpers.assert_eq(count_notes(data.lanes.KICK), 1, "sanity: replace_pattern should have shrunk KICK")

  -- ...then revert using the snapshot taken before that run.
  local ok = step_editor.replace_pattern(data, snapshot)
  helpers.assert_true(ok, "replace_pattern (revert) returned false")
  step_editor.commit(fx.item, data)

  helpers.assert_eq(count_notes(data.lanes.KICK), before_kick, "KICK should be restored after revert")
  helpers.assert_eq(count_notes(data.lanes.SNARE), before_snare, "SNARE should be restored after revert")
end)

t.case("parse_pattern_json: an empty array parses to an empty list, not an error", function()
  local notes = step_editor.parse_pattern_json("[]")
  helpers.assert_eq(#notes, 0, "empty JSON array should parse to zero notes")
end)

t.case("replace_pattern: replaces the whole pattern across every lane", function()
  local fx, data = build_fixture()

  local notes = {
    { instrument = "KICK", position_qn = 0.0, velocity = 90 },
    { instrument = "KICK", position_qn = 1.5, velocity = 95 },
    -- SNARE deliberately omitted - replace_pattern must empty it out,
    -- not leave its old bar0 notes in place.
  }
  local ok = step_editor.replace_pattern(data, notes)
  helpers.assert_true(ok, "replace_pattern returned false")
  step_editor.commit(fx.item, data)

  helpers.assert_eq(count_notes(data.lanes.KICK), 2, "KICK should have exactly the 2 replacement notes")
  helpers.assert_eq(count_notes(data.lanes.SNARE), 0, "SNARE should be emptied by replace_pattern")

  local kick_steps = {}
  for _, n in ipairs(data.lanes.KICK.notes) do
    kick_steps[#kick_steps + 1] = n.step
  end
  table.sort(kick_steps)
  helpers.assert_eq(kick_steps[1], 0, "first replacement KICK step")
  helpers.assert_eq(kick_steps[2], 6, "second replacement KICK step (qn 1.5 at 16th grid)")
end)

t.case("replace_pattern: creates a lane on demand from the kit map", function()
  local fx, data = build_fixture()
  helpers.assert_true(data.lanes.OPEN_HH == nil, "fixture should start with no OPEN_HH lane")

  local notes = { { instrument = "OPEN_HH", position_qn = 0.0, velocity = 90 } }
  local ok = step_editor.replace_pattern(data, notes)
  helpers.assert_true(ok, "replace_pattern returned false")
  step_editor.commit(fx.item, data)

  helpers.assert_true(data.lanes.OPEN_HH ~= nil, "OPEN_HH lane should be created on demand")
  helpers.assert_eq(count_notes(data.lanes.OPEN_HH), 1, "OPEN_HH note count")
end)

t.case("replace_pattern: an instrument absent from the kit map is silently dropped", function()
  local fx, data = build_fixture()

  local notes = { { instrument = "not_a_real_lane", position_qn = 0.0, velocity = 90 } }
  local ok = step_editor.replace_pattern(data, notes)
  helpers.assert_true(ok, "replace_pattern returned false")
  step_editor.commit(fx.item, data)

  helpers.assert_true(data.lanes.not_a_real_lane == nil, "unknown lane must not be created")
end)

t.finish()
