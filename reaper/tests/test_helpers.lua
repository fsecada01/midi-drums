-- reaper/tests/test_helpers.lua
-- Tiny assert-based test runner shared by every reaper/tests/test_*.lua
-- file - no external dependency, just enough structure (named cases,
-- a pass/fail tally, a nonzero exit code on failure) to work as a CI
-- gate via `lua reaper/tests/test_step_editor.lua`.
local M = {}

function M.new()
  local runner = { passed = 0, failed = 0, failures = {} }

  function runner.case(name, fn)
    local ok, err = pcall(fn)
    if ok then
      runner.passed = runner.passed + 1
      print("  ok   - " .. name)
    else
      runner.failed = runner.failed + 1
      runner.failures[#runner.failures + 1] = { name = name, err = err }
      print("  FAIL - " .. name)
      print("         " .. tostring(err))
    end
  end

  function runner.finish()
    print(string.format("\n%d passed, %d failed", runner.passed, runner.failed))
    if runner.failed > 0 then
      os.exit(1)
    end
  end

  return runner
end

function M.assert_eq(actual, expected, msg)
  if actual ~= expected then
    error(string.format(
      "%s: expected %s, got %s",
      msg or "assert_eq", tostring(expected), tostring(actual)
    ), 2)
  end
end

function M.assert_true(value, msg)
  if not value then
    error(msg or "assert_true failed", 2)
  end
end

function M.assert_nil(value, msg)
  if value ~= nil then
    error((msg or "assert_nil failed") .. ": got " .. tostring(value), 2)
  end
end

return M
