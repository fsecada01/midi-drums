# 🥁 MIDI Drums Generator

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MIDI](https://img.shields.io/badge/Output-MIDI-purple.svg)](https://en.wikipedia.org/wiki/MIDI)
[![EZDrummer](https://img.shields.io/badge/Compatible-EZDrummer_3-orange.svg)](https://www.toontrack.com/product/ezdrummer-3/)

*A comprehensive, plugin-based MIDI drum track generation system*

[🚀 Quick Start](#-quick-start) • [📖 Documentation](#-documentation) • [🎵 Examples](#-examples) • [🔌 Plugins](#-plugin-system) • [🤝 Contributing](#-contributing)

</div>

---

## 🎯 Overview

MIDI Drums Generator is a powerful Python system that creates professional-quality drum tracks in MIDI format. Built with a modular, plugin-based architecture, it supports multiple musical genres, drummer styles, and song structures with realistic humanization and variations.

### ✨ Key Features

🎪 **Multi-Genre Support**
- **Metal**: Heavy, Death, Power, Progressive, Doom, Thrash, Breakdown
- **Expandable**: Plugin architecture for Rock, Jazz, Electronic, and more

🥁 **Drummer Imitation**
- Apply characteristic styles of famous drummers
- Signature fills and playing techniques
- Compatible across multiple genres

🏗️ **Flexible Song Structure**
- Configurable sections (verse, chorus, bridge, breakdown)
- Pattern variations and dynamic fills
- Custom song arrangements

🎛️ **Professional Features**
- Realistic velocity variations and humanization
- EZDrummer 3 compatible MIDI mapping
- Multiple complexity and dynamics levels

🔧 **Multiple Interfaces**
- Python API for integration
- Command-line interface for batch processing
- Direct module usage for custom applications

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/midi-drums.git
cd midi-drums

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r core_requirements.txt
```

### Generate Your First Drum Track

```python
from midi_drums.api.python_api import DrumGeneratorAPI

# Initialize the generator
api = DrumGeneratorAPI()

# Create a death metal song
song = api.create_song("metal", "death", tempo=180)
api.save_as_midi(song, "death_metal_track.mid")

print("🎵 Generated: death_metal_track.mid")
```

### Command Line Usage

```bash
# Generate a complete song
python -m midi_drums generate --genre metal --style heavy --tempo 155 --output metal_song.mid

# Generate a single pattern
python -m midi_drums pattern --genre metal --section breakdown --output breakdown.mid

# List available options
python -m midi_drums list genres
```

## 📖 Documentation

### Architecture

The system follows a layered, plugin-based architecture:

```
┌─────────────────────────────────────────┐
│           API Layer                     │
│  CLI │ Python API │ Direct Usage       │
├─────────────────────────────────────────┤
│        Application Layer                │
│  DrumGenerator │ Pattern Manager        │
├─────────────────────────────────────────┤
│         Plugin System                   │
│  Genre Plugins │ Drummer Plugins        │
├─────────────────────────────────────────┤
│         Core Models                     │
│  Pattern │ Song │ Beat │ Kit            │
├─────────────────────────────────────────┤
│         Processing Engines              │
│  MIDI Engine │ Humanization             │
└─────────────────────────────────────────┘
```

### Available Genres & Styles

#### 🤘 Metal Genre
- **Heavy**: Classic heavy metal (Sabbath, Iron Maiden style)
- **Death**: Blast beats, double bass, intense patterns
- **Power**: Anthemic, driving patterns with melodic elements
- **Progressive**: Complex time signatures and syncopation
- **Thrash**: Fast, aggressive patterns with precision
- **Doom**: Slow, heavy, powerful patterns
- **Breakdown**: Syncopated patterns for breakdown sections

#### 🔮 Future Genres
- **Rock**: Classic, Blues, Punk, Alternative, Progressive
- **Jazz**: Swing, Bebop, Fusion, Latin
- **Electronic**: House, Techno, Drum'n'Bass, Dubstep

## 🎵 Examples

### Python API Examples

```python
from midi_drums.api.python_api import DrumGeneratorAPI

api = DrumGeneratorAPI()

# Metal song with custom parameters
song = api.metal_song(
    style="progressive",
    tempo=140,
    complexity=0.9
)
api.save_as_midi(song, "prog_metal.mid")

# Batch generation
specs = [
    {'genre': 'metal', 'style': 'death', 'tempo': 180},
    {'genre': 'metal', 'style': 'power', 'tempo': 160},
    {'genre': 'metal', 'style': 'doom', 'tempo': 90}
]
files = api.batch_generate(specs, "output/")

# Individual patterns
verse = api.generate_pattern("metal", "verse", "heavy")
chorus = api.generate_pattern("metal", "chorus", "death")
breakdown = api.generate_pattern("metal", "breakdown", "heavy")
```

### Direct Module Usage

```python
from midi_drums import DrumGenerator

generator = DrumGenerator()

# Custom song structure
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
```

### CLI Examples

```bash
# Generate songs with different styles
python -m midi_drums generate --genre metal --style death --tempo 180 --complexity 0.8 --output death.mid
python -m midi_drums generate --genre metal --style power --tempo 160 --dynamics 0.9 --output power.mid

# Generate patterns for specific sections
python -m midi_drums pattern --genre metal --section verse --style progressive --bars 8 --output verse.mid
python -m midi_drums pattern --genre metal --section breakdown --style heavy --output breakdown.mid

# System information
python -m midi_drums info
python -m midi_drums list styles --genre metal
```

## 🔌 Plugin System

The plugin architecture makes it easy to extend the system with new genres and drummer styles.

### Creating a Genre Plugin

```python
from midi_drums.plugins.base import GenrePlugin
from midi_drums.models.pattern import PatternBuilder

class RockGenrePlugin(GenrePlugin):
    @property
    def genre_name(self) -> str:
        return "rock"

    @property
    def supported_styles(self) -> List[str]:
        return ["classic", "blues", "punk", "alternative"]

    def generate_pattern(self, section: str, parameters: GenerationParameters) -> Pattern:
        builder = PatternBuilder(f"rock_{parameters.style}_{section}")

        if parameters.style == "classic":
            # Classic rock pattern: kick on 1 & 3, snare on 2 & 4
            builder.kick(0.0, 105).kick(2.0, 105)
            builder.snare(1.0, 110).snare(3.0, 110)

            # Hi-hat eighths
            for i in range(8):
                builder.hihat(i * 0.5, 80)

        return builder.build()
```

### Creating a Drummer Plugin

```python
from midi_drums.plugins.base import DrummerPlugin

class BonhamPlugin(DrummerPlugin):
    @property
    def drummer_name(self) -> str:
        return "bonham"

    def apply_style(self, pattern: Pattern) -> Pattern:
        # Apply Bonham's characteristic triplet feels and powerful accents
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_bonham"

        # Add signature style modifications
        return self._add_bonham_characteristics(styled_pattern)
```

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
bin/py_update.sh  # Linux/macOS
bin/py_update.bat # Windows

# Run tests
python test_new_architecture.py

# Run linting
bin/linting.sh  # Linux/macOS
bin/linting.bat # Windows
```

### Project Structure

```
midi_drums/
├── __init__.py              # Main exports
├── core/
│   └── engine.py           # DrumGenerator - main engine
├── models/
│   ├── pattern.py          # Pattern, Beat, PatternBuilder
│   ├── song.py             # Song, Section, GenerationParameters
│   └── kit.py              # DrumKit configurations
├── plugins/
│   ├── base.py             # Plugin system foundation
│   └── genres/
│       └── metal.py        # Metal genre plugin
├── engines/
│   └── midi_engine.py      # MIDI file generation
└── api/
    ├── python_api.py       # High-level Python API
    └── cli.py              # Command-line interface
```

### Running Examples

```bash
# Test the system
python test_new_architecture.py

# Try the examples
python examples/basic_usage.py

# Compare with original implementation
python migrate_from_original.py
```

## 🎼 MIDI Output

The system generates professional MIDI files compatible with:

- **EZDrummer 3** (primary target)
- **Superior Drummer 3**
- **BFD3**
- **Any GM-compatible drum sampler**
- **DAWs** (Logic Pro, Pro Tools, Cubase, Reaper, etc.)

### MIDI Features

- ✅ Standard GM drum mapping
- ✅ Realistic velocity variations (60-127)
- ✅ Humanized timing (configurable)
- ✅ Ghost notes and accents
- ✅ Dynamic fills and variations
- ✅ Multi-bar pattern support

## 📊 Migration from Original

This system evolved from a simple single-file generator (`generate_metal_drum_track.py`) into a comprehensive platform:

### Before → After

| Original | New Architecture |
|----------|------------------|
| Single file | Modular plugin system |
| One metal style | 7+ metal styles, expandable |
| Fixed song structure | Configurable structures |
| Hardcoded patterns | Dynamic pattern generation |
| No API | Multiple interfaces |
| No variations | Humanization & variations |

The original script is preserved for compatibility, and `migrate_from_original.py` demonstrates equivalent functionality.

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### 🎵 Add New Genres
1. Create a new plugin in `midi_drums/plugins/genres/`
2. Implement the `GenrePlugin` interface
3. Add comprehensive patterns for different sections
4. Include characteristic fills and variations

### 🥁 Add Drummer Styles
1. Create a drummer plugin in `midi_drums/plugins/drummers/`
2. Implement the `DrummerPlugin` interface
3. Add signature playing techniques and fills
4. Make it compatible with multiple genres

### 🐛 Report Issues
- Found a bug? Open an issue on GitHub
- Include MIDI output samples if possible
- Provide steps to reproduce

### 💡 Suggest Features
- New musical genres or styles
- Advanced humanization techniques
- Integration with specific DAWs or samplers

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original Inspiration**: Single-file metal drum generator
- **MIDI Generation**: [midiutil](https://github.com/MarkCWirt/MIDIUtil) library
- **Target Platform**: [EZDrummer 3](https://www.toontrack.com/product/ezdrummer-3/) compatibility
- **Architecture**: Plugin-based design inspired by modern audio software

## 📈 Roadmap

### Phase 1: Core Expansion 🚧
- [ ] Rock genre plugin with 5+ styles
- [ ] Jazz genre plugin (swing, bebop, fusion)
- [ ] First drummer plugins (Bonham, Peart)

### Phase 2: Advanced Features 🔮
- [ ] Real-time audio synthesis
- [ ] AI-driven pattern variations
- [ ] Advanced humanization algorithms
- [ ] Groove template system

### Phase 3: Integration 🌐
- [ ] REST API for web services
- [ ] DAW integration (VST/AU plugins)
- [ ] Pattern marketplace
- [ ] Visual pattern editor

---

<div align="center">

**Made with ❤️ for drummers, producers, and music creators**

[⭐ Star this project](https://github.com/yourusername/midi-drums) • [🐛 Report Bug](https://github.com/yourusername/midi-drums/issues) • [💡 Request Feature](https://github.com/yourusername/midi-drums/issues)

</div>