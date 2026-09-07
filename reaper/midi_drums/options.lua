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
}

function M.build_cmd(python_exe)
  return string.format('"%s" -m midi_drums list options', python_exe)
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

return M
