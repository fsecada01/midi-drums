# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive MIDI drum generation system with a modular, plugin-based architecture. It supports multiple genres, styles, drummer imitations, and song structures. The system evolved from a simple single-file metal generator (`generate_metal_drum_track.py`) into a full-featured, extensible platform.

### Key Features
- **Multi-Genre Support**: Metal (heavy, death, power, progressive, doom), expandable to rock, jazz, electronic
- **Drummer Imitation**: Plugin system for applying characteristic styles of famous drummers
- **Song Structure**: Configurable sections (verse, chorus, bridge, breakdown, intro, outro)
- **Pattern Variations**: Humanization, fills, complexity control, and dynamic variations
- **Multiple Interfaces**: Python API, CLI, and direct module usage
- **Plugin Architecture**: Easily extensible for new genres and drummers
- **Professional Output**: EZDrummer 3 compatible MIDI with realistic velocity and timing

## Development Setup

```bash
# Activate virtual environment
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Update dependencies from .in files
bin/py_update.bat       # Windows
bin/py_update.sh        # Linux/macOS

# Run linting tools
bin/linting.bat         # Windows
bin/linting.sh          # Linux/macOS

# Quick test - generate using new API
python examples/basic_usage.py

# Generate using CLI interface
python -m midi_drums generate --genre metal --style heavy --tempo 155 --output song.mid

# Run comprehensive architecture tests
python test_new_architecture.py

# Compare old vs new architecture
python migrate_from_original.py

# Run unit tests (when implemented)
pytest
```

## Architecture Overview

The system uses a layered, plugin-based architecture following SOLID principles:

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                │
│  CLI Interface │ Python API │ Direct Module Usage │ REST (future)│
├─────────────────────────────────────────────────────────────────┤
│                    Application Layer                            │
│  DrumGenerator │ Composition Engine │ Pattern Manager           │
├─────────────────────────────────────────────────────────────────┤
│                    Plugin System                                │
│  Genre Plugins │ Drummer Plugins │ Auto-Discovery │ Registry    │
├─────────────────────────────────────────────────────────────────┤
│                      Core Models                                │
│  Pattern │ Beat │ Song │ Section │ Kit │ GenerationParameters   │
├─────────────────────────────────────────────────────────────────┤
│                 Processing Engines                              │
│  MIDI Engine │ Humanization │ Pattern Builder │ Variations     │
└─────────────────────────────────────────────────────────────────┘
```

### Package Structure
```
midi_drums/
├── __init__.py           # Main exports (DrumGenerator, Pattern, Song)
├── __main__.py           # CLI entry point
├── core/
│   ├── engine.py         # DrumGenerator - main composition engine
│   └── __init__.py
├── models/
│   ├── pattern.py        # Pattern, Beat, DrumInstrument, PatternBuilder
│   ├── song.py          # Song, Section, GenerationParameters
│   ├── kit.py           # DrumKit configurations (EZDrummer3, Metal, Jazz)
│   └── __init__.py
├── plugins/
│   ├── base.py          # GenrePlugin, DrummerPlugin, PluginManager
│   ├── genres/
│   │   └── metal.py     # MetalGenrePlugin with 7 styles
│   ├── drummers/        # Future drummer style plugins
│   └── __init__.py
├── engines/
│   ├── midi_engine.py   # MIDI file generation
│   └── __init__.py
├── api/
│   ├── python_api.py    # DrumGeneratorAPI - high-level interface
│   ├── cli.py           # Command-line interface
│   └── __init__.py
└── examples/            # Usage demonstrations
    └── basic_usage.py   # Complete examples
```

## Dependencies

### Core Requirements (core_requirements.in)
- **midiutil**: Core MIDI file generation library (only required dependency)

### Dev Requirements (dev_requirements.in)
- **black**: Code formatting
- **isort**: Import sorting
- **pytest**: Testing framework
- **pytest-cov**: Test coverage
- **ruff**: Fast Python linter

The project uses uv for dependency management with `.in` files that compile to `.txt` files for reproducible builds.

## Usage Examples

### Python API (Recommended)
```python
from midi_drums.api.python_api import DrumGeneratorAPI

api = DrumGeneratorAPI()

# Generate complete songs
song = api.create_song("metal", "death", tempo=180, complexity=0.8)
api.save_as_midi(song, "death_metal.mid")

# Metal-specific convenience method
metal_song = api.metal_song("progressive", tempo=140, complexity=0.9)
api.save_as_midi(metal_song, "prog_metal.mid")

# Generate individual patterns
pattern = api.generate_pattern("metal", "breakdown", "heavy")
api.save_pattern_as_midi(pattern, "breakdown.mid")

# Batch generation
specs = [
    {'genre': 'metal', 'style': 'death', 'tempo': 180},
    {'genre': 'metal', 'style': 'power', 'tempo': 160}
]
files = api.batch_generate(specs, "output_dir/")

# List available options
print("Genres:", api.list_genres())
print("Metal styles:", api.list_styles("metal"))
print("Drummers:", api.list_drummers())
```

### CLI Interface
```bash
# Generate complete songs
python -m midi_drums generate --genre metal --style death --tempo 180 --output song.mid
python -m midi_drums generate --genre metal --style progressive --complexity 0.9 --output prog.mid

# Generate single patterns
python -m midi_drums pattern --genre metal --section breakdown --bars 8 --output fill.mid

# List available options
python -m midi_drums list genres
python -m midi_drums list styles --genre metal
python -m midi_drums info

# Get help
python -m midi_drums --help
python -m midi_drums generate --help
```

### Direct Module Usage
```python
from midi_drums import DrumGenerator

# Direct engine usage
generator = DrumGenerator()

# Generate with custom structure
song = generator.create_song(
    genre="metal",
    style="heavy",
    tempo=155,
    structure=[
        ("intro", 4), ("verse", 8), ("chorus", 8),
        ("verse", 8), ("chorus", 8), ("bridge", 4),
        ("chorus", 8), ("outro", 4)
    ],
    complexity=0.7,
    humanization=0.3
)

generator.export_midi(song, "custom_song.mid")

# Pattern-level control
pattern = generator.generate_pattern("metal", "verse", style="death", bars=4)
if pattern:
    generator.export_pattern_midi(pattern, "death_verse.mid", tempo=180)
```

## Available Genres and Styles

### Metal Genre (MetalGenrePlugin)
- **heavy**: Classic heavy metal patterns (Sabbath, Iron Maiden style)
- **death**: Blast beats, double bass, intense patterns
- **power**: Anthemic, driving patterns with melodic elements
- **progressive**: Complex time signatures and syncopation
- **thrash**: Fast, aggressive patterns with emphasis on precision
- **doom**: Slow, heavy, powerful patterns
- **breakdown**: Syncopated patterns for breakdown sections

### Future Expandability
The plugin system is designed for easy addition of:
- **Rock**: classic, blues, punk, alternative, progressive
- **Jazz**: swing, bebop, fusion, latin
- **Electronic**: house, techno, drum'n'bass, dubstep
- **World**: latin, reggae, afrobeat, etc.

## Plugin Development Guide

### Creating a Genre Plugin
```python
from midi_drums.plugins.base import GenrePlugin
from midi_drums.models.pattern import PatternBuilder, DrumInstrument
from midi_drums.models.song import GenerationParameters, Fill

class RockGenrePlugin(GenrePlugin):
    @property
    def genre_name(self) -> str:
        return "rock"

    @property
    def supported_styles(self) -> List[str]:
        return ["classic", "blues", "punk", "alternative", "progressive"]

    def generate_pattern(self, section: str, parameters: GenerationParameters) -> Pattern:
        builder = PatternBuilder(f"rock_{parameters.style}_{section}")

        if parameters.style == "classic":
            return self._classic_rock_pattern(builder, section, parameters)
        elif parameters.style == "blues":
            return self._blues_rock_pattern(builder, section, parameters)
        # ... other styles

    def get_common_fills(self) -> List[Fill]:
        # Return rock-specific fills
        return []

    def _classic_rock_pattern(self, builder, section, params):
        # Implement classic rock patterns
        builder.kick(0.0, 105).kick(2.0, 105)
        builder.snare(1.0, 110).snare(3.0, 110)
        # Add hi-hat pattern
        for i in range(8):
            builder.hihat(i * 0.5, 80)
        return builder.build()
```

### Creating a Drummer Plugin
```python
from midi_drums.plugins.base import DrummerPlugin
from midi_drums.models.pattern import Pattern, Beat, DrumInstrument

class BonhamPlugin(DrummerPlugin):
    @property
    def drummer_name(self) -> str:
        return "bonham"

    @property
    def compatible_genres(self) -> List[str]:
        return ["rock", "metal", "blues"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        # Apply Bonham's characteristic modifications
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_bonham"

        # Add triplet feels, ghost notes, powerful accents
        # Modify kick patterns, add signature fills

        return styled_pattern

    def get_signature_fills(self) -> List[Fill]:
        # Return Bonham's signature fills (Moby Dick, etc.)
        return []
```

## Key Design Patterns

### Strategy Pattern
- Genre and drummer plugins implement strategy interfaces
- Allows runtime selection of generation algorithms
- Easy to add new styles without modifying core code

### Builder Pattern
- `PatternBuilder` provides fluent API for pattern creation
- Separates pattern construction from representation
- Makes pattern creation code more readable

### Factory Pattern
- `PluginManager` acts as factory for plugin instances
- `DrumKit.create_*_kit()` methods for kit configurations
- Centralizes object creation logic

### Observer Pattern (Future)
- Real-time generation can notify listeners of pattern changes
- Event system for plugin lifecycle management

## Testing Strategy

### Current Tests
- `test_new_architecture.py`: Comprehensive integration tests
- Tests import system, pattern creation, plugin functionality, MIDI export

### Future Test Structure
```
tests/
├── unit/
│   ├── test_models.py       # Pattern, Song, Beat models
│   ├── test_plugins.py      # Plugin system
│   ├── test_engines.py      # MIDI engine
│   └── test_api.py          # API interfaces
├── integration/
│   ├── test_generation.py   # End-to-end generation
│   ├── test_cli.py          # CLI interface
│   └── test_plugins_integration.py
└── fixtures/
    ├── expected_outputs/    # Reference MIDI files
    └── test_patterns.py     # Test pattern data
```

## Migration from Original

### Preserved Compatibility
- Original `generate_metal_drum_track.py` still works unchanged
- `migrate_from_original.py` demonstrates equivalent functionality
- Same EZDrummer 3 MIDI mapping and output format

### Enhanced Capabilities
- **Extensibility**: Plugin system vs hardcoded patterns
- **Flexibility**: Configurable song structures vs fixed arrangement
- **Variety**: Multiple metal styles vs single heavy metal pattern
- **API**: Multiple interfaces vs single-use script
- **Quality**: Humanization, variations, professional patterns

### Migration Path
1. Use `DrumGeneratorAPI.metal_song()` for drop-in replacement
2. Gradually adopt new features (styles, complexity, humanization)
3. Extend with custom plugins as needed

## Performance Considerations

- **Plugin Loading**: Lazy loading of plugins reduces startup time
- **Pattern Caching**: Future enhancement for repeated generations
- **Memory Efficiency**: Patterns use efficient data structures
- **MIDI Generation**: Direct midiutil usage avoids intermediate representations

## Future Development Priorities

### Phase 1: Core Expansion
1. **Rock Genre Plugin**: Complete rock genre with 5+ styles
2. **Jazz Genre Plugin**: Swing, bebop, fusion styles
3. **Drummer Plugins**: Bonham, Peart, Baker, Rich implementations
4. **Real-time Generation**: Live performance capabilities

### Phase 2: Advanced Features
1. **Audio Engine**: Real audio synthesis alongside MIDI
2. **Pattern Variations**: AI-driven pattern evolution
3. **Groove Templates**: Preset combinations for quick generation
4. **Advanced Humanization**: Machine learning-based timing

### Phase 3: Integration
1. **REST API**: Web service for remote generation
2. **DAW Integration**: VST/AU plugin for direct DAW use
3. **Pattern Marketplace**: Community-contributed patterns
4. **Visual Interface**: GUI for pattern visualization and editing

## Common Development Tasks

### Adding a New Metal Style
1. Edit `midi_drums/plugins/genres/metal.py`
2. Add style to `supported_styles` property
3. Implement `_[style]_metal_[section]()` methods
4. Add tests for new style patterns

### Adding a New Genre
1. Create `midi_drums/plugins/genres/[genre].py`
2. Implement `GenrePlugin` interface
3. Add to plugin discovery system
4. Create comprehensive test suite

### Adding MIDI Export Features
1. Extend `midi_drums/engines/midi_engine.py`
2. Add new export methods to `MIDIEngine`
3. Update `DrumGeneratorAPI` with new interfaces
4. Add CLI commands if needed

### Debugging Plugin Issues
1. Check plugin loading with `DrumGenerator().get_available_genres()`
2. Use `test_new_architecture.py` for systematic testing
3. Enable logging in `midi_drums.plugins.base` module
4. Test plugin isolation with unit tests