# reaper/tests

Automated Lua tests for `reaper/midi_drums/step_editor.lua`, run against a
fake in-memory REAPER environment instead of live REAPER. This supersedes
ADR 0001's "no automated Lua test runner exists" v1 caveat for this module.

## Requirements

A Lua 5.4 interpreter on PATH (matches REAPER's embedded Lua version).
On Windows without admin rights: `winget install --id DEVCOM.Lua --scope user`.

## Running

```bash
lua reaper/tests/test_step_editor.lua
```

Exits nonzero if any case fails - safe to wire into CI.

For a fast syntax-only check of every panel/module file (no execution,
useful since `midi_drums_panel.lua` itself needs live REAPER globals and
can't be run standalone):

```bash
luac -p reaper/midi_drums_panel.lua
for f in reaper/midi_drums/*.lua; do luac -p "$f"; done
```

## Files

- `fake_reaper.lua` - minimal in-memory stand-in for the slice of the
  ReaScript API `step_editor.lua` touches (MIDI note CRUD, QN/PPQ
  conversions, Undo_BeginBlock/EndBlock). Assumes constant tempo/time
  signature. Installs itself as the global `reaper`.
- `test_helpers.lua` - tiny pcall-based test runner (`runner.case`,
  `assert_eq`/`assert_true`/`assert_nil`, `runner.finish()`).
- `test_step_editor.lua` - the actual test suite.

## Scope

Only `step_editor.lua` is covered so far. `midi_drums_panel.lua` and the
other business-logic modules (`sections.lua`, `riff_lock.lua`, etc.) are
still unverified beyond `luac -p` syntax checks - they either render UI
(untestable outside REAPER's ImGui context) or call `job_runner.start()`
against a real subprocess, neither of which the fake environment models.
