# MIDI Drums Generator - Comprehensive Refactoring Plan

**Date**: 2025-10-26
**Status**: Draft v1.0
**Objective**: Modernize architecture for congruent system design, optimal performance, and LLM integration

---

## Executive Summary

This refactoring plan transforms the MIDI Drums Generator from a well-architected algorithmic system into an **AI-enhanced, high-performance music generation platform**. The plan focuses on:

1. **Eliminating code duplication** (~30% reduction in LOC)
2. **Performance optimization** (5-10x speedup for batch operations)
3. **LLM integration** (pydantic-ai for structured generation, langchain for complex workflows)
4. **Comprehensive testing** (90%+ coverage with unit + property-based tests)
5. **Enhanced maintainability** (template system, modification registry)

**Estimated Impact**:
- Code reduction: ~2,000 lines eliminated through templates
- Performance: 5-10x improvement in batch generation
- New capabilities: AI-driven pattern variation, natural language control
- Test coverage: 20% → 90%+

---

## Phase 1: Foundation & Structure (Week 1)

### 1.1 Configuration Constants Extraction

**Current Issue**: Magic numbers scattered throughout codebase (~200+ instances)

**Solution**: Create centralized configuration module

```python
# midi_drums/config/constants.py
from dataclasses import dataclass
from typing import Final

@dataclass(frozen=True)
class VelocityRanges:
    """MIDI velocity ranges for different dynamics."""

    # Kick drum
    KICK_WHISPER: Final[int] = 60
    KICK_LIGHT: Final[int] = 95
    KICK_NORMAL: Final[int] = 110
    KICK_HEAVY: Final[int] = 120
    KICK_ACCENT: Final[int] = 127

    # Snare drum
    SNARE_GHOST: Final[int] = 40
    SNARE_LIGHT: Final[int] = 90
    SNARE_NORMAL: Final[int] = 115
    SNARE_HEAVY: Final[int] = 127
    SNARE_RIMSHOT: Final[int] = 125

    # Hi-hat
    HIHAT_WHISPER: Final[int] = 40
    HIHAT_LIGHT: Final[int] = 60
    HIHAT_NORMAL: Final[int] = 80
    HIHAT_ACCENT: Final[int] = 100
    HIHAT_OPEN: Final[int] = 100
    HIHAT_PEDAL: Final[int] = 70

    # Cymbals
    RIDE_LIGHT: Final[int] = 70
    RIDE_NORMAL: Final[int] = 90
    RIDE_BELL: Final[int] = 100
    CRASH_NORMAL: Final[int] = 110
    CRASH_ACCENT: Final[int] = 120
    CHINA_NORMAL: Final[int] = 105
    SPLASH_NORMAL: Final[int] = 95

    # Toms
    TOM_LIGHT: Final[int] = 85
    TOM_NORMAL: Final[int] = 100
    TOM_HEAVY: Final[int] = 115

@dataclass(frozen=True)
class TimingConstants:
    """Beat position constants for rhythmic notation."""

    # Note values
    WHOLE: Final[float] = 4.0
    HALF: Final[float] = 2.0
    QUARTER: Final[float] = 1.0
    EIGHTH: Final[float] = 0.5
    SIXTEENTH: Final[float] = 0.25
    THIRTY_SECOND: Final[float] = 0.125

    # Triplets
    HALF_TRIPLET: Final[float] = 4.0 / 3.0
    QUARTER_TRIPLET: Final[float] = 2.0 / 3.0
    EIGHTH_TRIPLET: Final[float] = 1.0 / 3.0
    SIXTEENTH_TRIPLET: Final[float] = 1.0 / 6.0

    # Dotted notes
    DOTTED_HALF: Final[float] = 3.0
    DOTTED_QUARTER: Final[float] = 1.5
    DOTTED_EIGHTH: Final[float] = 0.75

    # Humanization defaults
    HUMANIZATION_TIMING_VAR: Final[float] = 0.02
    HUMANIZATION_VELOCITY_VAR: Final[int] = 10
    HUMANIZATION_MIN_TIMING: Final[float] = 0.01
    HUMANIZATION_MAX_TIMING: Final[float] = 0.1

@dataclass(frozen=True)
class GenerationDefaults:
    """Default parameters for pattern generation."""

    TEMPO_MIN: Final[int] = 60
    TEMPO_MAX: Final[int] = 300
    TEMPO_DEFAULT: Final[int] = 120

    COMPLEXITY_MIN: Final[float] = 0.0
    COMPLEXITY_MAX: Final[float] = 1.0
    COMPLEXITY_DEFAULT: Final[float] = 0.5

    HUMANIZATION_MIN: Final[float] = 0.0
    HUMANIZATION_MAX: Final[float] = 1.0
    HUMANIZATION_DEFAULT: Final[float] = 0.3

    FILL_FREQUENCY_MIN: Final[float] = 0.0
    FILL_FREQUENCY_MAX: Final[float] = 1.0
    FILL_FREQUENCY_DEFAULT: Final[float] = 0.2

    BARS_DEFAULT: Final[int] = 4
    BARS_MIN: Final[int] = 1
    BARS_MAX: Final[int] = 256

# Singleton instances
VELOCITY = VelocityRanges()
TIMING = TimingConstants()
DEFAULTS = GenerationDefaults()
```

**Usage Example**:
```python
# Before:
builder.kick(0.0, 110)
builder.snare(1.0, 115)

# After:
from midi_drums.config.constants import VELOCITY, TIMING

builder.kick(TIMING.QUARTER * 0, VELOCITY.KICK_NORMAL)
builder.snare(TIMING.QUARTER * 1, VELOCITY.SNARE_NORMAL)
```

**Files to Update**: All genre plugins, drummer plugins, pattern builders (~30 files)

---

### 1.2 Pattern Template System

**Current Issue**: ~2,000 lines of duplicated pattern generation logic

**Solution**: Create reusable pattern templates with composition

```python
# midi_drums/patterns/templates.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from midi_drums.models.pattern import Pattern, PatternBuilder, DrumInstrument
from midi_drums.config.constants import VELOCITY, TIMING

class PatternTemplate(ABC):
    """Base class for reusable pattern structures."""

    @abstractmethod
    def generate(self, builder: PatternBuilder, **kwargs) -> PatternBuilder:
        """Generate pattern using builder."""
        pass

@dataclass
class BasicGroove(PatternTemplate):
    """Standard rock/metal groove: kick + snare + hihat."""

    kick_positions: list[float] = None
    snare_positions: list[float] = None
    hihat_subdivision: float = TIMING.EIGHTH

    def __post_init__(self):
        if self.kick_positions is None:
            self.kick_positions = [0.0, 2.0]  # 1 and 3
        if self.snare_positions is None:
            self.snare_positions = [1.0, 3.0]  # 2 and 4

    def generate(self, builder: PatternBuilder, **kwargs) -> PatternBuilder:
        complexity = kwargs.get('complexity', 0.5)

        # Add kicks
        for pos in self.kick_positions:
            velocity = VELOCITY.KICK_NORMAL + int(complexity * 10)
            builder.kick(pos, velocity)

        # Add snares
        for pos in self.snare_positions:
            velocity = VELOCITY.SNARE_NORMAL + int(complexity * 12)
            builder.snare(pos, velocity)

        # Add hi-hat pattern
        for i in range(int(4.0 / self.hihat_subdivision)):
            pos = i * self.hihat_subdivision
            velocity = VELOCITY.HIHAT_NORMAL
            builder.hihat(pos, velocity)

        return builder

@dataclass
class DoubleBassPedal(PatternTemplate):
    """Fast double bass pattern for metal."""

    subdivision: float = TIMING.SIXTEENTH
    intensity: float = 1.0

    def generate(self, builder: PatternBuilder, **kwargs) -> PatternBuilder:
        beats_per_bar = int(4.0 / self.subdivision)

        for i in range(beats_per_bar):
            pos = i * self.subdivision
            # Alternate velocity for realism
            velocity = VELOCITY.KICK_NORMAL if i % 2 == 0 else VELOCITY.KICK_LIGHT
            velocity = int(velocity * self.intensity)
            builder.kick(pos, velocity)

        return builder

@dataclass
class BlastBeat(PatternTemplate):
    """Death metal blast beat pattern."""

    style: str = "traditional"  # "traditional", "hammer", "gravity"

    def generate(self, builder: PatternBuilder, **kwargs) -> PatternBuilder:
        if self.style == "traditional":
            # Kick + snare on every 8th note
            for i in range(8):
                pos = i * TIMING.EIGHTH
                builder.kick(pos, VELOCITY.KICK_HEAVY)
                builder.snare(pos, VELOCITY.SNARE_HEAVY)
                # Fast hihat
                builder.hihat(pos, VELOCITY.HIHAT_NORMAL)

        elif self.style == "hammer":
            # Faster snare, slower kick
            for i in range(16):
                pos = i * TIMING.SIXTEENTH
                if i % 2 == 0:
                    builder.kick(pos, VELOCITY.KICK_HEAVY)
                builder.snare(pos, VELOCITY.SNARE_HEAVY)
                builder.hihat(pos, VELOCITY.HIHAT_LIGHT)

        return builder

@dataclass
class JazzRidePattern(PatternTemplate):
    """Jazz ride cymbal pattern with swing."""

    swing_ratio: float = 0.33
    accent_pattern: str = "standard"  # "standard", "elvin", "tony"

    def generate(self, builder: PatternBuilder, **kwargs) -> PatternBuilder:
        # Triplet-based swing feel
        for i in range(12):  # 12 triplets in 4/4
            pos = i * TIMING.EIGHTH_TRIPLET

            # Swing: emphasize 1st and 3rd of each triplet
            if i % 3 in [0, 2]:
                if self.accent_pattern == "elvin":
                    # Elvin Jones style: accent every 4th
                    velocity = VELOCITY.RIDE_NORMAL if i % 4 == 0 else VELOCITY.RIDE_LIGHT
                else:
                    velocity = VELOCITY.RIDE_NORMAL

                builder.ride(pos, velocity)

        return builder

@dataclass
class FunkGhostNotes(PatternTemplate):
    """Funk ghost note pattern for snare."""

    density: float = 0.7  # How many 16ths get ghost notes

    def generate(self, builder: PatternBuilder, **kwargs) -> PatternBuilder:
        import random

        for i in range(16):
            pos = i * TIMING.SIXTEENTH

            # Main snare on 2 and 4
            if pos in [1.0, 3.0]:
                builder.snare(pos, VELOCITY.SNARE_NORMAL)
            # Ghost notes on other 16ths (probabilistic)
            elif random.random() < self.density:
                builder.snare(pos, VELOCITY.SNARE_GHOST)

        return builder

class TemplateComposer:
    """Compose multiple templates into complete patterns."""

    def __init__(self, name: str):
        self.name = name
        self.templates: list[PatternTemplate] = []

    def add(self, template: PatternTemplate) -> 'TemplateComposer':
        """Fluent API for adding templates."""
        self.templates.append(template)
        return self

    def build(self, **kwargs) -> Pattern:
        """Build pattern by applying all templates."""
        builder = PatternBuilder(self.name)

        for template in self.templates:
            builder = template.generate(builder, **kwargs)

        return builder.build()

# Usage in genre plugins:
def _generate_verse_pattern(self, style, params, time_sig):
    """Generate verse pattern using templates."""

    if params.style == "heavy":
        return TemplateComposer("metal_heavy_verse") \
            .add(BasicGroove(
                kick_positions=[0.0, 2.0, 2.5],
                snare_positions=[1.0, 3.0]
            )) \
            .build(complexity=params.complexity)

    elif params.style == "death":
        return TemplateComposer("metal_death_verse") \
            .add(BlastBeat(style="traditional")) \
            .add(DoubleBassPedal(intensity=0.9)) \
            .build(complexity=params.complexity)
```

**Benefits**:
- Reduces genre plugin size by ~40%
- Makes patterns more composable and testable
- Easier to add new genres (combine existing templates)
- Clear separation between pattern structure and style

**Files Created**:
- `midi_drums/patterns/templates.py` (~500 lines)
- `midi_drums/patterns/composers.py` (~200 lines)

**Files to Refactor**: All 4 genre plugins (~1,846 lines → ~1,100 lines)

---

### 1.3 Drummer Modification Registry

**Current Issue**: ~2,590 lines of duplicated drummer modification logic

**Solution**: Create modification registry with composable modifications

```python
# midi_drums/plugins/drummer_modifications.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from midi_drums.models.pattern import Pattern, Beat
import random

class DrummerModification(ABC):
    """Base class for drummer style modifications."""

    @abstractmethod
    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Apply modification to pattern.

        Args:
            pattern: Input pattern to modify
            intensity: Modification strength (0.0-1.0)

        Returns:
            Modified pattern (new instance)
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Modification name for logging."""
        pass

@dataclass
class BehindBeatTiming(DrummerModification):
    """Apply behind-the-beat timing (Bonham, Chambers style)."""

    max_delay_ms: float = 20.0  # Maximum delay in milliseconds

    @property
    def name(self) -> str:
        return "behind_beat_timing"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Shift snare hits slightly behind the beat."""
        modified_beats = []

        for beat in pattern.beats:
            new_beat = beat

            if beat.instrument == DrumInstrument.SNARE:
                # Convert ms to beat position offset
                delay = (self.max_delay_ms / 1000.0) * (pattern.tempo / 60.0) * intensity
                new_beat = Beat(
                    position=beat.position + delay,
                    instrument=beat.instrument,
                    velocity=beat.velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent
                )

            modified_beats.append(new_beat)

        return Pattern(
            name=f"{pattern.name}_behind_beat",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, 'modification': self.name}
        )

@dataclass
class TripletVocabulary(DrummerModification):
    """Add triplet-based fills and embellishments (Bonham style)."""

    triplet_probability: float = 0.3

    @property
    def name(self) -> str:
        return "triplet_vocabulary"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Add triplet-based rhythmic vocabulary."""
        from midi_drums.config.constants import TIMING, VELOCITY

        modified_beats = list(pattern.beats)

        # Look for opportunities to add triplets (empty spaces)
        for bar in range(int(pattern.duration_bars())):
            bar_start = bar * 4.0

            # Check beat 4 for triplet fill opportunity
            if random.random() < (self.triplet_probability * intensity):
                # Add descending triplet fill
                for i in range(3):
                    pos = bar_start + 3.0 + (i * TIMING.EIGHTH_TRIPLET)

                    # Descending toms
                    if i == 0:
                        instrument = DrumInstrument.MID_TOM
                    elif i == 1:
                        instrument = DrumInstrument.MID_TOM
                    else:
                        instrument = DrumInstrument.FLOOR_TOM

                    modified_beats.append(Beat(
                        position=pos,
                        instrument=instrument,
                        velocity=VELOCITY.TOM_HEAVY,
                        duration=TIMING.EIGHTH_TRIPLET,
                        ghost_note=False,
                        accent=True
                    ))

        # Sort by position
        modified_beats.sort(key=lambda b: b.position)

        return Pattern(
            name=f"{pattern.name}_triplets",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, 'modification': self.name}
        )

@dataclass
class GhostNoteLayer(DrummerModification):
    """Add ghost notes on snare (Porcaro, Chambers style)."""

    density: float = 0.6  # How many 16ths get ghost notes

    @property
    def name(self) -> str:
        return "ghost_note_layer"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Add subtle ghost notes between main snare hits."""
        from midi_drums.config.constants import TIMING, VELOCITY

        modified_beats = list(pattern.beats)

        # Find main snare hits
        main_snare_positions = [
            b.position for b in pattern.beats
            if b.instrument == DrumInstrument.SNARE and not b.ghost_note
        ]

        # Add ghost notes on 16ths that don't have main snares
        for bar in range(int(pattern.duration_bars())):
            bar_start = bar * 4.0

            for i in range(16):
                pos = bar_start + (i * TIMING.SIXTEENTH)

                # Skip if main snare already exists
                if pos in main_snare_positions:
                    continue

                # Probabilistically add ghost note
                if random.random() < (self.density * intensity):
                    modified_beats.append(Beat(
                        position=pos,
                        instrument=DrumInstrument.SNARE,
                        velocity=VELOCITY.SNARE_GHOST,
                        duration=TIMING.SIXTEENTH,
                        ghost_note=True,
                        accent=False
                    ))

        # Sort by position
        modified_beats.sort(key=lambda b: b.position)

        return Pattern(
            name=f"{pattern.name}_ghost_notes",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, 'modification': self.name}
        )

@dataclass
class LinearCoordination(DrummerModification):
    """Apply linear playing style (Weckl style - no simultaneous limbs)."""

    @property
    def name(self) -> str:
        return "linear_coordination"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Remove overlapping hits to create linear patterns."""
        # Group beats by position (quantize to 32nd notes)
        from collections import defaultdict

        position_groups = defaultdict(list)
        for beat in pattern.beats:
            quantized_pos = round(beat.position * 8) / 8  # 32nd note resolution
            position_groups[quantized_pos].append(beat)

        modified_beats = []

        for pos, beats in sorted(position_groups.items()):
            if len(beats) == 1:
                modified_beats.append(beats[0])
            else:
                # Multiple hits - keep only one based on priority
                # Priority: Snare > Kick > Cymbals > Toms > Hihat
                priority = {
                    DrumInstrument.SNARE: 5,
                    DrumInstrument.KICK: 4,
                    DrumInstrument.CRASH: 3,
                    DrumInstrument.RIDE: 3,
                    DrumInstrument.MID_TOM: 2,
                    DrumInstrument.FLOOR_TOM: 2,
                    DrumInstrument.CLOSED_HH: 1,
                }

                # Keep highest priority hit
                kept_beat = max(beats, key=lambda b: priority.get(b.instrument, 0))
                modified_beats.append(kept_beat)

        return Pattern(
            name=f"{pattern.name}_linear",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, 'modification': self.name}
        )

@dataclass
class HeavyAccents(DrummerModification):
    """Apply heavy accenting and dynamics (metal drummers)."""

    accent_boost: int = 15

    @property
    def name(self) -> str:
        return "heavy_accents"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Increase accent contrast for powerful feel."""
        modified_beats = []

        for beat in pattern.beats:
            new_velocity = beat.velocity

            if beat.accent:
                # Boost accents
                new_velocity = min(127, beat.velocity + int(self.accent_boost * intensity))
            elif beat.ghost_note:
                # Reduce ghost notes for more contrast
                new_velocity = max(20, beat.velocity - int(10 * intensity))

            modified_beats.append(Beat(
                position=beat.position,
                instrument=beat.instrument,
                velocity=new_velocity,
                duration=beat.duration,
                ghost_note=beat.ghost_note,
                accent=beat.accent
            ))

        return Pattern(
            name=f"{pattern.name}_heavy_accents",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, 'modification': self.name}
        )

# Modification registry
class ModificationRegistry:
    """Registry of available drummer modifications."""

    def __init__(self):
        self._modifications: dict[str, type[DrummerModification]] = {}

    def register(self, mod_class: type[DrummerModification]):
        """Register a modification class."""
        # Create temporary instance to get name
        instance = mod_class()
        self._modifications[instance.name] = mod_class

    def get(self, name: str) -> type[DrummerModification] | None:
        """Get modification class by name."""
        return self._modifications.get(name)

    def list_modifications(self) -> list[str]:
        """List all registered modification names."""
        return list(self._modifications.keys())

# Global registry instance
MODIFICATION_REGISTRY = ModificationRegistry()

# Register standard modifications
MODIFICATION_REGISTRY.register(BehindBeatTiming)
MODIFICATION_REGISTRY.register(TripletVocabulary)
MODIFICATION_REGISTRY.register(GhostNoteLayer)
MODIFICATION_REGISTRY.register(LinearCoordination)
MODIFICATION_REGISTRY.register(HeavyAccents)
```

**Usage in Drummer Plugins**:
```python
# midi_drums/plugins/drummers/bonham.py (REFACTORED)
from midi_drums.plugins.base import DrummerPlugin
from midi_drums.plugins.drummer_modifications import (
    BehindBeatTiming,
    TripletVocabulary,
    HeavyAccents
)

class BonhamPlugin(DrummerPlugin):
    """John Bonham style: triplets, behind-beat, powerful."""

    MODIFICATIONS = [
        (BehindBeatTiming(max_delay_ms=25.0), 0.8),
        (TripletVocabulary(triplet_probability=0.4), 0.9),
        (HeavyAccents(accent_boost=20), 0.7),
    ]

    @property
    def drummer_name(self) -> str:
        return "bonham"

    @property
    def compatible_genres(self) -> list[str]:
        return ["rock", "metal", "blues", "hard_rock"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Bonham style modifications."""
        styled_pattern = pattern

        # Apply each modification in sequence
        for modification, intensity in self.MODIFICATIONS:
            styled_pattern = modification.apply(styled_pattern, intensity)

        styled_pattern.name = f"{pattern.name}_bonham"
        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Bonham signature fills (Moby Dick style)."""
        # Keep this method for drummer-specific fills
        return [
            # Simplified - use TemplateComposer for actual fills
        ]
```

**Benefits**:
- Drummer plugins reduce from ~370 lines → ~100 lines each (~70% reduction)
- Modifications are composable and reusable
- Easy to create new drummers by combining modifications
- Testable in isolation
- Clear separation of concerns

**Files Created**:
- `midi_drums/plugins/drummer_modifications.py` (~600 lines)

**Files to Refactor**: All 7 drummer plugins (~2,590 lines → ~700 lines total)

---

## Phase 2: Performance Optimization (Week 2)

### 2.1 Pattern Caching System

```python
# midi_drums/core/cache.py
from functools import lru_cache
from typing import Any
import hashlib
import json

class PatternCache:
    """LRU cache for generated patterns."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: dict[str, Pattern] = {}
        self._access_order: list[str] = []

    def _make_key(
        self,
        genre: str,
        section: str,
        params: GenerationParameters
    ) -> str:
        """Create cache key from generation parameters."""
        # Serialize parameters to dict
        param_dict = {
            'genre': genre,
            'section': section,
            'style': params.style,
            'complexity': round(params.complexity, 2),
            'dynamics': round(params.dynamics, 2),
            'drummer': params.drummer,
            'fill_frequency': round(params.fill_frequency, 2),
            'swing_ratio': round(params.swing_ratio, 2),
        }

        # Create hash
        param_json = json.dumps(param_dict, sort_keys=True)
        return hashlib.md5(param_json.encode()).hexdigest()

    def get(self, key: str) -> Pattern | None:
        """Get pattern from cache."""
        if key in self._cache:
            # Update access order (LRU)
            self._access_order.remove(key)
            self._access_order.append(key)

            # Return deep copy to prevent mutation
            return self._cache[key].copy()

        return None

    def put(self, key: str, pattern: Pattern):
        """Put pattern in cache."""
        # Evict if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]

        # Add to cache
        self._cache[key] = pattern.copy()

        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def clear(self):
        """Clear cache."""
        self._cache.clear()
        self._access_order.clear()

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'utilization': len(self._cache) / self.max_size
        }
```

**Integration in DrumGenerator**:
```python
class DrumGenerator:
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.drum_kit = DrumKit.create_ezdrummer3_kit()
        self.midi_engine = MIDIEngine(drum_kit)
        self.cache = PatternCache(max_size=1000)  # NEW
        self._load_plugins()

    def generate_pattern(
        self,
        genre: str,
        section: str,
        parameters: GenerationParameters | None = None
    ) -> Pattern | None:
        """Generate pattern with caching."""

        if parameters is None:
            parameters = GenerationParameters(genre=genre)

        # Try cache first (skip if humanization enabled)
        if parameters.humanization == 0.0:
            cache_key = self.cache._make_key(genre, section, parameters)
            cached = self.cache.get(cache_key)

            if cached is not None:
                logger.info(f"Cache hit for {genre}/{section}")
                return cached

        # Generate pattern (existing logic)
        pattern = self._generate_pattern_uncached(genre, section, parameters)

        # Cache result (if no humanization)
        if pattern and parameters.humanization == 0.0:
            cache_key = self.cache._make_key(genre, section, parameters)
            self.cache.put(cache_key, pattern)

        return pattern
```

**Expected Performance Gain**: 5-10x speedup for repeated pattern generation

---

### 2.2 Lazy Plugin Loading

```python
# midi_drums/plugins/base.py (REFACTORED)
class LazyPluginRegistry:
    """Registry with lazy plugin instantiation."""

    def __init__(self):
        self._genre_classes: dict[str, type[GenrePlugin]] = {}
        self._drummer_classes: dict[str, type[DrummerPlugin]] = {}

        # Cached instances (only create when needed)
        self._genre_instances: dict[str, GenrePlugin] = {}
        self._drummer_instances: dict[str, DrummerPlugin] = {}

    def register_genre(self, plugin_class: type[GenrePlugin]):
        """Register genre plugin class (not instance)."""
        # Create temporary instance only to get name
        temp_instance = plugin_class()
        genre_name = temp_instance.genre_name

        self._genre_classes[genre_name] = plugin_class
        logger.info(f"Registered genre plugin class: {genre_name}")

    def get_genre_plugin(self, genre: str) -> GenrePlugin | None:
        """Get genre plugin instance (lazy instantiation)."""
        # Return cached instance if exists
        if genre in self._genre_instances:
            return self._genre_instances[genre]

        # Instantiate on first access
        if genre in self._genre_classes:
            plugin_class = self._genre_classes[genre]
            instance = plugin_class()
            self._genre_instances[genre] = instance
            logger.debug(f"Lazy-loaded genre plugin: {genre}")
            return instance

        return None

    def list_genres(self) -> list[str]:
        """List registered genres (no instantiation needed)."""
        return list(self._genre_classes.keys())
```

**Expected Performance Gain**: 50-100ms faster startup

---

### 2.3 Batch Generation Optimization

```python
# midi_drums/api/python_api.py (ENHANCED)
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator

class DrumGeneratorAPI:
    """Enhanced API with batch optimization."""

    def batch_generate_parallel(
        self,
        specs: list[dict],
        output_dir: str = "./output",
        max_workers: int = 4
    ) -> list[str]:
        """Generate multiple songs in parallel."""

        def generate_single(spec: dict) -> str:
            """Generate single song and return filename."""
            genre = spec['genre']
            style = spec.get('style', 'default')
            tempo = spec.get('tempo', 120)
            output_name = spec.get('output', f"{genre}_{style}.mid")

            song = self.create_song(genre, style, tempo=tempo)
            output_path = f"{output_dir}/{output_name}"
            self.save_as_midi(song, output_path)

            return output_path

        # Generate in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(generate_single, spec) for spec in specs]
            results = [f.result() for f in futures]

        return results

    def stream_generate(
        self,
        specs: list[dict]
    ) -> Iterator[tuple[int, Song]]:
        """Stream generation results (memory efficient for large batches)."""
        for i, spec in enumerate(specs):
            genre = spec['genre']
            style = spec.get('style', 'default')
            tempo = spec.get('tempo', 120)

            song = self.create_song(genre, style, tempo=tempo)
            yield (i, song)
```

**Expected Performance Gain**: 3-4x speedup for batch generation (4 cores)

---

## Phase 3: LLM Integration (Week 3-4)

### 3.1 Architecture Decision: Pydantic-AI vs LangChain

**Decision**: Use **both** strategically:

1. **Pydantic-AI** for:
   - Structured pattern generation (validated Beat/Pattern outputs)
   - Parameter validation and defaults
   - Type-safe LLM interactions
   - CLI-focused tasks (perfect for this project)

2. **LangChain** for:
   - Complex multi-step workflows (song narrative → structure → patterns)
   - Retrieval-Augmented Generation (music theory knowledge)
   - Agent-based pattern improvement loops
   - Future web API integration

**Why both?**
- Pydantic-AI: Better for CLI, simpler, type-safe, perfect for structured outputs
- LangChain: Better for complex workflows, RAG, agents, future-proofing

---

### 3.2 Pydantic-AI Integration: Structured Pattern Generation

```python
# midi_drums/ai/pattern_generator.py
from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from midi_drums.models.pattern import Pattern, Beat, DrumInstrument
from midi_drums.config.constants import VELOCITY, TIMING

class BeatSpec(BaseModel):
    """Structured specification for a beat."""

    position: float = Field(
        ...,
        ge=0.0,
        lt=4.0,
        description="Beat position in 4/4 bar (0.0-4.0)"
    )
    instrument: str = Field(
        ...,
        description="Drum instrument name (kick, snare, hihat, etc.)"
    )
    velocity: int = Field(
        ...,
        ge=20,
        le=127,
        description="MIDI velocity (20-127)"
    )
    ghost_note: bool = Field(
        default=False,
        description="Whether this is a ghost note (quiet accent)"
    )
    accent: bool = Field(
        default=False,
        description="Whether this is an accented note"
    )

    @field_validator('instrument')
    @classmethod
    def validate_instrument(cls, v: str) -> str:
        """Validate instrument name."""
        valid_instruments = [
            'kick', 'snare', 'rim', 'closed_hh', 'open_hh', 'pedal_hh',
            'ride', 'ride_bell', 'crash', 'china', 'splash',
            'mid_tom', 'floor_tom'
        ]

        if v.lower() not in valid_instruments:
            raise ValueError(f"Invalid instrument: {v}. Must be one of {valid_instruments}")

        return v.lower()

class PatternSpec(BaseModel):
    """Structured specification for a complete pattern."""

    name: str = Field(..., description="Pattern name")
    beats: list[BeatSpec] = Field(..., description="List of beats in pattern")
    style_description: str = Field(..., description="Musical style description")
    complexity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Pattern complexity (0.0-1.0)"
    )
    genre_fit_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How well pattern fits requested genre (0.0-1.0)"
    )

    @field_validator('beats')
    @classmethod
    def validate_beats(cls, v: list[BeatSpec]) -> list[BeatSpec]:
        """Validate beat list."""
        if len(v) == 0:
            raise ValueError("Pattern must have at least one beat")

        if len(v) > 100:
            raise ValueError("Pattern has too many beats (max 100)")

        return v

class AIPatternGenerator:
    """Generate drum patterns using Claude via Pydantic-AI."""

    def __init__(self, api_key: str):
        """Initialize with Anthropic API key."""
        self.model = AnthropicModel(
            'claude-sonnet-4',
            api_key=api_key
        )

        # Create agent with structured output
        self.agent = Agent(
            self.model,
            result_type=PatternSpec,
            system_prompt="""You are an expert drummer and music producer.

            Generate realistic, musically valid drum patterns based on user requests.

            Follow these principles:
            1. MUSICAL VALIDITY: Patterns must be playable by a human drummer
            2. GENRE AUTHENTICITY: Respect genre conventions and characteristics
            3. RHYTHMIC LOGIC: Use proper subdivision and timing
            4. DYNAMIC VARIATION: Use velocity and accents for expressiveness

            Beat positions:
            - Use standard subdivisions: 0.0, 0.25 (16th), 0.5 (8th), 1.0 (quarter), etc.
            - For triplets: use 1/3, 2/3, etc.

            Velocity guidelines:
            - Ghost notes: 30-50
            - Light: 60-80
            - Normal: 90-110
            - Heavy/accent: 115-127

            Common patterns:
            - Basic rock: kick on 1&3, snare on 2&4, 8th note hi-hat
            - Blast beat: kick+snare on all 8ths, fast hi-hat
            - Jazz ride: triplet feel on ride, kicks "dropping bombs"
            - Funk: "the one" emphasis, ghost notes on 16ths
            """
        )

    async def generate_from_description(
        self,
        description: str,
        genre: str,
        section: str = "verse",
        bars: int = 1
    ) -> Pattern:
        """Generate pattern from natural language description.

        Args:
            description: Natural language description of desired pattern
            genre: Musical genre (metal, rock, jazz, funk)
            section: Song section (verse, chorus, bridge)
            bars: Number of bars to generate

        Returns:
            Generated Pattern object

        Example:
            >>> pattern = await generator.generate_from_description(
            ...     "Aggressive death metal with blast beats and double bass",
            ...     genre="metal",
            ...     section="verse"
            ... )
        """

        # Create user prompt
        user_prompt = f"""Generate a {genre} drum pattern for a {section} section.

Description: {description}

Requirements:
- Generate exactly {bars} bar(s) (4/4 time)
- Follow {genre} genre conventions
- Be musically authentic and playable
- Include appropriate dynamics and accents
"""

        # Run agent to get structured output
        result = await self.agent.run(user_prompt)

        # Convert PatternSpec to Pattern
        pattern = self._spec_to_pattern(result.data, bars)

        return pattern

    def _spec_to_pattern(self, spec: PatternSpec, bars: int) -> Pattern:
        """Convert PatternSpec to Pattern object."""
        from midi_drums.models.pattern import PatternBuilder, TimeSignature

        # Map instrument names to enums
        instrument_map = {
            'kick': DrumInstrument.KICK,
            'snare': DrumInstrument.SNARE,
            'rim': DrumInstrument.RIM,
            'closed_hh': DrumInstrument.CLOSED_HH,
            'open_hh': DrumInstrument.OPEN_HH,
            'pedal_hh': DrumInstrument.PEDAL_HH,
            'ride': DrumInstrument.RIDE,
            'ride_bell': DrumInstrument.RIDE_BELL,
            'crash': DrumInstrument.CRASH,
            'china': DrumInstrument.CHINA,
            'splash': DrumInstrument.SPLASH,
            'mid_tom': DrumInstrument.MID_TOM,
            'floor_tom': DrumInstrument.FLOOR_TOM,
        }

        # Create beats
        beats = []
        for beat_spec in spec.beats:
            # Tile pattern across bars if needed
            for bar in range(bars):
                position = bar * 4.0 + beat_spec.position

                beats.append(Beat(
                    position=position,
                    instrument=instrument_map[beat_spec.instrument],
                    velocity=beat_spec.velocity,
                    duration=0.2,  # Default duration
                    ghost_note=beat_spec.ghost_note,
                    accent=beat_spec.accent
                ))

        # Sort by position
        beats.sort(key=lambda b: b.position)

        # Create pattern
        pattern = Pattern(
            name=spec.name,
            beats=beats,
            time_signature=TimeSignature(4, 4),
            subdivision=16,
            swing_ratio=0.0,
            metadata={
                'ai_generated': True,
                'style_description': spec.style_description,
                'complexity_score': spec.complexity_score,
                'genre_fit_score': spec.genre_fit_score,
            }
        )

        return pattern

    async def improve_pattern(
        self,
        pattern: Pattern,
        feedback: str
    ) -> Pattern:
        """Improve existing pattern based on feedback.

        Args:
            pattern: Existing pattern to improve
            feedback: Natural language feedback

        Returns:
            Improved pattern

        Example:
            >>> improved = await generator.improve_pattern(
            ...     original_pattern,
            ...     "Make it more aggressive with faster hi-hats"
            ... )
        """

        # Convert pattern to description for LLM
        pattern_desc = self._pattern_to_description(pattern)

        user_prompt = f"""Here is an existing drum pattern:

{pattern_desc}

User feedback: {feedback}

Generate an improved version that addresses this feedback while maintaining musical validity.
"""

        result = await self.agent.run(user_prompt)
        improved_pattern = self._spec_to_pattern(result.data, int(pattern.duration_bars()))

        return improved_pattern

    def _pattern_to_description(self, pattern: Pattern) -> str:
        """Convert Pattern to text description for LLM."""
        description = f"Pattern: {pattern.name}\n"
        description += f"Duration: {pattern.duration_bars()} bars\n"
        description += f"Beats:\n"

        for beat in pattern.beats[:20]:  # Limit to first 20 beats
            description += f"  - {beat.instrument.name} at position {beat.position:.2f}, "
            description += f"velocity {beat.velocity}"
            if beat.ghost_note:
                description += " (ghost)"
            if beat.accent:
                description += " (accent)"
            description += "\n"

        if len(pattern.beats) > 20:
            description += f"  ... ({len(pattern.beats) - 20} more beats)\n"

        return description
```

**CLI Integration**:
```bash
# New CLI command using AI generation
python -m midi_drums ai-generate \
    --description "Aggressive blast beat with double bass and cymbal accents" \
    --genre metal \
    --section verse \
    --output ai_pattern.mid

python -m midi_drums ai-improve \
    --input existing_pattern.mid \
    --feedback "Add more ghost notes and make the hi-hat pattern more complex" \
    --output improved_pattern.mid
```

---

### 3.3 LangChain Integration: Complex Workflows

```python
# midi_drums/ai/narrative_composer.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage

class NarrativeComposer:
    """Compose complete songs from narrative descriptions using LangChain agents."""

    def __init__(self, api_key: str):
        """Initialize with Anthropic API key."""
        self.llm = ChatAnthropic(
            model="claude-sonnet-4",
            anthropic_api_key=api_key,
            temperature=0.7
        )

        # Create tools for agent
        self.tools = self._create_tools()

        # Create agent
        self.agent = self._create_agent()

    def _create_tools(self) -> list[Tool]:
        """Create LangChain tools for song composition."""

        def analyze_narrative(narrative: str) -> dict:
            """Analyze narrative and extract song structure."""
            # This would use LLM to parse narrative
            return {
                'structure': [
                    ('intro', 4),
                    ('verse', 8),
                    ('chorus', 8),
                    ('verse', 8),
                    ('chorus', 8),
                    ('bridge', 4),
                    ('chorus', 8),
                    ('outro', 4)
                ],
                'genre': 'metal',
                'style': 'death',
                'tempo': 180,
                'dynamics': {
                    'intro': 0.3,
                    'verse': 0.7,
                    'chorus': 1.0,
                    'bridge': 0.5,
                    'outro': 0.4
                }
            }

        def generate_section(
            section_type: str,
            intensity: float,
            genre: str,
            style: str
        ) -> str:
            """Generate a specific song section."""
            # This would call DrumGenerator
            from midi_drums import DrumGenerator

            generator = DrumGenerator()
            params = GenerationParameters(
                genre=genre,
                style=style,
                complexity=intensity,
                dynamics=intensity
            )

            pattern = generator.generate_pattern(genre, section_type, params)
            return f"Generated {section_type} pattern with {len(pattern.beats)} beats"

        tools = [
            Tool(
                name="analyze_narrative",
                func=analyze_narrative,
                description="Analyze a narrative description and extract song structure, genre, tempo, and dynamics"
            ),
            Tool(
                name="generate_section",
                func=generate_section,
                description="Generate a specific song section with given parameters"
            ),
        ]

        return tools

    def _create_agent(self) -> AgentExecutor:
        """Create LangChain agent for song composition."""

        system_prompt = """You are an expert music producer specializing in drum composition.

Your job is to:
1. Analyze narrative descriptions of songs
2. Create appropriate song structures (intro, verse, chorus, bridge, outro)
3. Determine genre, style, and tempo from descriptions
4. Generate each section with appropriate dynamics and complexity

When analyzing narratives, consider:
- Story arc (tension, release, climax)
- Energy trajectory
- Genre characteristics
- Section purposes (intro sets mood, verse tells story, chorus is memorable, bridge provides contrast)

Be creative but musically logical."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

        return executor

    async def compose_from_narrative(self, narrative: str) -> Song:
        """Compose complete song from narrative description.

        Args:
            narrative: Story-like description of song

        Returns:
            Complete Song object

        Example:
            >>> song = await composer.compose_from_narrative(
            ...     '''Create a death metal song that tells the story of a battle.
            ...     Start with ominous intro, build tension in verses,
            ...     explode into brutal chorus, then slow breakdown bridge,
            ...     final crushing chorus and fade out.'''
            ... )
        """

        # Run agent to analyze and generate
        result = await self.agent.ainvoke({
            "input": f"""Compose a complete drum track from this narrative:

{narrative}

Steps:
1. Analyze the narrative to determine song structure
2. Choose appropriate genre and style
3. Determine tempo and dynamics for each section
4. Generate patterns for each section
5. Assemble into complete song
"""
        })

        # Parse agent output and create Song
        # (Implementation would parse agent's work and call DrumGenerator)

        return song
```

**Usage**:
```python
from midi_drums.ai.narrative_composer import NarrativeComposer

composer = NarrativeComposer(api_key="...")

# Generate from narrative
song = await composer.compose_from_narrative("""
    Create an epic progressive metal song:
    - Mysterious acoustic intro with light percussion
    - Build with verses that gradually increase intensity
    - Explosive chorus with double bass and blast beats
    - Technical bridge with odd time signatures
    - Final chorus with maximum power
    - Slow fade outro
""")

# Save result
api = DrumGeneratorAPI()
api.save_as_midi(song, "epic_prog_metal.mid")
```

---

### 3.4 RAG for Music Theory Knowledge

```python
# midi_drums/ai/music_theory_rag.py
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

class MusicTheoryRAG:
    """Retrieval-Augmented Generation for music theory knowledge."""

    def __init__(self):
        """Initialize with music theory knowledge base."""

        # Create knowledge base documents
        theory_docs = [
            Document(
                page_content="""
                Death Metal Drumming Characteristics:
                - Blast beats (kick + snare on 8th or 16th notes simultaneously)
                - Double bass pedal at high speeds (16th note triplets)
                - Emphasis on power and precision over groove
                - Cymbals: China for accents, ride for blast beats
                - Fill patterns: Fast tom rolls, often descending
                - Tempo: 160-260 BPM typical
                """,
                metadata={'genre': 'metal', 'style': 'death'}
            ),
            Document(
                page_content="""
                Jazz Swing Drumming Characteristics:
                - Ride cymbal: triplet-based pattern (ding-ding-a, ding-ding-a)
                - Hi-hat: foot on 2 and 4 (backbeat)
                - Kick drum: "dropping bombs" - sparse, accenting phrases
                - Snare: very light "feathering" on all 4 beats, ghost notes
                - Brushes: common for ballads and medium tempos
                - Tempo: 120-240 BPM typical
                - Feel: Swung 8ths (triplet subdivision)
                """,
                metadata={'genre': 'jazz', 'style': 'swing'}
            ),
            # ... more theory documents
        ]

        # Create embeddings and vector store
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = Chroma.from_documents(
            documents=theory_docs,
            embedding=self.embeddings,
            persist_directory="./midi_drums_knowledge"
        )

    async def get_relevant_theory(
        self,
        query: str,
        genre: str = None,
        k: int = 3
    ) -> list[Document]:
        """Retrieve relevant music theory for query."""

        # Build filter
        filter_dict = {}
        if genre:
            filter_dict['genre'] = genre

        # Semantic search
        docs = await self.vectorstore.asimilarity_search(
            query,
            k=k,
            filter=filter_dict if filter_dict else None
        )

        return docs

    async def augmented_generation(
        self,
        description: str,
        genre: str,
        llm: ChatAnthropic
    ) -> str:
        """Generate pattern with theory knowledge augmentation."""

        # Retrieve relevant theory
        theory_docs = await self.get_relevant_theory(
            f"{genre} drumming {description}",
            genre=genre
        )

        # Build context
        theory_context = "\n\n".join([doc.page_content for doc in theory_docs])

        # Augmented prompt
        prompt = f"""Using this music theory knowledge:

{theory_context}

Generate a drum pattern for:
Genre: {genre}
Description: {description}
"""

        result = await llm.ainvoke([HumanMessage(content=prompt)])

        return result.content
```

---

## Phase 4: Testing & Quality (Week 5)

### 4.1 Comprehensive Unit Tests

```python
# tests/unit/test_models.py
import pytest
from midi_drums.models.pattern import Pattern, Beat, DrumInstrument, PatternBuilder
from midi_drums.models.song import Song, Section, GenerationParameters
from midi_drums.config.constants import VELOCITY, TIMING

class TestBeat:
    """Unit tests for Beat model."""

    def test_beat_creation(self):
        """Test basic beat creation."""
        beat = Beat(
            position=0.0,
            instrument=DrumInstrument.KICK,
            velocity=VELOCITY.KICK_NORMAL,
            duration=TIMING.QUARTER,
            ghost_note=False,
            accent=False
        )

        assert beat.position == 0.0
        assert beat.instrument == DrumInstrument.KICK
        assert beat.velocity == VELOCITY.KICK_NORMAL

    def test_beat_validation_velocity_bounds(self):
        """Test velocity validation in Beat.__post_init__."""

        # Too low
        with pytest.raises(ValueError, match="Velocity must be between 0 and 127"):
            Beat(
                position=0.0,
                instrument=DrumInstrument.KICK,
                velocity=-10,
                duration=TIMING.QUARTER
            )

        # Too high
        with pytest.raises(ValueError, match="Velocity must be between 0 and 127"):
            Beat(
                position=0.0,
                instrument=DrumInstrument.KICK,
                velocity=200,
                duration=TIMING.QUARTER
            )

    def test_beat_equality(self):
        """Test beat equality comparison."""
        beat1 = Beat(0.0, DrumInstrument.KICK, 100, 0.2)
        beat2 = Beat(0.0, DrumInstrument.KICK, 100, 0.2)
        beat3 = Beat(0.5, DrumInstrument.SNARE, 110, 0.2)

        assert beat1 == beat2
        assert beat1 != beat3

class TestPattern:
    """Unit tests for Pattern model."""

    def test_pattern_creation(self):
        """Test pattern creation."""
        beats = [
            Beat(0.0, DrumInstrument.KICK, 100, 0.2),
            Beat(1.0, DrumInstrument.SNARE, 110, 0.2),
        ]

        pattern = Pattern(
            name="test_pattern",
            beats=beats,
            time_signature=TimeSignature(4, 4),
            subdivision=16
        )

        assert pattern.name == "test_pattern"
        assert len(pattern.beats) == 2
        assert pattern.duration_bars() == 1.0

    def test_pattern_humanize(self):
        """Test pattern humanization."""
        original = Pattern(
            name="original",
            beats=[
                Beat(0.0, DrumInstrument.KICK, 100, 0.2),
                Beat(1.0, DrumInstrument.SNARE, 110, 0.2),
            ],
            time_signature=TimeSignature(4, 4),
            subdivision=16
        )

        humanized = original.humanize(timing_variance=0.05, velocity_variance=10)

        # Positions should be slightly different
        assert humanized.beats[0].position != original.beats[0].position
        assert abs(humanized.beats[0].position - original.beats[0].position) < 0.1

        # Velocities should be slightly different
        assert humanized.beats[0].velocity != original.beats[0].velocity
        assert abs(humanized.beats[0].velocity - original.beats[0].velocity) <= 10

    def test_pattern_copy(self):
        """Test pattern deep copy."""
        original = Pattern(
            name="original",
            beats=[Beat(0.0, DrumInstrument.KICK, 100, 0.2)],
            time_signature=TimeSignature(4, 4),
            subdivision=16
        )

        copied = original.copy()

        # Should be equal but different objects
        assert copied.name == original.name
        assert copied.beats == original.beats
        assert copied is not original
        assert copied.beats is not original.beats

class TestPatternBuilder:
    """Unit tests for PatternBuilder."""

    def test_builder_fluent_api(self):
        """Test fluent API chaining."""
        pattern = PatternBuilder("test") \
            .kick(0.0, 100) \
            .snare(1.0, 110) \
            .hihat(0.0, 80) \
            .hihat(0.5, 80) \
            .build()

        assert len(pattern.beats) == 4
        assert pattern.name == "test"

    def test_builder_sorting(self):
        """Test that beats are sorted by position."""
        pattern = PatternBuilder("test") \
            .snare(2.0, 110) \
            .kick(0.0, 100) \
            .hihat(1.0, 80) \
            .build()

        # Should be sorted: kick (0.0), hihat (1.0), snare (2.0)
        assert pattern.beats[0].position == 0.0
        assert pattern.beats[1].position == 1.0
        assert pattern.beats[2].position == 2.0
```

---

### 4.2 Property-Based Testing

```python
# tests/unit/test_properties.py
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite
import pytest

from midi_drums.models.pattern import Pattern, Beat, DrumInstrument
from midi_drums.api.python_api import DrumGeneratorAPI

@composite
def valid_tempo(draw):
    """Generate valid tempo values."""
    return draw(st.integers(min_value=60, max_value=300))

@composite
def valid_complexity(draw):
    """Generate valid complexity values."""
    return draw(st.floats(min_value=0.0, max_value=1.0))

@composite
def valid_genre_and_style(draw):
    """Generate valid genre/style combinations."""
    genres = {
        'metal': ['heavy', 'death', 'power', 'progressive', 'thrash', 'doom', 'breakdown'],
        'rock': ['classic', 'blues', 'alternative', 'progressive', 'punk', 'hard', 'pop'],
        'jazz': ['swing', 'bebop', 'fusion', 'latin', 'ballad', 'hard_bop', 'contemporary'],
        'funk': ['classic', 'pfunk', 'shuffle', 'new_orleans', 'fusion', 'minimal', 'heavy']
    }

    genre = draw(st.sampled_from(list(genres.keys())))
    style = draw(st.sampled_from(genres[genre]))

    return (genre, style)

class TestGenerationProperties:
    """Property-based tests for pattern generation."""

    @given(
        tempo=valid_tempo(),
        complexity=valid_complexity()
    )
    @settings(max_examples=100)
    def test_generation_always_succeeds(self, tempo, complexity):
        """Test that generation never crashes with valid parameters."""
        api = DrumGeneratorAPI()

        # Should not raise exception
        song = api.create_song(
            genre="metal",
            style="heavy",
            tempo=tempo,
            complexity=complexity
        )

        assert song is not None
        assert song.tempo == tempo
        assert len(song.sections) > 0

    @given(genre_style=valid_genre_and_style())
    @settings(max_examples=50)
    def test_all_genre_style_combinations(self, genre_style):
        """Test all genre/style combinations work."""
        genre, style = genre_style
        api = DrumGeneratorAPI()

        song = api.create_song(genre, style, tempo=120)

        assert song is not None
        assert song.tempo == 120
        assert len(song.sections) > 0

    @given(
        humanization=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=50)
    def test_humanization_preserves_pattern_integrity(self, humanization):
        """Test that humanization doesn't break patterns."""
        from midi_drums.models.pattern import Pattern, Beat, DrumInstrument

        # Create simple pattern
        original = Pattern(
            name="test",
            beats=[
                Beat(0.0, DrumInstrument.KICK, 100, 0.2),
                Beat(1.0, DrumInstrument.SNARE, 110, 0.2),
            ],
            time_signature=TimeSignature(4, 4),
            subdivision=16
        )

        # Humanize
        timing_var = humanization * 0.05
        velocity_var = int(humanization * 20)
        humanized = original.humanize(timing_var, velocity_var)

        # Should preserve beat count
        assert len(humanized.beats) == len(original.beats)

        # Velocities should stay in valid range
        for beat in humanized.beats:
            assert 0 <= beat.velocity <= 127

        # Positions should stay reasonable
        for beat in humanized.beats:
            assert -0.5 <= beat.position <= 5.0  # Allow some variance
```

---

### 4.3 Integration Tests

```python
# tests/integration/test_full_workflow.py
import pytest
import tempfile
import os
from pathlib import Path

from midi_drums.api.python_api import DrumGeneratorAPI

class TestFullWorkflow:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def api(self):
        """Fixture providing API instance."""
        return DrumGeneratorAPI()

    @pytest.fixture
    def temp_output_dir(self):
        """Fixture providing temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_complete_song_generation_metal(self, api, temp_output_dir):
        """Test complete metal song generation."""

        # Generate song
        song = api.metal_song(
            style="death",
            tempo=180,
            complexity=0.8,
            humanization=0.3
        )

        # Verify structure
        assert song is not None
        assert song.tempo == 180
        assert len(song.sections) >= 5  # intro, verse, chorus, bridge, outro

        # Export MIDI
        output_path = temp_output_dir / "death_metal.mid"
        api.save_as_midi(song, str(output_path))

        # Verify file exists
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_batch_generation(self, api, temp_output_dir):
        """Test batch generation workflow."""

        specs = [
            {'genre': 'metal', 'style': 'heavy', 'tempo': 155},
            {'genre': 'rock', 'style': 'classic', 'tempo': 140},
            {'genre': 'jazz', 'style': 'swing', 'tempo': 180},
        ]

        files = api.batch_generate(specs, str(temp_output_dir))

        # Verify all files created
        assert len(files) == 3

        for file_path in files:
            path = Path(file_path)
            assert path.exists()
            assert path.stat().st_size > 0

    def test_drummer_style_application(self, api, temp_output_dir):
        """Test drummer style application workflow."""

        # Generate with drummer
        song = api.create_song(
            genre="rock",
            style="classic",
            tempo=140,
            drummer="bonham"
        )

        # Verify drummer metadata
        assert song is not None
        for section in song.sections:
            if section.pattern:
                # Check for Bonham characteristics in metadata
                assert 'bonham' in section.pattern.name.lower() or \
                       section.pattern.metadata.get('drummer') == 'bonham'

    def test_all_genres_and_styles(self, api):
        """Test that all genre/style combinations work."""

        genres_styles = {
            'metal': ['heavy', 'death', 'power', 'progressive', 'thrash', 'doom'],
            'rock': ['classic', 'blues', 'alternative', 'progressive', 'punk', 'hard'],
            'jazz': ['swing', 'bebop', 'fusion', 'latin', 'ballad', 'hard_bop'],
            'funk': ['classic', 'pfunk', 'shuffle', 'new_orleans', 'fusion', 'minimal']
        }

        for genre, styles in genres_styles.items():
            for style in styles:
                # Should not raise exception
                song = api.create_song(genre, style, tempo=120)

                assert song is not None
                assert len(song.sections) > 0

                # Verify section patterns exist
                for section in song.sections:
                    assert section.pattern is not None
                    assert len(section.pattern.beats) > 0
```

---

## Phase 5: Documentation & Examples (Week 6)

### 5.1 API Documentation

```python
# Update all docstrings with comprehensive examples

class DrumGeneratorAPI:
    """High-level API for MIDI drum generation.

    This API provides simple methods for generating complete drum tracks
    across multiple genres, styles, and with various drummer personalities.

    Quick Start:
        >>> from midi_drums.api.python_api import DrumGeneratorAPI
        >>>
        >>> api = DrumGeneratorAPI()
        >>>
        >>> # Generate a complete song
        >>> song = api.metal_song(style="death", tempo=180)
        >>> api.save_as_midi(song, "death_metal.mid")
        >>>
        >>> # Generate with drummer style
        >>> song = api.rock_song(style="classic", drummer="bonham")
        >>> api.save_as_midi(song, "bonham_rock.mid")

    Available Genres:
        - metal: Heavy, death, power, progressive, thrash, doom, breakdown
        - rock: Classic, blues, alternative, progressive, punk, hard, pop
        - jazz: Swing, bebop, fusion, latin, ballad, hard_bop, contemporary
        - funk: Classic, pfunk, shuffle, new_orleans, fusion, minimal, heavy

    Available Drummers:
        - bonham: John Bonham (Led Zeppelin) - Triplets, behind-beat, powerful
        - porcaro: Jeff Porcaro (Toto) - Shuffle, ghost notes, studio precision
        - weckl: Dave Weckl - Linear, fusion, sophisticated
        - chambers: Dennis Chambers - Funk mastery, pocket, chops
        - roeder: Jason Roeder (Neurosis) - Atmospheric, sludge, minimal
        - dee: Mikkey Dee (Motörhead) - Speed, precision, power
        - hoglan: Gene Hoglan - Blast beats, progressive, mechanical precision

    Performance:
        - Caching: Patterns are cached for repeated parameters (5-10x speedup)
        - Batch: Use batch_generate_parallel() for multi-core generation
        - Streaming: Use stream_generate() for memory-efficient large batches

    See Also:
        - DrumGenerator: Lower-level generation engine
        - Pattern: Pattern data model
        - Song: Song structure model
    """

    def create_song(
        self,
        genre: str,
        style: str = "default",
        tempo: int = 120,
        structure: list[tuple[str, int]] | None = None,
        complexity: float = 0.5,
        humanization: float = 0.3,
        drummer: str | None = None,
        fill_frequency: float = 0.2
    ) -> Song:
        """Create a complete song with multiple sections.

        Args:
            genre: Musical genre (metal, rock, jazz, funk)
            style: Genre-specific style (e.g., "death" for metal)
            tempo: Beats per minute (60-300)
            structure: Optional song structure as list of (section, bars) tuples
                Default: [(intro, 4), (verse, 8), (chorus, 8), (verse, 8),
                         (chorus, 8), (bridge, 4), (chorus, 8), (outro, 4)]
            complexity: Pattern complexity (0.0-1.0)
                - 0.0-0.3: Simple, basic patterns
                - 0.4-0.6: Moderate complexity (default)
                - 0.7-1.0: Complex, technical patterns
            humanization: Timing/velocity randomization (0.0-1.0)
                - 0.0: Perfectly quantized (robotic)
                - 0.3: Subtle humanization (default)
                - 0.5+: Noticeable human feel
            drummer: Optional drummer style to apply
            fill_frequency: How often to add fills (0.0-1.0)

        Returns:
            Complete Song object ready for MIDI export

        Raises:
            ValueError: If genre/style combination is invalid
            ValueError: If tempo is out of range

        Examples:
            Basic usage:
                >>> api = DrumGeneratorAPI()
                >>> song = api.create_song("metal", "heavy", tempo=155)
                >>> api.save_as_midi(song, "heavy_metal.mid")

            Custom structure:
                >>> song = api.create_song(
                ...     "jazz",
                ...     "bebop",
                ...     tempo=220,
                ...     structure=[
                ...         ("intro", 8),
                ...         ("verse", 16),
                ...         ("solo", 32),
                ...         ("outro", 8)
                ...     ]
                ... )

            With drummer style:
                >>> song = api.create_song(
                ...     "rock",
                ...     "classic",
                ...     tempo=140,
                ...     drummer="bonham",
                ...     complexity=0.7
                ... )

        Performance Notes:
            - First call per genre loads plugins (~100-200ms)
            - Subsequent calls are cached if humanization=0.0
            - Typical generation time: 50-200ms depending on structure

        See Also:
            - metal_song(), rock_song(), jazz_song(), funk_song(): Convenience methods
            - generate_pattern(): Generate single pattern
            - batch_generate(): Generate multiple songs
        """
        # Implementation...
```

---

### 5.2 Usage Examples

```python
# examples/advanced_usage.py
"""Advanced usage examples for MIDI Drums Generator."""

from midi_drums.api.python_api import DrumGeneratorAPI
from midi_drums.models.song import GenerationParameters
import asyncio

def example_1_basic_generation():
    """Example 1: Basic song generation across genres."""

    api = DrumGeneratorAPI()

    # Metal
    metal_song = api.metal_song("death", tempo=180, complexity=0.9)
    api.save_as_midi(metal_song, "death_metal.mid")

    # Rock
    rock_song = api.rock_song("classic", drummer="bonham")
    api.save_as_midi(rock_song, "bonham_rock.mid")

    # Jazz
    jazz_song = api.jazz_song("bebop", tempo=220, drummer="weckl")
    api.save_as_midi(jazz_song, "bebop_jazz.mid")

    # Funk
    funk_song = api.funk_song("classic", drummer="chambers")
    api.save_as_midi(funk_song, "funk_classic.mid")

def example_2_batch_generation():
    """Example 2: Batch generation with parallel processing."""

    api = DrumGeneratorAPI()

    # Define specifications
    specs = [
        {'genre': 'metal', 'style': 'heavy', 'tempo': 155, 'output': 'metal_heavy.mid'},
        {'genre': 'metal', 'style': 'death', 'tempo': 180, 'output': 'metal_death.mid'},
        {'genre': 'metal', 'style': 'progressive', 'tempo': 140, 'output': 'metal_prog.mid'},
        {'genre': 'rock', 'style': 'classic', 'tempo': 140, 'output': 'rock_classic.mid'},
        {'genre': 'jazz', 'style': 'swing', 'tempo': 180, 'output': 'jazz_swing.mid'},
    ]

    # Generate in parallel (4 cores)
    files = api.batch_generate_parallel(specs, output_dir="./output", max_workers=4)

    print(f"Generated {len(files)} files:")
    for file in files:
        print(f"  - {file}")

def example_3_custom_structure():
    """Example 3: Custom song structures."""

    api = DrumGeneratorAPI()

    # Epic progressive metal with extended structure
    epic_structure = [
        ("intro", 8),           # Long atmospheric intro
        ("verse", 8),
        ("pre_chorus", 4),
        ("chorus", 8),
        ("verse", 8),
        ("pre_chorus", 4),
        ("chorus", 8),
        ("bridge", 8),          # Technical bridge
        ("solo", 16),           # Extended solo section
        ("breakdown", 8),       # Heavy breakdown
        ("chorus", 8),
        ("outro", 8),
    ]

    song = api.create_song(
        genre="metal",
        style="progressive",
        tempo=145,
        structure=epic_structure,
        complexity=0.9,
        humanization=0.4
    )

    api.save_as_midi(song, "epic_prog_metal.mid")

async def example_4_ai_generation():
    """Example 4: AI-driven pattern generation."""

    from midi_drums.ai.pattern_generator import AIPatternGenerator

    # Initialize AI generator
    ai_gen = AIPatternGenerator(api_key="your_api_key")

    # Generate from description
    pattern = await ai_gen.generate_from_description(
        description="Aggressive blast beat with china cymbal accents every 2 bars",
        genre="metal",
        section="verse",
        bars=4
    )

    # Save pattern
    api = DrumGeneratorAPI()
    api.save_pattern_as_midi(pattern, "ai_blast_beat.mid", tempo=200)

    print(f"Generated AI pattern: {pattern.name}")
    print(f"Complexity score: {pattern.metadata['complexity_score']:.2f}")
    print(f"Genre fit score: {pattern.metadata['genre_fit_score']:.2f}")

async def example_5_narrative_composition():
    """Example 5: Compose from narrative description."""

    from midi_drums.ai.narrative_composer import NarrativeComposer

    composer = NarrativeComposer(api_key="your_api_key")

    # Compose from story
    song = await composer.compose_from_narrative("""
        Create a death metal epic that tells the story of an ancient battle.

        Start with a dark, atmospheric intro using sparse percussion.
        Build tension with verses that gradually increase in intensity.
        Explode into a brutal chorus with full blast beats and double bass.
        Include a technical bridge with odd time signatures (7/8).
        Final chorus should be the most intense part.
        End with a slow, heavy outro that fades to silence.
    """)

    # Save result
    api = DrumGeneratorAPI()
    api.save_as_midi(song, "battle_epic.mid")

def example_6_drummer_comparison():
    """Example 6: Compare different drummer styles on same pattern."""

    api = DrumGeneratorAPI()

    drummers = ["bonham", "porcaro", "weckl", "chambers"]

    for drummer in drummers:
        song = api.rock_song(
            style="classic",
            tempo=140,
            drummer=drummer,
            complexity=0.6
        )

        api.save_as_midi(song, f"rock_classic_{drummer}.mid")

    print("Generated 4 versions with different drummer styles")

if __name__ == "__main__":
    # Run examples
    print("Example 1: Basic generation")
    example_1_basic_generation()

    print("\nExample 2: Batch generation")
    example_2_batch_generation()

    print("\nExample 3: Custom structure")
    example_3_custom_structure()

    # AI examples (async)
    print("\nExample 4: AI generation")
    asyncio.run(example_4_ai_generation())

    print("\nExample 5: Narrative composition")
    asyncio.run(example_5_narrative_composition())

    print("\nExample 6: Drummer comparison")
    example_6_drummer_comparison()
```

---

## Summary & Timeline

### Phase Overview

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|--------------|
| 1. Foundation | Week 1 | Constants, templates, modifications | Config module, pattern templates, modification registry |
| 2. Performance | Week 2 | Caching, lazy loading, batch optimization | PatternCache, LazyPluginRegistry, parallel generation |
| 3. LLM Integration | Week 3-4 | Pydantic-AI, LangChain, RAG | AI pattern generation, narrative composition, theory RAG |
| 4. Testing | Week 5 | Unit tests, property tests, integration | 90%+ test coverage, comprehensive test suite |
| 5. Documentation | Week 6 | API docs, examples, guides | Complete documentation, advanced examples |

### Expected Impact

**Code Quality**:
- LOC reduction: ~2,000 lines eliminated (~30%)
- Duplication reduction: ~70% in drummer plugins, ~40% in genre plugins
- Test coverage: 20% → 90%+

**Performance**:
- Startup: 50-100ms faster (lazy loading)
- Pattern generation: 5-10x faster (caching)
- Batch generation: 3-4x faster (parallel processing)

**New Capabilities**:
- AI pattern generation from natural language
- Narrative-driven composition
- Music theory RAG for enhanced authenticity
- Structured validation with Pydantic-AI
- Complex workflows with LangChain agents

**Maintainability**:
- Clear separation of concerns
- Composable components
- Easy to extend (new genres, drummers, modifications)
- Comprehensive test coverage
- Professional documentation

---

## Next Steps

1. **Review & Approval**: Review this plan and approve approach
2. **Dependency Setup**: Add pydantic-ai, langchain, testing libraries
3. **Phase 1 Implementation**: Start with constants and templates
4. **Incremental Rollout**: Refactor one module at a time
5. **Continuous Testing**: Add tests as we refactor
6. **Documentation**: Update docs throughout process

**Ready to begin implementation?**
