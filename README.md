# 🥁 MIDI Drums Generator

<div align="center">

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/fsecada01/midi-drums/releases)
[![Tests](https://github.com/fsecada01/midi-drums/actions/workflows/tests.yml/badge.svg)](https://github.com/fsecada01/midi-drums/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.12%2B%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MIDI](https://img.shields.io/badge/Output-MIDI-purple.svg)](https://en.wikipedia.org/wiki/MIDI)
[![EZDrummer](https://img.shields.io/badge/Compatible-EZDrummer_3-orange.svg)](https://www.toontrack.com/product/ezdrummer-3/)
[![Tests](https://img.shields.io/badge/Tests-500%2B_passing-success.svg)](tests/)
[![Docs](https://img.shields.io/badge/Docs-GitHub_Pages-blueviolet.svg)](https://fsecada01.github.io/midi-drums/)

*A comprehensive, plugin-based MIDI drum track generation system*

[🚀 Quick Start](#-quick-start) • [📖 Full Docs](https://fsecada01.github.io/midi-drums/) • [🎵 Examples](#-examples) • [🔌 Plugins](#-plugin-system) • [🤝 Contributing](#-contributing)

</div>

---

## 🎯 Overview

MIDI Drums Generator is a Python system that creates professional-quality drum tracks in MIDI format. Built on a modular, plugin-based architecture, it supports 5 musical genres, 10 drummer imitations, and configurable song structures — with realistic humanization, pattern variations, natural-language AI generation, and direct Reaper DAW integration.

### ✨ Key Features

- 🎪 **Multi-Genre Support** — 32 styles across 5 genres
  - **Metal**: Heavy, Death, Power, Progressive, Doom, Thrash, Breakdown
  - **Rock**: Classic, Blues, Alternative, Progressive, Punk, Hard, Pop
  - **Jazz**: Swing, Bebop, Fusion, Latin, Ballad, Hard Bop, Contemporary
  - **Funk**: Classic, P-Funk, Shuffle, New Orleans, Fusion, Minimal, Heavy
  - **Electronic**: House, Techno, Drum & Bass, Dubstep
  - **Expandable**: Plugin architecture for more genres
- 🥁 **Drummer Imitation** — 10 legendary styles
  - Bonham, Porcaro, Weckl, Chambers, Roeder, Dee, Hoglan, Peart, Rich, Copeland
  - Signature fills and playing techniques based on research
  - Compatible across multiple genres with authentic styles
- 🏗️ **Flexible Song Structure**
  - Configurable sections (verse, chorus, bridge, breakdown)
  - Pattern variations and dynamic fills
  - Custom song arrangements
- 🎛️ **Professional Features**
  - Realistic velocity variations and humanization
  - EZDrummer 3 compatible MIDI mapping
  - Multiple complexity and dynamics levels
- 🔧 **Multiple Interfaces**
  - Python API for integration
  - Command-line interface (CLI tool installable with `uv tool install`)
  - Direct module usage for custom applications
  - Reaper DAW integration for professional workflows
- 🤖 **AI-Powered Generation**
  - Natural language pattern generation with Pydantic AI
  - Intelligent multi-section composition with Langchain agents
  - Provider-agnostic backend (Anthropic, OpenAI, Groq, Cohere)
  - Environment-driven configuration for production use

## 🚀 Quick Start

### Installation

**Option 1: Install as CLI tool (Recommended)**
```bash
git clone https://github.com/fsecada01/midi-drums.git
cd midi-drums

uv tool install .

# Now use 'midi-drums' command anywhere
midi-drums --help
```

**Option 2: Development installation**
```bash
git clone https://github.com/fsecada01/midi-drums.git
cd midi-drums

uv sync                  # recommended
# or: pip install -e "."
```

### Generate Your First Drum Track

```python
from midi_drums.api.python_api import DrumGeneratorAPI

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
midi-drums generate --genre electronic --style techno --tempo 128 --output techno_song.mid

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
uv sync --group ai
# or: pip install -e ".[ai]"

export AI_PROVIDER="anthropic"  # or openai, groq, cohere
export ANTHROPIC_API_KEY="your-api-key"
export AI_MODEL="claude-sonnet-5"  # optional, has smart defaults
```

### Natural Language Pattern Generation

```python
from midi_drums.ai import DrumGeneratorAI

ai = DrumGeneratorAI()

pattern, response = await ai.generate_pattern_from_text(
    "aggressive metal breakdown with double bass and blast beats",
    section="breakdown",
    tempo=180,
    bars=4
)

print(f"Genre: {response.characteristics.genre}")
print(f"Style: {response.characteristics.style}")
print(f"Intensity: {response.characteristics.intensity}")
print(f"Double bass: {response.characteristics.use_double_bass}")

ai.export_pattern(pattern, "ai_breakdown.mid", tempo=180)
```

### Agent-Based Composition

```python
result = ai.compose_with_agent(
    "Create a progressive metal song with verse and chorus patterns, "
    "then apply the Bonham drummer style to make it more dynamic"
)

print(result['output'])  # Agent's creative response
```

### CLI — `prompt` command

The fastest way to get a MIDI file from plain English:

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
#     ...
```

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

openai_config = AIBackendConfig(
    provider=AIProvider.OPENAI, model="gpt-4o", api_key="sk-...", temperature=0.7
)
ai_openai = DrumGeneratorAI(backend_config=openai_config)

groq_config = AIBackendConfig(
    provider=AIProvider.GROQ, model="llama-3.3-70b-versatile", api_key="gsk-..."
)
ai_groq = DrumGeneratorAI(backend_config=groq_config)
```

| Provider | Models | Best For |
|----------|--------|----------|
| **Anthropic** | Claude Sonnet 5 | High-quality, nuanced generation |
| **OpenAI** | GPT-4o, GPT-4 Turbo | Versatile, well-tested |
| **Groq** | Llama 3.3 70B | Fast inference, cost-effective |

> Cohere is defined in the provider config (`AIProvider.COHERE`) but not yet wired into the Pydantic AI / Langchain backends — `AIBackendFactory` raises for it today. Support is tracked as a future item.

**Environment Variables:** `AI_PROVIDER`, `AI_MODEL`, `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GROQ_API_KEY`, `AI_TEMPERATURE` (0.0-2.0, default 0.7), `AI_MAX_TOKENS` (default 4096)

See [claudedocs/AI_BACKEND_MIGRATION.md](claudedocs/AI_BACKEND_MIGRATION.md) for complete documentation.

## 🎛️ Reaper DAW Integration

Export drum tracks directly to Reaper projects with automatic section markers.

### Python API

```python
from midi_drums.api.python_api import DrumGeneratorAPI
from midi_drums.exporters import ReaperExporter

api = DrumGeneratorAPI()
song = api.create_song("metal", "doom", tempo=120)

exporter = ReaperExporter()
exporter.export_with_markers(song=song, output_rpp="doom_metal.rpp", marker_color="#FF5733")
exporter.export_with_midi(song=song, output_rpp="doom_metal.rpp", output_midi="doom_metal.mid")
```

### CLI Usage

```bash
midi-drums reaper export --genre metal --style doom --tempo 120 --output doom_metal.rpp --midi

midi-drums reaper export \
    --genre metal --style death --tempo 180 \
    --output death.rpp --midi death_drums.mid \
    --complexity 0.8 --humanization 0.4 --drummer hoglan \
    --marker-color "#FF0000" --template my_template.rpp

# Add markers from existing metadata (recommended)
midi-drums reaper add-markers --metadata output/my_song/metadata.json --output project.rpp

# Auto-detect metadata from MIDI directory
midi-drums reaper add-markers --song output/my_song/complete.mid --output project.rpp --marker-color "#00FF00"

# Manual structure specification
midi-drums reaper add-markers --structure "intro:4,verse:8,chorus:8,outro:4" --tempo 120 --output project.rpp
```

**Features:** automatic section markers, time-accurate positioning, metadata-based or auto-detected workflow, template support, custom marker colors, immutable operations (originals never modified), optional MIDI export alongside the Reaper project.

See [docs/REAPER_INTEGRATION.md](docs/REAPER_INTEGRATION.md) for complete documentation.

### ReaScript Lua Integration (`create_song_sections.lua`)

The script [`reaper/create_song_sections.lua`](reaper/create_song_sections.lua)
(vendored in this repo) provides a four-mode bi-directional bridge between
REAPER and the midi_drums Python module. See
[`reaper/README.md`](reaper/README.md) for the install step (symlink or copy
into REAPER's `Scripts/` directory).

#### Quick Setup

1. Symlink or copy `reaper/create_song_sections.lua` and
   `reaper/midi_drums_help.lua` into REAPER's `Scripts/` directory (see
   [`reaper/README.md`](reaper/README.md)).
2. Open the script in a text editor and set `PYTHON_EXE` to your virtualenv:
   ```lua
   local PYTHON_EXE = "C:/path/to/midi_drums/.venv/Scripts/pythonw.exe"
   ```
3. Add it as a REAPER action: **Actions → Load ReaScript** → select the file.
4. Bind it to a key shortcut for quick access.
5. Run **`midi_drums_help.lua`** from the same directory at any time for in-REAPER usage instructions.

#### Four Modes

| Mode | When to use | Wait time |
|------|-------------|-----------|
| **REAPER** (default, YES) | You define the structure in the script | ~1–2 s |
| **Python sidecar** (NO → "sidecar") | Python already generated MIDI + sidecar | instant |
| **AI agent** (NO → "ai") | Natural language description drives everything | ~20–45 s |
| **Song map** (NO → "songmap") | A song_creator-shaped JSON drives per-section tempo/meter | ~1–2 s |

The follow-up prompt after choosing "External" is a text field, not another
Yes/No dialog — type `sidecar`, `ai`, or `songmap`.

```python
# Python-drives workflow: generate + write sidecar in one call
api = DrumGeneratorAPI()
song = api.create_song("metal", "doom", tempo=70)
api.save_as_midi_with_sidecar(song, "drums.mid")
# → writes drums.mid + midi_drums_sections.json; run the script in REAPER (NO → YES)

# REAPER-drives workflow: load a REAPER-written sidecar
song = api.create_song_from_sections_json(
    "midi_drums_sections.json", genre="metal", style="doom"
)
api.save_as_midi(song, "drums.mid")
```

AI agent mode requires `uv sync --group ai` and an API key in `.env`.

**Sidecar JSON format** (`midi_drums_sections.json`), written by Lua (`"source": "reaper"`) or by `export_sections_json` (`"source": "python"`):
```json
{
  "source": "reaper",
  "tempo": 70,
  "time_signature": [4, 4],
  "sections": [
    {"name": "Intro", "bars": 8},
    {"name": "Verse", "bars": 16}
  ]
}
```

**CLI flags:**
```bash
# generate: use sidecar for section structure (REAPER-driven workflow)
midi-drums generate --genre metal --style doom --sidecar midi_drums_sections.json --output drums.mid

# prompt: write sidecar after AI generation (AI-driven workflow)
midi-drums prompt "heavy doom metal, slow and crushing" --song --write-sidecar midi_drums_sections.json
```

**API reference:** `DrumGeneratorAPI.export_sections_json(song, path)`, `.create_song_from_sections_json(path, genre, style, **kw)`, `.save_as_midi_with_sidecar(song, filename)`.

**Song map mode** drives section structure *and* per-segment tempo/meter
overrides from a song_creator-shaped JSON file (regions containing segments,
each with its own `bars`/`bpm`/`num`/`denom`):
```bash
midi-drums generate --genre metal --style doom \
  --song-map song_map.json --write-timeline timeline.json --output drums.mid
```
The Lua script reads back `timeline.json` (a flat, resolved tempo/region
timeline) and places one `SetTempoTimeSigMarker` per tempo/meter change plus
one colored region per song-map region.

**API reference:** `DrumGeneratorAPI.create_song_from_song_map(song_map, genre, style, **kw)`, `.export_song_map_json(song, path)`, `.export_song_timeline_json(song, path)`.

## 📖 Documentation

Full documentation — quickstart, genre/drummer recipes, Reaper walkthrough, auto-generated API reference — lives on **[GitHub Pages](https://fsecada01.github.io/midi-drums/)**, built with `pdoc` and deployed automatically on every push to `main`:

| Page | Description |
|------|-------------|
| **[Home](https://fsecada01.github.io/midi-drums/)** | Overview, features, quick examples |
| **[Quickstart](https://fsecada01.github.io/midi-drums/quickstart.html)** | Installation, first track, AI setup |
| **[Recipes](https://fsecada01.github.io/midi-drums/recipes.html)** | Death metal, modern jazz, progressive rock examples |
| **[Use Cases](https://fsecada01.github.io/midi-drums/use-cases.html)** | End-to-end scenarios: batch export, Reaper sidecar round-trip, AI prompt to drummer lock-in |
| **[Reaper Tutorial](https://fsecada01.github.io/midi-drums/reaper.html)** | DAW integration walkthrough |
| **[API Reference](https://fsecada01.github.io/midi-drums/midi_drums/)** | Auto-generated module documentation |

Build docs locally:
```bash
just docs        # Build to docs/site/
just docs-serve  # Live reload at localhost:8080
```

### Architecture

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

The layered, plugin-based architecture uses three reusable infrastructure systems:

**Configuration Constants** — type-safe constants, no magic numbers:
```python
from midi_drums.config import VELOCITY, TIMING, DEFAULTS
builder.kick(0.0, VELOCITY.KICK_MEDIUM)  # Self-documenting!
```

**Pattern Templates** — 8 reusable templates for declarative composition:
```python
from midi_drums.patterns import TemplateComposer, DoubleBassPedal, BlastBeat
pattern = TemplateComposer("death_metal").add(DoubleBassPedal()).build()
```

**Drummer Modifications** — 12 composable modifications for authentic playing techniques:
```python
from midi_drums.modifications import BehindBeatTiming, TripletVocabulary
pattern = behind_beat.apply(triplets.apply(pattern))
```

See [`docs/DDD_ARCHITECTURE.md`](docs/DDD_ARCHITECTURE.md) for the domain-boundary rules behind this layout, [`docs/MIGRATION_GUIDE.md`](docs/MIGRATION_GUIDE.md) for pre-DDD-migration import paths, and [claudedocs/REFACTORING_PROGRESS.md](claudedocs/REFACTORING_PROGRESS.md) for the history behind this design (a 62% code-reduction refactor from the original per-plugin implementations).

### Available Genres & Styles

#### 🤘 Metal — Heavy, Death, Power, Progressive, Thrash, Doom, Breakdown
#### 🎸 Rock — Classic, Blues, Alternative, Progressive, Punk, Hard, Pop
#### 🎷 Jazz — Swing, Bebop, Fusion, Latin, Ballad, Hard Bop, Contemporary
#### 🕺 Funk — Classic, P-Funk, Shuffle, New Orleans, Fusion, Minimal, Heavy
#### 🎧 Electronic — House, Techno, Drum & Bass, Dubstep

### Available Drummers

| Drummer | Signature Techniques |
|---------|----------------------|
| **John Bonham** | Triplet vocabulary, behind-the-beat timing |
| **Jeff Porcaro** | Half-time shuffle, studio precision |
| **Dave Weckl** | Linear playing, fusion mastery |
| **Dennis Chambers** | Funk mastery, incredible chops |
| **Jason Roeder** | Atmospheric sludge, minimal creativity |
| **Mikkey Dee** | Speed/precision, versatile power |
| **Gene Hoglan** | Mechanical precision, blast beats |
| **Neil Peart** | Extreme timing precision, linear limb independence, polyrhythmic fills |
| **Buddy Rich** | Virtuosic single-stroke speed, dramatic dynamic contrast |
| **Stewart Copeland** | Reggae/ska-influenced off-beat hi-hat, cross-stick snare |

**Future expansions:** World genres (Latin, Reggae, Afrobeat) — see [Roadmap](#-roadmap).

## 🎵 Examples

### Python API

```python
from midi_drums.api.python_api import DrumGeneratorAPI

api = DrumGeneratorAPI()

# Multi-genre songs with custom parameters
metal_song = api.create_song("metal", "progressive", tempo=140, complexity=0.9)
rock_song = api.create_song("rock", "classic", tempo=130, drummer="bonham")
jazz_song = api.create_song("jazz", "swing", tempo=120, drummer="weckl")
funk_song = api.create_song("funk", "classic", tempo=110, drummer="chambers")
electronic_song = api.create_song("electronic", "techno", tempo=128)

# Batch generation across genres
specs = [
    {'genre': 'metal', 'style': 'death', 'tempo': 180},
    {'genre': 'rock', 'style': 'blues', 'tempo': 95, 'drummer': 'porcaro'},
    {'genre': 'jazz', 'style': 'fusion', 'tempo': 135, 'drummer': 'weckl'},
    {'genre': 'funk', 'style': 'pfunk', 'tempo': 105, 'drummer': 'chambers'},
]
files = api.batch_generate(specs, "output/")

# Individual patterns, applying a drummer style during generation
bonham_verse = api.generate_pattern("rock", "verse", "classic", drummer="bonham")
```

### Direct Module Usage

```python
from midi_drums import DrumGenerator

generator = DrumGenerator()

song = generator.create_song(
    genre="metal",
    style="heavy",
    tempo=155,
    structure=[
        ("intro", 4), ("verse", 8), ("chorus", 8),
        ("verse", 8), ("chorus", 8), ("bridge", 4),
        ("chorus", 8), ("outro", 4),
    ],
    complexity=0.7,
    humanization=0.3,
)

generator.export_midi(song, "custom_song.mid")
```

### CLI

**Using `midi-drums` command (after `uv tool install`):**
```bash
midi-drums generate --genre metal --style death --tempo 180 --complexity 0.8 --output death.mid
midi-drums generate --genre rock --style classic --tempo 140 --drummer bonham --output rock_bonham.mid
midi-drums generate --genre electronic --style dubstep --tempo 140 --output dubstep.mid

midi-drums pattern --genre rock --section verse --style blues --drummer porcaro --output porcaro_verse.mid

midi-drums reaper export --genre metal --style doom --tempo 120 --output doom.rpp --midi

midi-drums info
midi-drums list genres
midi-drums list styles --genre jazz
midi-drums list drummers
```

## 🔌 Plugin System

The plugin architecture makes it easy to extend the system with new genres and drummer styles, using reusable templates and modifications for rapid development.

### Genre Plugin

```python
from midi_drums.plugins.interfaces.genre_plugin import GenrePlugin
from midi_drums.patterns import TemplateComposer, DoubleBassPedal, BlastBeat
from midi_drums.config import TIMING

class MetalGenrePlugin(GenrePlugin):
    @property
    def genre_name(self) -> str:
        return "metal"

    @property
    def supported_styles(self) -> list[str]:
        return ["heavy", "death", "power", "progressive", "thrash", "doom"]

    def generate_pattern(self, section: str, parameters: GenerationParameters) -> Pattern:
        if parameters.style == "death":
            # Declarative composition - just a few lines
            return (
                TemplateComposer(f"death_metal_{section}")
                .add(DoubleBassPedal(subdivision=TIMING.SIXTEENTH, pattern_type="continuous"))
                .add(BlastBeat(style="traditional", intensity=0.9))
                .build(bars=2, complexity=parameters.complexity)
            )
        # ... other styles using templates
```

### Drummer Plugin

```python
from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin
from midi_drums.modifications import BehindBeatTiming, TripletVocabulary, HeavyAccents

class BonhamPlugin(DrummerPlugin):
    def __init__(self):
        self.behind_beat = BehindBeatTiming(max_delay_ms=25.0)
        self.triplets = TripletVocabulary(triplet_probability=0.4)
        self.accents = HeavyAccents(accent_boost=15)

    @property
    def drummer_name(self) -> str:
        return "bonham"

    def apply_style(self, pattern: Pattern) -> Pattern:
        styled_pattern = pattern.copy()
        styled_pattern = self.behind_beat.apply(styled_pattern, intensity=0.7)
        styled_pattern = self.triplets.apply(styled_pattern, intensity=0.8)
        styled_pattern = self.accents.apply(styled_pattern, intensity=0.9)
        return styled_pattern
```

**Available Modifications**: BehindBeatTiming, TripletVocabulary, GhostNoteLayer, LinearCoordination, HeavyAccents, ShuffleFeelApplication, FastChopsTriplets, PocketStretching, MinimalCreativity, SpeedPrecision, TwistedAccents, MechanicalPrecision

**Available Templates**: BasicGroove, DoubleBassPedal, BlastBeat, JazzRidePattern, FunkGhostNotes, CrashAccents, TomFill, TemplateComposer

## 🛠️ Development

### Setup

```bash
uv sync --all-groups     # everything, including dev + AI

uv sync                  # core only
uv sync --group dev      # + dev tools (pytest, ruff, black)
uv sync --group ai       # + AI providers (langchain, anthropic, etc.)

just lint    # ruff + black + isort
just format  # auto-format code
just check   # format + lint + tests
```

### Continuous Integration

GitHub Actions runs automated linting (ruff, black, isort), multi-version testing (Python 3.12, 3.13), and coverage reporting on every push. See [docs/CI_CD.md](docs/CI_CD.md).

### Testing

```bash
pytest                                    # all tests
pytest -m unit                            # unit tests (no API key needed)
pytest -m integration                     # integration tests
pytest -m ai                              # AI tests (requires API key)
pytest -n auto                            # in parallel
pytest --cov=midi_drums --cov-report=html # with coverage
pytest -m "not requires_api"              # skip AI tests if no API key
```

**Test organization:** `tests/unit/`, `tests/integration/`, `tests/ai/`, shared fixtures in `tests/conftest.py`.

**Markers:** `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.ai`, `@pytest.mark.requires_api` (auto-skipped without a key), `@pytest.mark.slow`.

### Project Structure

```
midi_drums/
├── __init__.py              # Main exports (DrumGenerator, Pattern, Song, ...)
├── core/                    # Domain models & value objects (no other-domain deps)
│   ├── models/              # Pattern, Beat, Song, Section, Kit
│   └── value_objects/       # TimeSignature, DrumInstrument, GenerationParameters
├── generation/               # Composition engine, builder, strategies, orchestration
│   ├── engines/              # DrumGenerator - main composition engine
│   ├── builders/             # PatternBuilder - fluent pattern construction
│   ├── strategies/           # PatternStrategy / FillStrategy interfaces
│   └── services/             # GenerationService - high-level orchestration
├── export/                   # MIDI + Reaper file export
│   ├── midi/                 # MIDIEngine, MIDIExporter
│   └── reaper/                # ReaperEngine, ReaperExporter, section/marker models
├── exporters/                # Compat shim re-exporting ReaperExporter from export/reaper/
├── plugins/                  # Genre + drummer plugin system
│   ├── interfaces/            # GenrePlugin, DrummerPlugin
│   ├── registry/               # PluginRegistry, PluginManager, auto-discovery
│   ├── genres/                 # metal, rock, jazz, funk, electronic — 7/7/7/7/4 styles
│   └── drummers/                # bonham, porcaro, weckl, chambers, roeder, dee,
│       ├── hoglan, peart, rich, copeland  # (flat sibling files)
│       └── composite/            # Layered drummer styles (e.g. doom_blues)
├── api/
│   ├── python_api.py       # High-level Python API
│   └── cli.py               # Command-line interface
├── config/
│   └── constants.py        # VELOCITY, TIMING, DEFAULTS constants
├── patterns/
│   └── templates.py        # 8 reusable pattern templates
├── modifications/
│   └── drummer_mods.py     # 12 composable drummer modifications
├── ai/                      # AI-powered generation (optional)
│   ├── ai_api.py            # High-level AI generation API
│   ├── backends.py          # Multi-provider backend config
│   ├── pattern_generator.py # Pydantic AI pattern generation
│   ├── agents/               # Langchain agent orchestration
│   └── prompts/              # Prompt templates for AI generation
├── validation/
│   └── physical_constraints.py # Drummer-physically-playable checks
├── humanization/
│   └── advanced_humanization.py # Timing/velocity humanization
└── utils/
    └── pattern_fixer.py    # Post-generation pattern repair
```

See [`docs/DDD_ARCHITECTURE.md`](docs/DDD_ARCHITECTURE.md) for domain-boundary rules and [`docs/MIGRATION_GUIDE.md`](docs/MIGRATION_GUIDE.md) for pre-DDD-migration import paths.

### Running Examples

```bash
python examples/basic_usage.py       # basic usage walkthrough
python migrate_from_original.py      # compare with the original single-file generator
```

## 🎼 MIDI Output

The system generates professional MIDI files for use in any DAW (Logic Pro,
Pro Tools, Cubase, Reaper, etc.). Note-number output depends on the
`--mapping` preset (or `--mapping-file`) you choose — presets are **not**
all identical:

- **`ezdrummer3`** (default, primary target) — uses EZDrummer 3's real note
  numbers for extended hi-hat articulations (closed-hat edge/tip, tight-hat
  edge/tip, open-hat 1-3/max) that don't exist in General MIDI at all.
- **`gm_drums`** / **`gm`** / **`general_midi`** — strict GM Level 1
  percussion. The extended hi-hat articulations above are collapsed to
  their nearest real GM note (closed-hat family → note 42, open-hat family
  → note 46) so output stays GM-compliant.
- **`studio_drummer3`**, **`addictive_drums`**, **`bfd3`**, **`modo_drums`**,
  **`ml_drums`** — use the same GM-collapsed note table as `gm_drums`
  (no vendor-specific note research has been done for these yet — see
  `claudedocs/research_vendor_drum_midi_maps_20260812.md`); safe to use
  with any GM-compatible sampler today, but not yet verified against each
  vendor's own default map, which may differ from strict GM.
- **Custom mapping** — pass `--mapping-file path/to/mapping.json` (CLI) or
  `mapping_file="path/to/mapping.json"` (`DrumGeneratorAPI.create_song()`)
  to supply your own note table without editing the library. See
  `DrumKit.from_json()` / `DrumKit.from_dict()` for the expected JSON shape.

Run `python -m midi_drums list mappings` for the full list with
descriptions.

### MIDI Features

- ✅ Per-preset drum note mapping (see above)
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

### 🎵 Add New Genres
1. Create a new plugin in `midi_drums/plugins/genres/`
2. Implement the `GenrePlugin` interface
3. Add comprehensive patterns for different sections and styles, using [pattern templates](#-plugin-system) where possible
4. Include characteristic fills and variations

### 🥁 Add Drummer Styles
1. Create a drummer plugin in `midi_drums/plugins/drummers/`
2. Implement the `DrummerPlugin` interface
3. Add signature playing techniques and fills based on research, using [composable modifications](#-plugin-system) where possible
4. Make it compatible with multiple genres

### 🐛 Report Issues
Found a bug? [Open an issue](https://github.com/fsecada01/midi-drums/issues) — include MIDI output samples and steps to reproduce if possible.

### 💡 Suggest Features
New musical genres or styles, advanced humanization techniques, integration with specific DAWs or samplers.

## 📈 Roadmap

### Phase 1: Core Expansion ✅
- [x] Rock, Jazz, and Funk genre plugins (7 styles each)
- [x] 10 drummer plugins (Bonham, Porcaro, Weckl, Chambers, Roeder, Dee, Hoglan, Peart, Rich, Copeland)
- [x] Comprehensive testing and validation system
- [x] Reaper DAW integration with automatic markers
- [x] CLI tool installation (`uv tool install`)
- [x] GitHub Actions CI/CD pipeline

### Phase 2: Advanced Features 🚧
- [x] Electronic genre plugin (House, Techno, Drum & Bass, Dubstep)
- [x] Reaper marker import (generate drums from existing markers) — via the `create_song_sections.lua` REAPER-mode bridge
- [x] Advanced humanization algorithms — `midi_drums/humanization/advanced_humanization.py`
- [x] Groove template system — `midi_drums/patterns/templates.py` (8 templates + `TemplateComposer`)
- [ ] Real-time audio synthesis
- [ ] AI-driven pattern variations

### Phase 3: Integration 🔮
- [ ] REST API for web services
- [ ] DAW integration (VST/AU plugins)
- [ ] Pattern marketplace
- [ ] Visual pattern editor
- [ ] World music genres (Latin, Reggae, Afrobeat)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original Inspiration**: Single-file metal drum generator (`generate_metal_drum_track.py`, preserved for compatibility)
- **MIDI Generation**: [midiutil](https://github.com/MarkCWirt/MIDIUtil) library
- **Target Platform**: [EZDrummer 3](https://www.toontrack.com/product/ezdrummer-3/) compatibility
- **Architecture**: Plugin-based design inspired by modern audio software

---

<div align="center">

**Made with ❤️ for drummers, producers, and music creators**

[⭐ Star this project](https://github.com/fsecada01/midi-drums) • [🐛 Report Bug](https://github.com/fsecada01/midi-drums/issues) • [💡 Request Feature](https://github.com/fsecada01/midi-drums/issues)

</div>
