-- reaper/midi_drums/options.lua
-- Live-queried genre/drummer/style/mapping option lists for the panel's
-- Genre/Style/Drummer/Mapping dropdowns. Genre, Drummer, and (therefore)
-- Style are plugin-discovered at runtime (see PluginDiscovery), not a
-- fixed compile-time set - a hardcoded Lua list would go stale the same
-- way this repo's own CLAUDE.md already had (missing the "electronic"
-- genre and 3 of 10 drummers), so this module shells out to
-- `python -m midi_drums list options` instead of hardcoding one.
--
-- Mapping presets and the riff-lock Grid values ARE genuinely static
-- (see DrumKit.preset_map / cli.py's --grid choices) - Mapping still
-- rides this same cache for convenience, since the CLI already reports
-- it in the same JSON payload, but Grid is built as a separate hardcoded
-- combo in the panel itself.
local M = {}

M.cache = {
  genres = {},
  drummers = {},
  mappings = {},
  genre_styles = {}, -- flat list of {genre = ..., style = ...}
  loaded = false,
  error = nil,

  -- Per-mapping note map for the Step Editor panel (ADR 0009), keyed by
  -- mapping name and lazily fetched on demand rather than eagerly for
  -- every preset up front - unlike genres/drummers/mappings above,
  -- there's no single combo box that needs every mapping's note table
  -- loaded at once. Each entry is
  -- {notes = {...}, loaded = true/false, error = nil}.
  kit_maps = {},
}

function M.build_cmd(python_exe)
  return string.format('"%s" -m midi_drums list options', python_exe)
end

-- Same shell-arg sanitizing as sections.lua/riff_lock.lua/
-- additive_rhythm.lua's own M.shell_escape (duplicated per-module in
-- this codebase rather than shared via dofile - see those modules).
-- `mapping` comes from a dropdown, not free text, but every other
-- --mapping-carrying command still escapes it, so this does too.
function M.shell_escape(s)
  s = s:gsub("[\r\n]", " ")
  s = s:gsub('"', "'")
  s = s:gsub("[&|^<>%%]", "")
  return s
end

-- `list kit-map --mapping <preset>` - a given mapping preset's resolved
-- note table (see DrumKit.kit_map()), for the Step Editor panel instead
-- of a hardcoded Lua drum-note table (same rationale as M.build_cmd
-- above, applied to note mappings rather than genre/drummer/style).
function M.build_kit_map_cmd(python_exe, mapping)
  return string.format(
    '"%s" -m midi_drums list kit-map --mapping "%s"',
    python_exe, M.shell_escape(mapping)
  )
end

-- Flat-array parsing, mirroring sections.lua's parse_sidecar/
-- parse_timeline - no JSON library, just gmatch over the known flat
-- shape the "options" JSON always uses (see cli.py's
-- handle_list_command "options" branch: genres/drummers/mappings are
-- flat string arrays, genre_styles is a flat array of {genre, style}
-- objects rather than a nested genre -> [styles] map).
function M.parse(content)
  local function string_array(key)
    local out = {}
    local block = content:match('"' .. key .. '"%s*:%s*%[(.-)%]')
    if block then
      for name in block:gmatch('"([^"]*)"') do
        out[#out + 1] = name
      end
    end
    return out
  end

  local genres = string_array("genres")
  local drummers = string_array("drummers")
  local mappings = string_array("mappings")

  local genre_styles = {}
  for genre, style in content:gmatch(
    '"genre"%s*:%s*"([^"]*)"%s*,%s*"style"%s*:%s*"([^"]*)"'
  ) do
    genre_styles[#genre_styles + 1] = { genre = genre, style = style }
  end

  if #genres == 0 then
    return nil, "Could not parse 'genres' from options JSON."
  end

  return {
    genres = genres,
    drummers = drummers,
    mappings = mappings,
    genre_styles = genre_styles,
  }
end

-- Styles available for `genre`, sorted the same way the CLI already
-- sorted them. Returns {} (not nil) for an unknown/not-yet-loaded genre
-- so callers can always iterate the result directly.
function M.styles_for(genre)
  local out = {}
  for _, gs in ipairs(M.cache.genre_styles) do
    if gs.genre == genre then
      out[#out + 1] = gs.style
    end
  end
  return out
end

-- Parses `list kit-map --mapping <preset>`'s JSON (see
-- DrumKit.kit_map() / cli.py's handle_list_command "kit-map" branch):
-- {"mapping": "...", "notes": [{"note": N, "instrument": "...",
-- "label": "...", "group": "...", "family": "...",
-- "default_velocity": N}, ...]}. Same no-JSON-library, fixed-key-order
-- gmatch approach as M.parse - relies on DrumKit.kit_map() always
-- building each note dict in this exact key order (Python dicts
-- preserve insertion order, and json.dumps doesn't reorder them), same
-- assumption M.parse already makes about the "options" JSON's shape.
function M.parse_kit_map(content)
  local mapping = content:match('"mapping"%s*:%s*"([^"]*)"')

  local notes = {}
  for note, instrument, label, group, family, default_velocity in
    content:gmatch(
      '"note"%s*:%s*(%d+)%s*,%s*"instrument"%s*:%s*"([^"]*)"%s*,'
        .. '%s*"label"%s*:%s*"([^"]*)"%s*,%s*"group"%s*:%s*"([^"]*)"%s*,'
        .. '%s*"family"%s*:%s*"([^"]*)"%s*,'
        .. '%s*"default_velocity"%s*:%s*(%d+)'
    )
  do
    notes[#notes + 1] = {
      note = tonumber(note),
      instrument = instrument,
      label = label,
      group = group,
      family = family,
      default_velocity = tonumber(default_velocity),
    }
  end

  if #notes == 0 then
    return nil, "Could not parse 'notes' from kit-map JSON."
  end

  return { mapping = mapping, notes = notes }
end

-- Note table for `mapping`, from the lazily-populated per-mapping cache.
-- Returns {} (not nil) for a mapping that hasn't been fetched yet (or
-- failed to parse) so callers can always iterate the result directly,
-- same convention as M.styles_for. Callers that need to distinguish
-- "not yet loaded" from "loaded but empty" should check
-- M.cache.kit_maps[mapping] directly instead.
function M.kit_map_for(mapping)
  local entry = M.cache.kit_maps[mapping]
  if not entry or not entry.loaded then
    return {}
  end
  return entry.notes
end

return M
