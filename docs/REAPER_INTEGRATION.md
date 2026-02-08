# Reaper DAW Integration

> **Status**: 🚧 In Design | **Priority**: Workflow A (MIDI → Reaper) | **Complexity**: Medium

## Overview

This document outlines the architecture and implementation plan for integrating the MIDI Drums Generator with Cockos Reaper DAW through `.RPP` (Reaper Project) file manipulation.

## Table of Contents

- [Use Cases](#use-cases)
- [Architecture](#architecture)
- [Implementation Phases](#implementation-phases)
- [API Design](#api-design)
- [RPP File Format](#rpp-file-format)
- [Dependencies](#dependencies)
- [Testing Strategy](#testing-strategy)

## Use Cases

### Primary: Workflow A - MIDI Drums → Reaper Markers

**Goal**: Generate MIDI drum performance → Add markers/regions to Reaper project

**User Story**:
> As a music producer, I want to generate a drum MIDI performance and automatically add section markers (intro, verse, chorus, bridge, outro) to my existing Reaper project, so that my project structure matches the generated drum track.

**Workflow**:
```python
from midi_drums import DrumGenerator
from midi_drums.exporters import ReaperExporter

# 1. Generate MIDI drums
generator = DrumGenerator()
song = generator.create_song(
    genre="metal",
    style="doom",
    tempo=120,
    structure=[
        ("intro", 4),
        ("verse", 8),
        ("chorus", 8),
        ("bridge", 4),
        ("outro", 4),
    ]
)

# 2. Export to Reaper with markers
exporter = ReaperExporter()
exporter.export_with_markers(
    song=song,
    input_rpp="my_project.rpp",     # Existing Reaper project
    output_rpp="my_project_drums.rpp",  # New project with markers
    add_midi_track=True              # Also add MIDI track
)
```

**Result**: New `.rpp` file with:
- Original project content preserved (immutable operation)
- Section markers at correct time positions
- Optional: MIDI track with drum performance

### Secondary: Workflow B - Reaper Markers → MIDI Drums

**Goal**: Parse Reaper markers → Generate aligned MIDI drums

**User Story**:
> As a music producer with an existing Reaper project, I want to generate drum MIDI that aligns with my existing markers/sections, so the drums match my song structure.

**Workflow**:
```python
from midi_drums.exporters import ReaperExporter

# Parse markers and generate aligned drums
exporter = ReaperExporter()
song = exporter.generate_from_markers(
    input_rpp="my_project.rpp",
    genre="metal",
    style="death",
    output_midi="aligned_drums.mid"
)
```

**Result**: MIDI file with drum patterns aligned to existing Reaper markers.

## Architecture

### Module Structure

```
midi_drums/
├── engines/
│   ├── midi_engine.py (existing)
│   ├── reaper_engine.py (NEW)
│   └── __init__.py
├── exporters/
│   ├── __init__.py
│   ├── reaper_exporter.py (NEW)  # High-level API
│   └── templates/
│       └── base_project.rpp (NEW)  # Minimal Reaper template
├── parsers/
│   ├── __init__.py
│   └── rpp_parser.py (NEW)  # RPP file parsing
└── models/
    ├── reaper_models.py (NEW)  # Marker, Region data models
    └── ... (existing)
```

### Data Flow: Workflow A (MIDI → Reaper)

```
Song Object
    ↓
ReaperExporter.export_with_markers()
    ↓
1. Calculate marker positions (bars → seconds)
    ↓
2. Parse input .rpp file (rpp library)
    ↓
3. Create marker elements
    ↓
4. (Optional) Create MIDI track
    ↓
5. Serialize to new .rpp file
    ↓
Output .rpp file (immutable)
```

### Data Flow: Workflow B (Reaper → MIDI)

```
Input .rpp file
    ↓
ReaperExporter.generate_from_markers()
    ↓
1. Parse .rpp file
    ↓
2. Extract markers/regions
    ↓
3. Calculate section durations
    ↓
4. Generate Song structure
    ↓
5. Generate MIDI patterns per section
    ↓
Output MIDI file
```

## Implementation Phases

### Phase 1: Core Infrastructure (MVP) - Week 1

**Deliverables**:
- ✅ Research .RPP marker syntax (reverse-engineer)
- ✅ Create `ReaperEngine` class
- ✅ Create `ReaperExporter` API
- ✅ Implement marker position calculation
- ✅ Basic .rpp parsing/generation
- ✅ Unit tests for core functions

**Acceptance Criteria**:
- Can add single marker to .rpp file
- Can open resulting file in Reaper
- Marker appears at correct time position

### Phase 2: Workflow A Implementation - Week 1-2

**Deliverables**:
- ✅ Multi-marker support
- ✅ Section-based marker naming
- ✅ Marker color customization
- ✅ MIDI track insertion (optional)
- ✅ Integration tests
- ✅ Example scripts

**Acceptance Criteria**:
- Can export full song with all section markers
- MIDI track loads correctly in Reaper
- All markers align with section boundaries

### Phase 3: Workflow B Implementation - Week 2-3

**Deliverables**:
- ✅ RPP marker parsing
- ✅ Song structure generation from markers
- ✅ Aligned MIDI generation
- ✅ Integration tests

**Acceptance Criteria**:
- Can parse markers from existing .rpp
- Generated MIDI aligns with marker boundaries

### Phase 4: Enhancements (Future)

**Features**:
- Tempo/time signature synchronization
- Region support (time-spanning markers)
- Multiple MIDI tracks per instrument group
- Reaper FX chain templates
- Live Reaper control (via reapy)

## API Design

### ReaperEngine (Low-level)

```python
class ReaperEngine:
    """Low-level Reaper .rpp file manipulation."""

    def __init__(self, timing_tolerance: float = 0.01):
        """Initialize engine with timing tolerance."""

    def create_marker(
        self,
        position_seconds: float,
        name: str,
        color: str = "#FF5733",
        marker_id: int = 1
    ) -> Element:
        """Create marker element for .rpp file."""

    def add_markers_to_project(
        self,
        rpp_content: str,
        markers: List[Marker]
    ) -> str:
        """Insert markers into .rpp content."""

    def create_midi_track(
        self,
        song: Song,
        track_name: str = "MIDI Drums"
    ) -> Element:
        """Create MIDI track element."""
```

### ReaperExporter (High-level API)

```python
class ReaperExporter:
    """High-level API for Reaper integration."""

    def export_with_markers(
        self,
        song: Song,
        input_rpp: str,
        output_rpp: str,
        add_midi_track: bool = True,
        marker_color: str = "#FF5733"
    ) -> None:
        """Export song with markers to Reaper project.

        Args:
            song: Song object with sections
            input_rpp: Path to existing Reaper project (immutable)
            output_rpp: Path to new project file
            add_midi_track: Also add MIDI track with performance
            marker_color: Hex color for markers
        """

    def generate_from_markers(
        self,
        input_rpp: str,
        genre: str,
        style: str,
        output_midi: str,
        **kwargs
    ) -> Song:
        """Generate MIDI drums aligned to Reaper markers.

        Args:
            input_rpp: Reaper project with markers
            genre: Drum genre (metal, rock, jazz, funk)
            style: Genre-specific style
            output_midi: Output MIDI file path
            **kwargs: Additional generation parameters

        Returns:
            Generated Song object
        """

    def calculate_marker_positions(
        self,
        song: Song
    ) -> List[Marker]:
        """Calculate time positions for each section."""
```

### Data Models

```python
@dataclass
class Marker:
    """Reaper marker representation."""
    position_seconds: float
    name: str
    color: str = "#FF5733"
    marker_id: int = 1

@dataclass
class ReaperTrack:
    """Reaper track representation."""
    name: str
    midi_source: Optional[str] = None
    volume: float = 1.0
    pan: float = 0.0
```

## RPP File Format

### Marker Syntax (Hypothesis - needs verification)

Based on research, Reaper `.rpp` markers likely follow this structure:

```
<MARKER 1 position "name" color flags>
```

**Example**:
```
<MARKER 1 0.0 "Intro" 0 0>
<MARKER 2 8.0 "Verse" 0 0>
<MARKER 3 24.0 "Chorus" 0 0>
```

**Fields**:
- `1` = Marker ID
- `0.0` = Position in seconds
- `"Intro"` = Marker name
- `0 0` = Color and flags (needs verification)

### Time Position Calculation

```python
def bars_to_seconds(
    bars: int,
    tempo: int,
    time_signature: TimeSignature
) -> float:
    """Convert bars to seconds.

    Formula:
        total_beats = bars * beats_per_bar
        total_seconds = (total_beats / tempo) * 60

    Example:
        4 bars @ 120 BPM (4/4) = 4 * 4 / 120 * 60 = 8 seconds
    """
    beats_per_bar = time_signature.numerator
    total_beats = bars * beats_per_bar
    return (total_beats / tempo) * 60.0
```

## Dependencies

### Required

```python
# pyproject.toml
[project]
dependencies = [
    "midiutil>=1.2.1",  # Existing
    "rpp>=0.5.0",       # NEW - RPP parsing/generation
]
```

### Optional (Future)

```python
[project.optional-dependencies]
reaper = [
    "reapy>=0.10.0",  # Live Reaper control (Phase 4)
]
```

## Testing Strategy

### Unit Tests

**File**: `tests/unit/engines/test_reaper_engine.py`

```python
def test_marker_creation():
    """Test marker element creation."""

def test_time_position_calculation():
    """Test bars-to-seconds conversion."""

def test_marker_serialization():
    """Test marker to .rpp string format."""
```

**File**: `tests/unit/exporters/test_reaper_exporter.py`

```python
def test_export_with_markers():
    """Test full export workflow."""

def test_marker_position_calculation():
    """Test marker position calculation from Song."""
```

### Integration Tests

**File**: `tests/integration/test_reaper_integration.py`

```python
def test_full_export_workflow():
    """Test complete MIDI → Reaper workflow."""
    # 1. Generate song
    # 2. Export to .rpp
    # 3. Verify .rpp can be loaded
    # 4. Check marker positions

def test_parse_and_generate():
    """Test Reaper → MIDI workflow."""
    # 1. Load .rpp with markers
    # 2. Generate aligned MIDI
    # 3. Verify alignment
```

### Manual Validation

1. **Export test**:
   ```bash
   python examples/reaper_export_demo.py
   ```
2. **Open in Reaper**: Load `output.rpp` and verify:
   - Markers appear at correct positions
   - MIDI track loads correctly
   - Playback aligns with markers

## Example Usage

### Quick Start

```python
from midi_drums.api import DrumGeneratorAPI
from midi_drums.exporters import ReaperExporter

# Generate drums
api = DrumGeneratorAPI()
song = api.create_song("metal", "doom", tempo=120)

# Export to Reaper
exporter = ReaperExporter()
exporter.export_with_markers(
    song=song,
    input_rpp="template.rpp",
    output_rpp="doom_metal_project.rpp"
)
```

### Advanced Options

```python
# Customize markers
exporter.export_with_markers(
    song=song,
    input_rpp="template.rpp",
    output_rpp="project.rpp",
    add_midi_track=True,
    marker_color="#00FF00",  # Green markers
    track_name="Metal Drums",
    track_volume=0.8
)
```

### CLI Usage

The Reaper integration is also available through the command-line interface.

**Generate drums and create Reaper project**:
```bash
# Basic usage - creates both .rpp and .mid files
python -m midi_drums.api.cli reaper export \
    --genre metal \
    --style doom \
    --tempo 120 \
    --output doom_project.rpp \
    --midi

# With all options
python -m midi_drums.api.cli reaper export \
    --genre metal \
    --style death \
    --tempo 180 \
    --output death_metal.rpp \
    --midi death_drums.mid \
    --complexity 0.8 \
    --humanization 0.4 \
    --drummer hoglan \
    --marker-color "#FF0000" \
    --template my_template.rpp \
    --name "Death Metal Song"
```

**Add markers to existing project** (future):
```bash
# Note: Currently stubbed - requires MIDI loading implementation
python -m midi_drums.api.cli reaper add-markers \
    --song existing_drums.mid \
    --output project_with_markers.rpp \
    --template my_project.rpp \
    --marker-color "#00FF00"
```

**Available options**:
- `--genre`: Genre (metal, rock, jazz, funk)
- `--style`: Style within genre
- `--tempo`: Tempo in BPM (default: 120)
- `--output, -o`: Output Reaper project file (.rpp)
- `--midi`: Export MIDI file (auto-generates name or use custom path)
- `--complexity`: Complexity level 0.0-1.0 (default: 0.5)
- `--humanization`: Humanization level 0.0-1.0 (default: 0.3)
- `--drummer`: Drummer style plugin to apply
- `--marker-color`: Hex color for markers (default: #FF5733)
- `--template`: Input Reaper template to use as base
- `--name`: Custom song name

## Success Criteria

- ✅ Can add markers to .rpp files programmatically
- ✅ Markers appear at correct time positions in Reaper
- ✅ Generated .rpp files load without errors in Reaper
- ✅ MIDI tracks play correctly with proper routing
- ✅ All tests pass (unit + integration)
- ✅ Immutable operations (original files unchanged)
- ✅ Documentation complete with examples

## References

- [rpp Python Library](https://github.com/Perlence/rpp)
- [Reaper RPP Format Discussion](https://forum.cockos.com/forumdisplay.php?f=24)
- [Reaper ReaScript Documentation](https://www.reaper.fm/sdk/reascript/reascript.php)

## Next Steps

1. ✅ Research .RPP marker syntax (create test file in Reaper)
2. ⬜ Install rpp library and prototype parsing
3. ⬜ Implement `ReaperEngine` class
4. ⬜ Implement `ReaperExporter` API
5. ⬜ Write comprehensive tests
6. ⬜ Create example scripts
7. ⬜ Update main documentation
