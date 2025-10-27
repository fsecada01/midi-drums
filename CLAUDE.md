# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive MIDI drum generation system with a modular, plugin-based architecture. It supports multiple genres, styles, drummer imitations, and song structures. The system evolved from a simple single-file metal generator (`generate_metal_drum_track.py`) into a full-featured, extensible platform.

### Key Features
- **Multi-Genre Support**: Metal (7 styles), Rock (7 styles), Jazz (7 styles), Funk (7 styles), expandable to electronic
- **Drummer Imitation**: 7 drummer plugins with authentic styles (Bonham, Porcaro, Weckl, Chambers, Roeder, Dee, Hoglan)
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
│   │   ├── metal.py     # MetalGenrePlugin with 7 styles
│   │   ├── rock.py      # RockGenrePlugin with 7 styles
│   │   ├── jazz.py      # JazzGenrePlugin with 7 styles
│   │   └── funk.py      # FunkGenrePlugin with 7 styles
│   ├── drummers/        # 7 drummer style plugins
│   │   ├── bonham.py    # John Bonham - triplets, behind-beat
│   │   ├── porcaro.py   # Jeff Porcaro - shuffle, ghost notes
│   │   ├── weckl.py     # Dave Weckl - linear, fusion
│   │   ├── chambers.py  # Dennis Chambers - funk mastery
│   │   ├── roeder.py    # Jason Roeder - atmospheric sludge
│   │   ├── dee.py       # Mikkey Dee - speed/precision
│   │   └── hoglan.py    # Gene Hoglan - blast beats
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
print("Genres:", api.list_genres())  # ['metal', 'rock', 'jazz', 'funk']
print("Rock styles:", api.list_styles("rock"))  # 7 rock styles
print("Jazz styles:", api.list_styles("jazz"))  # 7 jazz styles
print("Drummers:", api.list_drummers())  # 7 drummer personalities
```

### CLI Interface
```bash
# Generate complete songs across genres
python -m midi_drums generate --genre metal --style death --tempo 180 --output song.mid
python -m midi_drums generate --genre rock --style classic --drummer bonham --output rock_song.mid
python -m midi_drums generate --genre jazz --style swing --drummer weckl --output jazz_song.mid
python -m midi_drums generate --genre funk --style classic --drummer chambers --output funk_song.mid

# Generate single patterns with drummer styles
python -m midi_drums pattern --genre rock --section verse --style blues --drummer porcaro --output verse.mid
python -m midi_drums pattern --genre jazz --section bridge --style fusion --drummer weckl --output bridge.mid

# List available options
python -m midi_drums list genres  # metal, rock, jazz, funk
python -m midi_drums list styles --genre jazz  # 7 jazz styles
python -m midi_drums list drummers  # 7 drummer personalities
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

### Rock Genre (RockGenrePlugin)
- **classic**: 70s classic rock (Led Zeppelin, Deep Purple)
- **blues**: Blues rock with shuffles and triplets
- **alternative**: 90s alternative rock syncopation
- **progressive**: Complex progressive rock patterns
- **punk**: Fast, aggressive punk rock
- **hard**: Hard rock with heavy emphasis
- **pop**: Pop rock with clean patterns

### Jazz Genre (JazzGenrePlugin)
- **swing**: Traditional swing with ride patterns
- **bebop**: Fast, complex bebop rhythms
- **fusion**: Jazz fusion with electric energy
- **latin**: Latin jazz with clave patterns
- **ballad**: Soft, brushed ballad patterns
- **hard_bop**: Aggressive hard bop rhythms
- **contemporary**: Modern contemporary jazz

### Funk Genre (FunkGenrePlugin)
- **classic**: James Brown "the one" emphasis
- **pfunk**: Parliament-Funkadelic grooves
- **shuffle**: Bernard Purdie shuffle patterns
- **new_orleans**: Second line funk patterns
- **fusion**: Jazz-funk fusion styles
- **minimal**: Stripped-down pocket grooves
- **heavy**: Heavy funk with rock influence

### Available Drummers
- **John Bonham (bonham)**: Triplet vocabulary, behind-the-beat timing, guitar-following patterns
- **Jeff Porcaro (porcaro)**: Half-time shuffle mastery, ghost notes, studio precision
- **Dave Weckl (weckl)**: Linear playing, sophisticated coordination, fusion expertise
- **Dennis Chambers (chambers)**: Funk mastery, incredible chops, pocket stretching
- **Jason Roeder (roeder)**: Atmospheric sludge, minimal creativity, crushing weight
- **Mikkey Dee (dee)**: Speed/precision, versatile power, twisted backbeats
- **Gene Hoglan (hoglan)**: Mechanical precision, blast beats, progressive complexity

### Future Expandability
The plugin system is designed for easy addition of:
- **Electronic**: house, techno, drum'n'bass, dubstep
- **World**: latin, reggae, afrobeat, etc.
- **More Drummers**: Neil Peart, Buddy Rich, Stewart Copeland, etc.

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
- `test_all_drummer_plugins.py`: Complete drummer plugin validation
- `test_new_genre_plugins.py`: Genre plugin testing (Rock, Jazz, Funk)
- Tests: import system, pattern creation, plugin functionality, MIDI export, drummer compatibility

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

### Phase 1: Core Expansion ✅ COMPLETED
1. **Rock Genre Plugin**: ✅ Complete with 7 styles (classic, blues, alternative, progressive, punk, hard, pop)
2. **Jazz Genre Plugin**: ✅ Complete with 7 styles (swing, bebop, fusion, latin, ballad, hard_bop, contemporary)
3. **Funk Genre Plugin**: ✅ Complete with 7 styles (classic, pfunk, shuffle, new_orleans, fusion, minimal, heavy)
4. **Drummer Plugins**: ✅ 7 implemented (Bonham, Porcaro, Weckl, Chambers, Roeder, Dee, Hoglan)
5. **Comprehensive Testing**: ✅ Full test suites for all plugins and compatibility

### Phase 2: Advanced Features 🚧 IN PROGRESS
1. **Electronic Genre Plugin**: House, Techno, Drum'n'Bass, Dubstep styles
2. **More Drummer Plugins**: Neil Peart, Buddy Rich, Stewart Copeland
3. **Audio Engine**: Real audio synthesis alongside MIDI
4. **Pattern Variations**: AI-driven pattern evolution
5. **Groove Templates**: Preset combinations for quick generation
6. **Advanced Humanization**: Machine learning-based timing
7. **Real-time Generation**: Live performance capabilities

### Phase 3: Integration
1. **REST API**: Web service for remote generation
2. **DAW Integration**: VST/AU plugin for direct DAW use
3. **Pattern Marketplace**: Community-contributed patterns
4. **Visual Interface**: GUI for pattern visualization and editing

## Refactoring Achievement

### Project Overview
The MIDI Drums Generator underwent a comprehensive refactoring project that achieved **extraordinary code reduction** while maintaining 100% functional equivalence. The refactoring introduced reusable infrastructure systems that dramatically improved code quality, maintainability, and extensibility.

### Key Metrics

| Metric | Value |
|--------|-------|
| **Total Code Eliminated** | 2,898 lines (62% reduction from originals) |
| **Genre Plugins Reduction** | 2,046 → 1,289 lines (37% reduction, 757 lines saved) |
| **Drummer Plugins Reduction** | 2,592 → 451 lines (83% reduction!, 2,141 lines saved) |
| **Infrastructure Created** | 1,743 lines of reusable code |
| **Test Coverage Added** | 2,023 lines (39 comprehensive tests) |
| **Net Code Reduction** | 1,155 lines eliminated (25% after infrastructure) |
| **All Tests Passing** | 100% functional equivalence maintained |

### Refactored Architecture

The refactoring introduced three foundational systems that work together to eliminate code duplication:

#### 1. Configuration Constants (`midi_drums/config/constants.py`)
Eliminates magic numbers throughout the codebase with type-safe frozen dataclasses:

```python
from midi_drums.config import VELOCITY, TIMING, DEFAULTS

# Instead of magic numbers:
builder.kick(0.0, 105)  # What does 105 mean?

# Use descriptive constants:
builder.kick(0.0, VELOCITY.KICK_MEDIUM)  # Self-documenting!

# Available constant groups:
# - VELOCITY: 40+ velocity constants (KICK_SOFT, SNARE_ACCENT, HIHAT_GHOST, etc.)
# - TIMING: 25+ timing constants (QUARTER, EIGHTH, SIXTEENTH, TRIPLET, etc.)
# - DEFAULTS: 50+ default parameters (TEMPO, COMPLEXITY, HUMANIZATION, etc.)
```

#### 2. Pattern Template System (`midi_drums/patterns/templates.py`)
Provides 8 reusable pattern templates for declarative pattern composition:

```python
from midi_drums.patterns import TemplateComposer, BasicGroove, DoubleBassPedal, BlastBeat

# Declarative pattern composition instead of manual PatternBuilder construction
pattern = (
    TemplateComposer("death_metal_verse")
    .add(DoubleBassPedal(pattern="continuous", speed=16))
    .add(BlastBeat(style="traditional", intensity=0.9))
    .build(bars=2, complexity=0.8)
)

# Available templates:
# - BasicGroove: Standard kick + snare + hihat patterns
# - DoubleBassPedal: Continuous, gallop, and burst patterns
# - BlastBeat: Traditional, hammer, and gravity blast beats
# - JazzRidePattern: Swing ride patterns with accents
# - FunkGhostNotes: Ghost note layers for funk grooves
# - CrashAccents: Crash cymbal placement
# - TomFill: Descending, ascending, and accent fills
# - TemplateComposer: Combines multiple templates
```

#### 3. Drummer Modification Registry (`midi_drums/modifications/drummer_mods.py`)
Provides 12 composable modifications for authentic drummer techniques:

```python
from midi_drums.modifications import BehindBeatTiming, TripletVocabulary, HeavyAccents

# Composable modifications instead of duplicated pattern manipulation code
behind_beat = BehindBeatTiming(max_delay_ms=25.0)
triplets = TripletVocabulary(triplet_probability=0.4)
accents = HeavyAccents(accent_boost=15)

styled_pattern = pattern.copy()
styled_pattern = behind_beat.apply(styled_pattern, intensity=0.7)
styled_pattern = triplets.apply(styled_pattern, intensity=0.8)
styled_pattern = accents.apply(styled_pattern, intensity=0.9)

# Available modifications:
# - BehindBeatTiming: Delays hits behind beat (Bonham, Chambers)
# - TripletVocabulary: Triplet-based fills (Bonham)
# - GhostNoteLayer: Subtle ghost notes (Porcaro, Weckl, Chambers)
# - LinearCoordination: Removes simultaneous hits (Weckl)
# - HeavyAccents: Increases accent contrast (metal drummers)
# - ShuffleFeelApplication: Shuffle/swing feel (Porcaro)
# - FastChopsTriplets: Fast technical fills (Chambers)
# - PocketStretching: Subtle groove variations (Chambers)
# - MinimalCreativity: Sparse, atmospheric approach (Roeder)
# - SpeedPrecision: Consistent timing/velocity (Dee)
# - TwistedAccents: Displaced accents (Dee)
# - MechanicalPrecision: Extreme quantization (Hoglan)
```

### Refactored File Structure

```
midi_drums/
├── config/
│   ├── __init__.py
│   └── constants.py              # 283 lines - VELOCITY, TIMING, DEFAULTS
├── patterns/
│   ├── __init__.py
│   └── templates.py              # 585 lines - 8 pattern templates
├── modifications/
│   ├── __init__.py
│   └── drummer_mods.py           # 732 lines - 12 drummer modifications
├── plugins/
│   ├── genres/
│   │   ├── metal.py              # Original: 373 lines
│   │   ├── metal_refactored.py   # Refactored: 290 lines (22% reduction)
│   │   ├── rock.py               # Original: 513 lines
│   │   ├── rock_refactored.py    # Refactored: 332 lines (35% reduction)
│   │   ├── jazz.py               # Original: 599 lines
│   │   ├── jazz_refactored.py    # Refactored: 337 lines (44% reduction!)
│   │   ├── funk.py               # Original: 561 lines
│   │   └── funk_refactored.py    # Refactored: 330 lines (41% reduction)
│   └── drummers/
│       ├── bonham.py             # Original: 339 lines
│       ├── bonham_refactored.py  # Refactored: 66 lines (80% reduction!)
│       ├── porcaro.py            # Original: 369 lines
│       ├── porcaro_refactored.py # Refactored: 63 lines (83% reduction!)
│       ├── weckl.py              # Original: 383 lines
│       ├── weckl_refactored.py   # Refactored: 63 lines (84% reduction!)
│       ├── chambers.py           # Original: 381 lines
│       ├── chambers_refactored.py # Refactored: 70 lines (82% reduction!)
│       ├── roeder.py             # Original: 371 lines
│       ├── roeder_refactored.py  # Refactored: 63 lines (83% reduction!)
│       ├── dee.py                # Original: 360 lines
│       ├── dee_refactored.py     # Refactored: 63 lines (82% reduction!)
│       ├── hoglan.py             # Original: 389 lines
│       └── hoglan_refactored.py  # Refactored: 63 lines (84% reduction!)
└── claudedocs/
    └── REFACTORING_PROGRESS.md   # Complete refactoring documentation
```

### Example: Genre Plugin Refactoring

**Before** (manual pattern construction, ~50 lines per style):
```python
def _death_metal_verse(self, builder, params):
    # Manual kick pattern construction
    positions = [0.0, 0.25, 0.5, 0.75, 1.0, ...]
    for pos in positions:
        builder.kick(pos, 105)

    # Manual snare pattern construction
    builder.snare(1.0, 110).snare(3.0, 110)

    # Manual blast beat construction
    for i in range(16):
        builder.hihat(i * 0.25, 95)

    # ... 40 more lines of pattern construction
    return builder.build()
```

**After** (declarative composition, ~5 lines per style):
```python
def _death_metal_verse(self, name: str, complexity: float) -> Pattern:
    return (
        TemplateComposer(name)
        .add(DoubleBassPedal(pattern="continuous", speed=16))
        .add(BlastBeat(style="traditional", intensity=0.9))
        .build(bars=2, complexity=complexity)
    )
```

### Example: Drummer Plugin Refactoring

**Before** (manual pattern manipulation, ~380 lines):
```python
class BonhamPlugin(DrummerPlugin):
    def apply_style(self, pattern: Pattern) -> Pattern:
        styled_pattern = pattern.copy()

        # 50+ lines of behind-beat timing code
        for beat in styled_pattern.beats:
            if beat.instrument == DrumInstrument.SNARE:
                beat.position += 0.025  # Magic number!

        # 50+ lines of triplet feel code
        # ... manual triplet construction

        # 50+ lines of accent code
        # ... manual accent application

        # ... 200+ more lines of pattern manipulation

        return styled_pattern
```

**After** (composable modifications, ~66 lines):
```python
class BonhamPluginRefactored(DrummerPlugin):
    def __init__(self):
        self.behind_beat = BehindBeatTiming(max_delay_ms=25.0)
        self.triplets = TripletVocabulary(triplet_probability=0.4)
        self.accents = HeavyAccents(accent_boost=15)

    def apply_style(self, pattern: Pattern) -> Pattern:
        styled_pattern = pattern.copy()
        styled_pattern = self.behind_beat.apply(styled_pattern, intensity=0.7)
        styled_pattern = self.triplets.apply(styled_pattern, intensity=0.8)
        styled_pattern = self.accents.apply(styled_pattern, intensity=0.9)
        return styled_pattern
```

### Benefits Achieved

**Code Quality:**
- Zero code duplication across all refactored plugins
- Full type hints throughout infrastructure
- Self-documenting with descriptive constants
- All linting passing (ruff, black, isort)
- Immutable data structures for safety

**Maintainability:**
- Changes propagate through reusable systems
- Bug fixes in templates/modifications benefit all plugins
- Clear separation of concerns
- Easy to understand and modify

**Extensibility:**
- New genres easy to add using templates
- New drummers easy to add using modifications
- New templates/modifications extend capabilities
- Composable systems enable creativity

**Testing:**
- 100% functional equivalence validated
- All 39 tests passing
- Comprehensive test coverage (2,023 lines)
- Test-driven validation of equivalence

### Design Patterns Used

**Strategy Pattern**: Templates and modifications as composable strategies
**Builder Pattern**: TemplateComposer for fluent pattern composition
**Factory Pattern**: Convenience functions and registries for discovery
**Composition over Inheritance**: Mix and match templates/modifications

### Future Refactoring Opportunities

1. **Migrate Active Plugins**: Switch from original to refactored plugins in production
2. **Additional Templates**: Add templates for electronic genres, world music
3. **Template Variations**: Parameterized variations of existing templates
4. **Visual Builder**: UI for composing templates visually
5. **Template Marketplace**: Community-contributed templates and modifications

For complete refactoring documentation, see `claudedocs/REFACTORING_PROGRESS.md`.

## Common Development Tasks

### Adding a New Metal Style
1. Edit `midi_drums/plugins/genres/metal.py`
2. Add style to `supported_styles` property
3. Implement `_[style]_metal_[section]()` methods
4. Add tests for new style patterns

### Adding a New Genre
1. Create `midi_drums/plugins/genres/[genre].py`
2. Implement `GenrePlugin` interface with 7+ styles
3. Add to plugin discovery system
4. Create comprehensive test suite
5. Examples: Rock, Jazz, Funk genres with authentic patterns

### Adding a New Drummer
1. Create `midi_drums/plugins/drummers/[drummer].py`
2. Implement `DrummerPlugin` interface
3. Research authentic playing techniques and signature patterns
4. Add signature fills and style modifications
5. Test compatibility across multiple genres
6. Examples: 7 drummers with research-based implementations

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