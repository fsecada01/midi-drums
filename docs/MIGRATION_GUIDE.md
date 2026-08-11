# Migration Guide: Pre-DDD Import Paths

> If your code imports `midi_drums` internals directly (rather than the
> top-level `midi_drums.DrumGenerator` / `midi_drums.api.python_api.DrumGeneratorAPI`
> surface, which never changed), use this table to update import paths after
> epic #8's domain re-organization. See
> [`DDD_ARCHITECTURE.md`](DDD_ARCHITECTURE.md) for *why* the layout changed.

## What Didn't Change

The top-level `midi_drums` package still exports the same names, backed by
the same classes:

```python
from midi_drums import DrumGenerator, Pattern, Beat, TimeSignature, Song, Section, GenerationParameters
```

If this is all you use, **no changes are needed**.

## Old Path → New Path

### Core models & value objects (#9)

| Old | New |
|-----|-----|
| `midi_drums.models.pattern.Pattern` / `.Beat` | `midi_drums.core.models.pattern.Pattern` / `.Beat` |
| `midi_drums.models.song.Song` / `.Section` / `.Fill` / `.PatternVariation` | `midi_drums.core.models.song.*` |
| `midi_drums.models.kit.DrumKit` / `.VelocityRange` | `midi_drums.core.models.kit.*` |
| `midi_drums.models.time_signature.TimeSignature` | `midi_drums.core.value_objects.time_signature.TimeSignature` |
| `midi_drums.models.drum_instrument.DrumInstrument` | `midi_drums.core.value_objects.drum_instrument.DrumInstrument` |
| `midi_drums.models.generation_parameters.GenerationParameters` | `midi_drums.core.value_objects.generation_parameters.GenerationParameters` |

### MIDI & Reaper export (#10)

| Old | New |
|-----|-----|
| `midi_drums.engines.midi_engine.MIDIEngine` | `midi_drums.export.midi.engine.MIDIEngine` |
| `midi_drums.engines.reaper_engine.ReaperEngine` / `bars_to_seconds` | `midi_drums.export.reaper.engine.*` |
| `midi_drums.exporters.reaper_exporter.ReaperExporter` | `midi_drums.export.reaper.exporter.ReaperExporter` (or keep using `midi_drums.exporters.ReaperExporter` — that shim is permanent) |
| `midi_drums.models.reaper_models.*` (`Marker`, `ReaperTrack`, `SectionTemplate`, `GenreStructurePreset`, ...) | `midi_drums.export.reaper.models.*` |

New in this phase, no old equivalent: `midi_drums.export.midi.exporter.MIDIExporter`
(high-level API wrapping `MIDIEngine`).

### Plugin system (#11)

| Old | New |
|-----|-----|
| `midi_drums.plugins.base.GenrePlugin` | `midi_drums.plugins.interfaces.genre_plugin.GenrePlugin` (or keep using `midi_drums.plugins.base.GenrePlugin` — that shim is permanent) |
| `midi_drums.plugins.base.DrummerPlugin` | `midi_drums.plugins.interfaces.drummer_plugin.DrummerPlugin` (shim permanent) |
| `midi_drums.plugins.base.PluginRegistry` / `.PluginManager` | `midi_drums.plugins.registry.plugin_registry.*` (shim permanent) |
| `midi_drums.plugins.drummers.composite_doom_blues.CompositeDoomBluesPlugin` | `midi_drums.plugins.drummers.composite.doom_blues.CompositeDoomBluesPlugin` |

New in this phase: `midi_drums.plugins.registry.discovery.PluginDiscovery`
(auto-discovery split out of `plugin_registry.py`).

### Generation engine & builder (#12)

| Old | New |
|-----|-----|
| `midi_drums.core.engine.DrumGenerator` | `midi_drums.generation.engines.drum_generator.DrumGenerator` |
| `midi_drums.core.builders.pattern_builder.PatternBuilder` | `midi_drums.generation.builders.pattern_builder.PatternBuilder` |

New in this phase, no old equivalent:
`midi_drums.generation.strategies.pattern_strategy.PatternStrategy` and
`.fill_strategy.FillStrategy` (ABC interfaces, no built-in implementations
yet), `midi_drums.generation.services.generation_service.GenerationService`
(thin orchestration wrapper over `DrumGenerator`).

## Which Shims Are Permanent vs. Which Paths Are Gone

- **Permanent compat shims** (safe to keep using indefinitely):
  `midi_drums.exporters.ReaperExporter`, `midi_drums.plugins.base.{GenrePlugin,DrummerPlugin,PluginRegistry,PluginManager}`.
- **Removed outright** (no shim, must update): everything under the old
  `midi_drums.models.*`, `midi_drums.engines.*`, `midi_drums.core.engine`,
  `midi_drums.core.builders.*`, and `midi_drums.plugins.drummers.composite_doom_blues`
  paths. Importing any of these now raises `ModuleNotFoundError`.

## Verifying Your Own Code

The domain-migration test suites double as a living spec of what's importable
from where — if you're unsure whether a path still exists, check the
relevant one directly:

- `tests/unit/core/test_core_domain_migration.py`
- `tests/unit/export/test_export_domain_migration.py`
- `tests/unit/plugins/test_plugin_domain_migration.py`
- `tests/unit/generation/test_generation_domain_migration.py`
