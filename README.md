# 🥁 MIDI Drums Generator

<div align="center">

[![Tests](https://github.com/fsecada01/midi-drums/actions/workflows/tests.yml/badge.svg)](https://github.com/fsecada01/midi-drums/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.12%2B%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MIDI](https://img.shields.io/badge/Output-MIDI-purple.svg)](https://en.wikipedia.org/wiki/MIDI)
[![EZDrummer](https://img.shields.io/badge/Compatible-EZDrummer_3-orange.svg)](https://www.toontrack.com/product/ezdrummer-3/)
[![Code Reduction](https://img.shields.io/badge/Code_Reduction-62%25-brightgreen.svg)](claudedocs/REFACTORING_PROGRESS.md)
[![Tests](https://img.shields.io/badge/Tests-257%2B_passing-success.svg)](tests/)
[![Docs](https://img.shields.io/badge/Docs-GitHub_Pages-blueviolet.svg)](https://fsecada01.github.io/midi-drums/)

*A comprehensive, plugin-based MIDI drum track generation system*

[🚀 Quick Start](#-quick-start) • [📖 Docs](https://fsecada01.github.io/midi-drums/) • [🎵 Examples](#-examples) • [🔌 Plugins](#-plugin-system) • [🤝 Contributing](#-contributing)

</div>

---

## 🎯 Overview

MIDI Drums Generator is a powerful Python system that creates professional-quality drum tracks in MIDI format. Built with a modular, plugin-based architecture, it supports multiple musical genres, drummer styles, and song structures with realistic humanization and variations.

### ✨ Key Features

🎪 **Multi-Genre Support**
- **Metal**: Heavy, Death, Power, Progressive, Doom, Thrash, Breakdown
- **Rock**: Classic, Blues, Alternative, Progressive, Punk, Hard, Pop
- **Jazz**: Swing, Bebop, Fusion, Latin, Ballad, Hard Bop, Contemporary
- **Funk**: Classic, P-Funk, Shuffle, New Orleans, Fusion, Minimal, Heavy
- **Expandable**: Plugin architecture for Electronic and more

🥁 **Drummer Imitation**
- **7 Famous Drummers**: Bonham, Porcaro, Weckl, Chambers, Roeder, Dee, Hoglan
- Signature fills and playing techniques based on research
- Compatible across multiple genres with authentic styles

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
- Command-line interface (CLI tool installable with `uv tool install`)
- Direct module usage for custom applications
- Reaper DAW integration for professional workflows

🤖 **AI-Powered Generation** (NEW!)
- Natural language pattern generation with Pydantic AI
- Intelligent composition with Langchain agents
- Provider-agnostic backend (Anthropic, OpenAI, Groq, Cohere)
- Environment-driven configuration for production use

## ⚡ Code Quality & Architecture

The MIDI Drums Generator underwent comprehensive refactoring achieving **extraordinary code reduction** while maintaining 100% functional equivalence:

### Refactoring Achievements

| Achievement | Metric |
|-------------|--------|
| **Total Code Reduction** | 62% (2,898 lines eliminated) |
| **Genre Plugins** | 37% reduction (757 lines saved) |
| **Drummer Plugins** | 83% reduction (2,141 lines saved!) |
| **Test Coverage** | 39 comprehensive tests, 100% passing |
| **Type Safety** | Full type hints throughout |

### Modern Architecture

The refactored architecture uses three foundational systems:

**1. Configuration Constants** - Type-safe constants eliminating magic numbers
```python
from midi_drums.config import VELOCITY, TIMING, DEFAULTS
builder.kick(0.0, VELOCITY.KICK_MEDIUM)  # Self-documenting!
```

**2. Pattern Templates** - 8 reusable templates for declarative composition
```python
from midi_drums.patterns import TemplateComposer, DoubleBassPedal, BlastBeat
pattern = TemplateComposer("death_metal").add(DoubleBassPedal()).build()
```

**3. Drummer Modifications** - 12 composable modifications for authentic techniques
```python
from midi_drums.modifications import BehindBeatTiming, TripletVocabulary
pattern = behind_beat.apply(triplets.apply(pattern))
```

### Benefits

✅ **Zero Code Duplication** - Reusable templates and modifications
✅ **Professional Quality** - Full type hints, comprehensive testing
✅ **Maintainable** - Clear separation of concerns, easy to extend
✅ **Tested** - 100% functional equivalence validated
✅ **Documented** - See [REFACTORING_PROGRESS.md](claudedocs/REFACTORING_PROGRESS.md) for details

## 🚀 Quick Start

### Installation

**Option 1: Install as CLI tool (Recommended)**
```bash
# Clone the repository
git clone https://github.com/yourusername/midi-drums.git
cd midi-drums

# Install as a global CLI tool
uv tool install .

# Now use 'midi-drums' command anywhere
midi-drums --help
```

**Option 2: Development installation**
```bash
# Clone the repository
git clone https://github.com/yourusername/midi-drums.git
cd midi-drums

# Install with uv (recommended)
uv sync

# Or using pip
pip install -e "."
```

### Generate Your First Drum Track

```python
from midi_drums.api.python_api import DrumGeneratorAPI

# Initialize the generator
api = DrumGeneratorAPI()

# Create a death metal song
song = api.create_song("metal", "death", tempo=180)
api.save_as_midi(song, "death_metal_track.mid")

# Create a jazz swing pattern with Dave Weckl style
jazz_song = api.create_song("jazz", "swing", tempo=120, drummer="weckl")
api.save_as_midi(jazz_song, "jazz_swing_weckl.mid")

print("🎵 Generated: death_metal_track.mid & jazz_swing_weckl.mid")
```

### Command Line Usage

**If installed with `uv tool install`:**
```bash
# Generate songs across different genres
midi-drums generate --genre metal --style heavy --tempo 155 --output metal_song.mid
midi-drums generate --genre rock --style classic --tempo 140 --output rock_song.mid
midi-drums generate --genre jazz --style swing --tempo 120 --output jazz_song.mid
midi-drums generate --genre funk --style classic --tempo 110 --output funk_song.mid

# Generate patterns with drummer styles
midi-drums pattern --genre rock --section verse --drummer bonham --output bonham_verse.mid

# Reaper DAW integration
midi-drums reaper export --genre metal --style doom --tempo 120 --output doom.rpp --midi

# List available options
midi-drums list genres
midi-drums list drummers

# AI natural language generation (requires AI setup)
midi-drums prompt "funky groove with ghost notes"
midi-drums prompt "aggressive death metal breakdown" --tempo 180 -o breakdown.mid
midi-drums prompt "Testament-style death metal epic" --song --save-metadata --tempo 185
```

**Or use the module directly:**
```bash
python -m midi_drums.api.cli generate --genre metal --style heavy --output metal.mid
python -m midi_drums.api.cli reaper export --genre metal --style doom --output doom.rpp
```

## 🤖 AI-Powered Generation

Generate drum patterns from natural language using AI! The system supports multiple AI providers with environment-driven configuration.

### Setup

```bash
# Install AI dependencies
uv sync --group ai
# or: pip install -e ".[ai]"

# Configure your preferred AI provider
export AI_PROVIDER="anthropic"  # or openai, groq, cohere
export ANTHROPIC_API_KEY="your-api-key"
export AI_MODEL="claude-sonnet-4-20250514"  # optional, has smart defaults
```

### Natural Language Pattern Generation

```python
from midi_drums.ai import DrumGeneratorAI

# Initialize AI generator (uses environment variables)
ai = DrumGeneratorAI()

# Generate from natural language descriptions
pattern, response = await ai.generate_pattern_from_text(
    "aggressive metal breakdown with double bass and blast beats",
    section="breakdown",
    tempo=180,
    bars=4
)

# AI analyzes and infers characteristics
print(f"Genre: {response.characteristics.genre}")
print(f"Style: {response.characteristics.style}")
print(f"Intensity: {response.characteristics.intensity}")
print(f"Double bass: {response.characteristics.use_double_bass}")

# Export to MIDI
ai.export_pattern(pattern, "ai_breakdown.mid", tempo=180)
```

### Agent-Based Composition

```python
# Use Langchain agent for multi-step reasoning
result = ai.compose_with_agent(
    "Create a progressive metal song with verse and chorus patterns, "
    "then apply the Bonham drummer style to make it more dynamic"
)

print(result['output'])  # Agent's creative response
```

### CLI — `prompt` command

The `prompt` subcommand is the fastest way to get a MIDI file from plain English:

```bash
# Single pattern — analyses the text, picks genre/style, exports MIDI
midi-drums prompt "funky groove with ghost notes and syncopation"
midi-drums prompt "aggressive metal breakdown with double bass at 180 bpm" \
    --tempo 180 -o breakdown.mid

# Full multi-section song via AI agent
midi-drums prompt "Testament-inspired death metal — Hoglan blast beats, \
Lombardo breakdowns, extended solo arc" \
    --song --tempo 185

# Organised output: --save-metadata creates a directory with parts
midi-drums prompt "brutal death metal with progressive solo section" \
    --song --save-metadata --tempo 185 --output my_song.mid

# Produces:
# output/my_song/
#   my_song.mid          ← full assembled song
#   metadata.json        ← prompt, structure, agent composition notes
#   parts/
#     00_intro.mid       ← each section exported individually
#     01_verse.mid
#     02_chorus.mid
#     03_breakdown.mid
#     ...
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--song` | Compose a full multi-section song via AI agent (default: single pattern) |
| `--save-metadata` | Write `metadata.json` + per-section `parts/` into `output/<name>/` |
| `--output` / `-o` | MIDI filename (auto-named from prompt words if omitted) |
| `--tempo` | Tempo in BPM (default: 120) |
| `--drummer` | Apply a specific drummer style (bonham, hoglan, weckl, …) |
| `--rpp` | Also create a Reaper project with section markers |

### Multi-Provider Support

```python
from midi_drums.ai import AIBackendConfig, AIProvider

# Switch providers programmatically
openai_config = AIBackendConfig(
    provider=AIProvider.OPENAI,
    model="gpt-4o",
    api_key="sk-...",
    temperature=0.7
)

ai_openai = DrumGeneratorAI(backend_config=openai_config)

# Or use Groq for fast, cost-effective generation
groq_config = AIBackendConfig(
    provider=AIProvider.GROQ,
    model="llama-3.3-70b-versatile",
    api_key="gsk-..."
)

ai_groq = DrumGeneratorAI(backend_config=groq_config)
```

### Supported AI Providers

| Provider | Models | Best For |
|----------|--------|----------|
| **Anthropic** | Claude Sonnet 4 | High-quality, nuanced generation |
| **OpenAI** | GPT-4o, GPT-4 Turbo | Versatile, well-tested |
| **Groq** | Llama 3.3 70B | Fast inference, cost-effective |
| **Cohere** | Command R+ | Enterprise use cases |

**Environment Variables:**
- `AI_PROVIDER` - Provider selection (default: anthropic)
- `AI_MODEL` - Model identifier (provider-specific defaults)
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `COHERE_API_KEY`
- `AI_TEMPERATURE` - Generation temperature (0.0-2.0, default: 0.7)
- `AI_MAX_TOKENS` - Maximum output tokens (default: 4096)

See [claudedocs/AI_BACKEND_MIGRATION.md](claudedocs/AI_BACKEND_MIGRATION.md) for complete documentation.

## 🎛️ Reaper DAW Integration

Export drum tracks directly to Reaper projects with automatic section markers!

### Python API

```python
from midi_drums.api.python_api import DrumGeneratorAPI
from midi_drums.exporters import ReaperExporter

# Generate drums
api = DrumGeneratorAPI()
song = api.create_song("metal", "doom", tempo=120)

# Export to Reaper with markers
exporter = ReaperExporter()
exporter.export_with_markers(
    song=song,
    output_rpp="doom_metal.rpp",
    marker_color="#FF5733"
)

# Also export MIDI separately
exporter.export_with_midi(
    song=song,
    output_rpp="doom_metal.rpp",
    output_midi="doom_metal.mid"
)
```

### CLI Usage

```bash
# Generate drums and create Reaper project with markers
midi-drums reaper export \
    --genre metal \
    --style doom \
    --tempo 120 \
    --output doom_metal.rpp \
    --midi

# With all options
midi-drums reaper export \
    --genre metal \
    --style death \
    --tempo 180 \
    --output death.rpp \
    --midi death_drums.mid \
    --complexity 0.8 \
    --humanization 0.4 \
    --drummer hoglan \
    --marker-color "#FF0000" \
    --template my_template.rpp

# Add markers from existing metadata (recommended)
midi-drums reaper add-markers \
    --metadata output/my_song/metadata.json \
    --output project.rpp

# Auto-detect metadata from MIDI directory
midi-drums reaper add-markers \
    --song output/my_song/complete.mid \
    --output project.rpp \
    --marker-color "#00FF00"

# Manual structure specification
midi-drums reaper add-markers \
    --structure "intro:4,verse:8,chorus:8,outro:4" \
    --tempo 120 \
    --output project.rpp
```

### Features

- ✅ **Automatic section markers** - Intro, verse, chorus, bridge, etc.
- ✅ **Time-accurate positioning** - Markers at exact bar positions
- ✅ **Metadata-based workflow** - Use existing metadata.json files or auto-detect
- ✅ **Template support** - Use existing Reaper projects as base
- ✅ **Custom marker colors** - Hex color codes supported
- ✅ **Immutable operations** - Original files never modified
- ✅ **MIDI export** - Optionally export MIDI alongside Reaper project
- ✅ **Flexible workflows** - Metadata file, auto-detection, or manual specification

See [docs/REAPER_INTEGRATION.md](docs/REAPER_INTEGRATION.md) for complete documentation.

### ReaScript Lua Integration (`create_song_sections.lua`)

The script `C:/REAPER/Scripts/create_song_sections.lua` provides a three-mode
bi-directional bridge between REAPER and the midi_drums Python module.

#### Quick Setup

1. Open the script in a text editor and set `PYTHON_EXE` to your virtualenv:
   ```lua
   local PYTHON_EXE = "C:/dev/python/projects/midi_drums/.venv/Scripts/pythonw.exe"
   ```
2. Add it as a REAPER action: **Actions → Load ReaScript** → select the file.
3. Bind it to a key shortcut for quick access.
4. Run **`midi_drums_help.lua`** from the same directory at any time for in-REAPER usage instructions.

#### Three Modes

| Mode | When to use | Wait time |
|------|-------------|-----------|
| **REAPER** (default, YES) | You define the structure in the script | ~1–2 s |
| **Python sidecar** (NO → YES) | Python already generated MIDI + sidecar | instant |
| **AI agent** (NO → NO) | Natural language description drives everything | ~20–45 s |

#### REAPER Mode Workflow

```
Run script → choose YES → regions created → prompted to generate MIDI?
  → YES → genre/style/mapping dialog → template engine generates drums.mid
        → drums.mid auto-imported on a new track
  → NO  → midi_drums_sections.json written (load manually in Python later)
```

```python
# Load the REAPER-written sidecar in Python:
song = api.create_song_from_sections_json(
    r"C:/path/to/project/midi_drums_sections.json",
    genre="metal", style="doom"
)
api.save_as_midi(song, "drums.mid")
```

#### Python Sidecar Mode Workflow

```python
# 1. Generate in Python first, write sidecar alongside MIDI:
api = DrumGeneratorAPI()
song = api.create_song("metal", "doom", tempo=70)
api.save_as_midi_with_sidecar(song, "drums.mid")
# → writes drums.mid  +  midi_drums_sections.json

# 2. Run script in REAPER (choose NO → YES) — regions created automatically.
```

#### AI Agent Mode Workflow

```
Run script → choose NO → NO
  → Enter description: "heavy doom riff, slow and crushing"
  → Enter tempo (or blank to let AI decide)
  → Confirm (~20-45s wait)
  → AI agent composes song → drums.mid + sidecar written
  → Project tempo synced to AI-chosen BPM
  → Regions created from AI structure
  → drums.mid auto-imported
```

Requires AI setup:
```bash
uv sync --group ai
# Add to C:/dev/python/projects/midi_drums/.env:
# ANTHROPIC_API_KEY=sk-ant-...   (or OPENAI_API_KEY / GROQ_API_KEY)
```

#### New Python API Methods

```python
from midi_drums.api.python_api import DrumGeneratorAPI

api = DrumGeneratorAPI()

# Write a sidecar from any Song object
api.export_sections_json(song, "midi_drums_sections.json")

# Read a REAPER-written sidecar and generate matching MIDI
song = api.create_song_from_sections_json(
    "midi_drums_sections.json", genre="metal", style="doom"
)

# Save MIDI + sidecar in one call (Python-drives workflow)
sidecar_path = api.save_as_midi_with_sidecar(song, "drums.mid")
```

#### New CLI Flags

```bash
# generate: use sidecar for section structure (REAPER-driven workflow)
midi-drums generate --genre metal --style doom \
    --sidecar midi_drums_sections.json \
    --output drums.mid

# prompt: write sidecar after AI generation (AI-driven workflow)
midi-drums prompt "heavy doom metal, slow and crushing" \
    --song --write-sidecar midi_drums_sections.json \
    --output drums.mid
```

#### Sidecar JSON Format

```json
{
  "source": "reaper",
  "tempo": 70,
  "time_signature": [4, 4],
  "sections": [
    {"name": "Intro",  "bars": 8},
    {"name": "Verse",  "bars": 16},
    {"name": "Chorus", "bars": 16},
    {"name": "Bridge", "bars": 8},
    {"name": "Outro",  "bars": 4}
  ]
}
```

`"source"` is either `"reaper"` (written by Lua) or `"python"` (written by `export_sections_json`).

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

#### 🎸 Rock Genre
- **Classic**: 70s classic rock (Led Zeppelin, Deep Purple)
- **Blues**: Blues rock with shuffles and triplets
- **Alternative**: 90s alternative rock syncopation
- **Progressive**: Complex progressive rock patterns
- **Punk**: Fast, aggressive punk rock
- **Hard**: Hard rock with heavy emphasis
- **Pop**: Pop rock with clean patterns

#### 🎷 Jazz Genre
- **Swing**: Traditional swing with ride patterns
- **Bebop**: Fast, complex bebop rhythms
- **Fusion**: Jazz fusion with electric energy
- **Latin**: Latin jazz with clave patterns
- **Ballad**: Soft, brushed ballad patterns
- **Hard Bop**: Aggressive hard bop rhythms
- **Contemporary**: Modern contemporary jazz

#### 🕺 Funk Genre
- **Classic**: James Brown "the one" emphasis
- **P-Funk**: Parliament-Funkadelic grooves
- **Shuffle**: Bernard Purdie shuffle patterns
- **New Orleans**: Second line funk patterns
- **Fusion**: Jazz-funk fusion styles
- **Minimal**: Stripped-down pocket grooves
- **Heavy**: Heavy funk with rock influence

#### 🥁 Available Drummers
- **John Bonham**: Triplet vocabulary, behind-the-beat timing
- **Jeff Porcaro**: Half-time shuffle, studio precision
- **Dave Weckl**: Linear playing, fusion mastery
- **Dennis Chambers**: Funk mastery, incredible chops
- **Jason Roeder**: Atmospheric sludge, minimal creativity
- **Mikkey Dee**: Speed/precision, versatile power
- **Gene Hoglan**: Mechanical precision, blast beats

#### 🔮 Future Expansions
- **Electronic**: House, Techno, Drum'n'Bass, Dubstep
- **World**: Latin, Reggae, Afrobeat
- **More Drummers**: Neil Peart, Buddy Rich, Stewart Copeland

## 🎵 Examples

### Python API Examples

```python
from midi_drums.api.python_api import DrumGeneratorAPI

api = DrumGeneratorAPI()

# Multi-genre songs with custom parameters
metal_song = api.create_song("metal", "progressive", tempo=140, complexity=0.9)
rock_song = api.create_song("rock", "classic", tempo=130, drummer="bonham")
jazz_song = api.create_song("jazz", "swing", tempo=120, drummer="weckl")
funk_song = api.create_song("funk", "classic", tempo=110, drummer="chambers")

# Batch generation across genres
specs = [
    {'genre': 'metal', 'style': 'death', 'tempo': 180},
    {'genre': 'rock', 'style': 'blues', 'tempo': 95, 'drummer': 'porcaro'},
    {'genre': 'jazz', 'style': 'fusion', 'tempo': 135, 'drummer': 'weckl'},
    {'genre': 'funk', 'style': 'pfunk', 'tempo': 105, 'drummer': 'chambers'}
]
files = api.batch_generate(specs, "output/")

# Individual patterns with drummer styles
verse = api.generate_pattern("rock", "verse", "classic")
bonham_verse = api.apply_drummer_style(verse, "bonham")
jazz_swing = api.generate_pattern("jazz", "verse", "swing")
funk_breakdown = api.generate_pattern("funk", "breakdown", "heavy")
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

**Using `midi-drums` command (after `uv tool install`):**

```bash
# Generate songs across all genres
midi-drums generate --genre metal --style death --tempo 180 --complexity 0.8 --output death.mid
midi-drums generate --genre rock --style classic --tempo 140 --drummer bonham --output rock_bonham.mid
midi-drums generate --genre jazz --style swing --tempo 120 --drummer weckl --output jazz_weckl.mid
midi-drums generate --genre funk --style classic --tempo 110 --drummer chambers --output funk_chambers.mid

# Generate patterns with drummer styles
midi-drums pattern --genre rock --section verse --style blues --drummer porcaro --output porcaro_verse.mid
midi-drums pattern --genre jazz --section bridge --style fusion --drummer weckl --output weckl_bridge.mid

# Reaper integration
midi-drums reaper export --genre metal --style doom --tempo 120 --output doom.rpp --midi
midi-drums reaper export --genre jazz --style swing --tempo 110 --output jazz.rpp --template my_template.rpp

# System information
midi-drums info
midi-drums list genres
midi-drums list styles --genre jazz
midi-drums list drummers
```

**Or use module directly:**
```bash
python -m midi_drums.api.cli generate --genre metal --style death --output death.mid
python -m midi_drums.api.cli reaper export --genre metal --output metal.rpp
```

## 🔌 Plugin System

The plugin architecture makes it easy to extend the system with new genres and drummer styles. The refactored architecture provides reusable templates and modifications for rapid development.

### Creating a Genre Plugin (Refactored Approach)

**Modern approach** using pattern templates for declarative composition:

```python
from midi_drums.plugins.base import GenrePlugin
from midi_drums.patterns import TemplateComposer, BasicGroove, DoubleBassPedal
from midi_drums.config import VELOCITY, TIMING

class MetalGenrePluginRefactored(GenrePlugin):
    @property
    def genre_name(self) -> str:
        return "metal"

    @property
    def supported_styles(self) -> List[str]:
        return ["heavy", "death", "power", "progressive", "thrash", "doom"]

    def generate_pattern(self, section: str, parameters: GenerationParameters) -> Pattern:
        if parameters.style == "death":
            # Declarative composition - just 5 lines!
            return (
                TemplateComposer(f"death_metal_{section}")
                .add(DoubleBassPedal(pattern="continuous", speed=16))
                .add(BlastBeat(style="traditional", intensity=0.9))
                .build(bars=2, complexity=parameters.complexity)
            )
        # ... other styles using templates
```

**Traditional approach** still available for custom patterns:

```python
from midi_drums.plugins.base import GenrePlugin
from midi_drums.models.pattern import PatternBuilder

class RockGenrePlugin(GenrePlugin):
    def generate_pattern(self, section: str, parameters: GenerationParameters) -> Pattern:
        builder = PatternBuilder(f"rock_{parameters.style}_{section}")

        if parameters.style == "classic":
            builder.kick(0.0, 105).kick(2.0, 105)
            builder.snare(1.0, 110).snare(3.0, 110)
            for i in range(8):
                builder.hihat(i * 0.5, 80)

        return builder.build()
```

### Creating a Drummer Plugin (Refactored Approach)

**Modern approach** using composable modifications (reduced from ~380 to ~66 lines!):

```python
from midi_drums.plugins.base import DrummerPlugin
from midi_drums.modifications import BehindBeatTiming, TripletVocabulary, HeavyAccents

class BonhamPluginRefactored(DrummerPlugin):
    def __init__(self):
        self.behind_beat = BehindBeatTiming(max_delay_ms=25.0)
        self.triplets = TripletVocabulary(triplet_probability=0.4)
        self.accents = HeavyAccents(accent_boost=15)

    @property
    def drummer_name(self) -> str:
        return "bonham"

    def apply_style(self, pattern: Pattern) -> Pattern:
        # Composable modifications - authentic Bonham techniques!
        styled_pattern = pattern.copy()
        styled_pattern = self.behind_beat.apply(styled_pattern, intensity=0.7)
        styled_pattern = self.triplets.apply(styled_pattern, intensity=0.8)
        styled_pattern = self.accents.apply(styled_pattern, intensity=0.9)
        return styled_pattern
```

**Available Modifications**: BehindBeatTiming, TripletVocabulary, GhostNoteLayer, LinearCoordination, HeavyAccents, ShuffleFeelApplication, FastChopsTriplets, PocketStretching, MinimalCreativity, SpeedPrecision, TwistedAccents, MechanicalPrecision

**Available Templates**: BasicGroove, DoubleBassPedal, BlastBeat, JazzRidePattern, FunkGhostNotes, CrashAccents, TomFill, TemplateComposer

## 📚 Documentation

Full documentation is available on **[GitHub Pages](https://fsecada01.github.io/midi-drums/)**:

| Page | Description |
|------|-------------|
| **[Home](https://fsecada01.github.io/midi-drums/)** | Overview, features, quick examples |
| **[Quickstart](https://fsecada01.github.io/midi-drums/quickstart.html)** | Installation, first track, AI setup |
| **[Recipes](https://fsecada01.github.io/midi-drums/recipes.html)** | Death metal, modern jazz, progressive rock examples |
| **[Reaper Tutorial](https://fsecada01.github.io/midi-drums/reaper.html)** | DAW integration walkthrough |
| **[API Reference](https://fsecada01.github.io/midi-drums/midi_drums/)** | Auto-generated module documentation |

Build docs locally:
```bash
just docs        # Build to docs/site/
just docs-serve  # Live reload at localhost:8080
```

## 🛠️ Development

### Setup Development Environment

```bash
# Install all dependencies including dev tools
uv sync --all-groups

# Or install specific groups
uv sync                  # Core only
uv sync --group dev      # + dev tools (pytest, ruff, black)
uv sync --group ai       # + AI providers (langchain, anthropic, etc.)

# Run linting
just lint    # ruff + black + isort
just format  # auto-format code
just check   # format + lint + tests
```

### Continuous Integration

The project uses **GitHub Actions** for automated testing:

- ✅ Automated linting (ruff, black, isort)
- ✅ Multi-version testing (Python 3.12, 3.13)
- ✅ Coverage reporting
- ✅ 257+ tests passing across all Python versions

See [docs/CI_CD.md](docs/CI_CD.md) for CI/CD documentation.

### Testing

The project uses **pytest** with comprehensive test coverage:

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests (no API key needed)
pytest -m integration   # Integration tests
pytest -m ai           # AI tests (requires API key)

# Run tests in parallel
pytest -n auto

# Run with coverage
pytest --cov=midi_drums --cov-report=html

# Skip AI tests if no API key
pytest -m "not requires_api"
```

**Test Organization:**
- `tests/unit/` - Unit tests for individual components (8 files)
- `tests/integration/` - End-to-end integration tests (6 files)
- `tests/ai/` - AI-powered generation tests (4 files)
- `tests/conftest.py` - Shared fixtures and configuration

**Test Markers:**
- `@pytest.mark.unit` - Fast unit tests, no external dependencies
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.ai` - AI functionality tests
- `@pytest.mark.requires_api` - Tests requiring API keys (auto-skipped if unavailable)
- `@pytest.mark.slow` - Long-running tests

```python
# Example test run output
============================= test session starts =============================
8 passed in 10.69s ==============================
✅ Backend abstraction tests
✅ Configuration validation
✅ Environment variable loading
✅ Provider fallback handling
```

### Project Structure

```
midi_drums/
├── __init__.py              # Main exports
├── config/
│   └── constants.py        # VELOCITY, TIMING, DEFAULTS constants
├── patterns/
│   └── templates.py        # 8 reusable pattern templates
├── modifications/
│   └── drummer_mods.py     # 12 composable drummer modifications
├── core/
│   └── engine.py           # DrumGenerator - main composition engine
├── models/
│   ├── pattern.py          # Pattern, Beat, PatternBuilder
│   ├── song.py             # Song, Section, GenerationParameters
│   └── kit.py              # DrumKit configurations (EZDrummer3, Metal, Jazz)
├── plugins/
│   ├── base.py             # Plugin system foundation
│   ├── genres/
│   │   ├── metal.py        # MetalGenrePlugin - 7 styles
│   │   ├── rock.py         # RockGenrePlugin - 7 styles
│   │   ├── jazz.py         # JazzGenrePlugin - 7 styles
│   │   └── funk.py         # FunkGenrePlugin - 7 styles
│   └── drummers/
│       ├── bonham.py       # John Bonham style
│       ├── porcaro.py      # Jeff Porcaro style
│       ├── weckl.py        # Dave Weckl style
│       ├── chambers.py     # Dennis Chambers style
│       ├── roeder.py       # Jason Roeder style
│       ├── dee.py          # Mikkey Dee style
│       └── hoglan.py       # Gene Hoglan style
├── engines/
│   └── midi_engine.py      # MIDI file generation
├── exporters/
│   └── reaper.py           # Reaper .rpp project exporter
├── api/
│   ├── python_api.py       # High-level Python API
│   └── cli.py              # Command-line interface
├── ai/                     # AI-powered generation (optional)
│   ├── agent.py            # Langchain agent orchestration
│   └── prompts/            # Prompt templates for AI generation
└── utils/
    └── pattern_fixer.py    # Physical feasibility validation
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
3. Add comprehensive patterns for different sections and styles
4. Include characteristic fills and variations
5. Examples: Rock, Jazz, and Funk genres with 7 styles each

### 🥁 Add Drummer Styles
1. Create a drummer plugin in `midi_drums/plugins/drummers/`
2. Implement the `DrummerPlugin` interface
3. Add signature playing techniques and fills based on research
4. Make it compatible with multiple genres
5. Examples: 7 drummers already implemented with authentic styles

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

### Phase 1: Core Expansion ✅
- [x] Rock genre plugin with 7 styles
- [x] Jazz genre plugin with 7 styles (swing, bebop, fusion, latin, etc.)
- [x] Funk genre plugin with 7 styles
- [x] 7 drummer plugins (Bonham, Porcaro, Weckl, Chambers, Roeder, Dee, Hoglan)
- [x] Comprehensive testing and validation system
- [x] Reaper DAW integration with automatic markers
- [x] CLI tool installation (`uv tool install`)
- [x] GitHub Actions CI/CD pipeline

### Phase 2: Advanced Features 🚧
- [ ] Electronic genre plugin (House, Techno, Drum'n'Bass)
- [ ] More drummer plugins (Neil Peart, Buddy Rich, Stewart Copeland)
- [ ] Reaper marker import (generate drums from existing markers)
- [ ] Real-time audio synthesis
- [ ] AI-driven pattern variations
- [ ] Advanced humanization algorithms
- [ ] Groove template system

### Phase 3: Integration 🔮
- [ ] REST API for web services
- [ ] DAW integration (VST/AU plugins)
- [ ] Pattern marketplace
- [ ] Visual pattern editor
- [ ] World music genres (Latin, Reggae, Afrobeat)

---

<div align="center">

**Made with ❤️ for drummers, producers, and music creators**

[⭐ Star this project](https://github.com/yourusername/midi-drums) • [🐛 Report Bug](https://github.com/yourusername/midi-drums/issues) • [💡 Request Feature](https://github.com/yourusername/midi-drums/issues)

</div>