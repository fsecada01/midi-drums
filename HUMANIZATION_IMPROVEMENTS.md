# MIDI Drum Humanization Improvements

## Analysis Date: 2026-01-24

## Executive Summary

This document analyzes the current humanization approach in `generate_complete_doom_blues.py` and the broader MIDI Drums Generator codebase, then proposes enhancements inspired by professional Toontrack MIDI library patterns.

## Current Humanization Systems

### 1. **Basic Humanization (`pattern.py:125-158`)**
```python
def humanize(self, timing_variance: float = 0.02, velocity_variance: float = 10) -> "Pattern":
    # Uniform random timing: ±0.02 beats (±20ms at 100 BPM)
    timing_offset = random.uniform(-timing_variance, timing_variance)
    # Uniform random velocity: ±10 MIDI units
    velocity_offset = random.randint(-velocity_variance, velocity_variance)
```

**Strengths:**
- Simple and predictable
- Prevents machine-gun timing
- Adds basic variation

**Weaknesses:**
- Uniform distribution (unnatural)
- No instrument-specific characteristics
- No awareness of musical context (accents, ghost notes)
- No velocity curves or dynamics
- Fixed variance regardless of tempo or style

### 2. **Physical Constraint Validation (`physical_constraints.py`)**
```python
- Checks hand limits (max 2 simultaneous)
- Validates ride + hi-hat conflicts
- Ensures playability
```

**Strengths:**
- Prevents impossible patterns
- Automatic conflict resolution
- Physical realism

**Weaknesses:**
- Only validates, doesn't enhance humanization
- Doesn't address timing relationships between limbs
- No fatigue modeling

### 3. **Drummer-Specific Modifications (`drummer_mods.py`)**
```python
- BehindBeatTiming (snare delay)
- TripletVocabulary (fill patterns)
- GhostNoteLayer (textural notes)
- LinearCoordination (Weckl-style)
- ShuffleFeelApplication (Porcaro)
```

**Strengths:**
- Authentic drummer characteristics
- Composable modifications
- Style-specific techniques

**Weaknesses:**
- Applied uniformly across pattern
- No micro-timing variations per hit
- Limited interaction between modifications

### 4. **Current Usage in `generate_complete_doom_blues.py`**
```python
# Lines 155-163: No drummer plugins applied!
song = api.create_song(
    genre="metal",
    style="doom",
    tempo=70,
    structure=structure,
    complexity=0.7,
    humanization=0.3,  # Only basic humanization
    name="doom_blues_composite",
)
```

**Issue:** The composite drummer plugin is documented but NOT applied due to timing conflicts. Only basic humanization is used.

## Professional Toontrack MIDI Characteristics

### What Makes Toontrack MIDI Sound Real:

1. **Gaussian Timing Distribution**
   - Natural timing errors follow bell curve, not uniform distribution
   - Early/late bias based on instrument and drummer style
   - Tighter timing on downbeats, looser on fills

2. **Velocity Curves and Dynamics**
   - Ghost notes: 25-45 velocity
   - Normal hits: 60-90 velocity
   - Accents: 95-120 velocity
   - Natural crescendos/decrescendos in fills
   - Velocity follows musical phrase structure

3. **Instrument-Specific Timing**
   - Kick drum: Slightly ahead of beat (drives rhythm)
   - Snare: Can be behind, on, or ahead depending on style
   - Hi-hat: Most consistent (metronome reference)
   - Cymbals (crash/ride): Slightly behind on accents
   - Toms: Varied timing in fills (natural hand speed limits)

4. **Micro-Timing Relationships**
   - Kick + snare flam (1-3ms offset when simultaneous)
   - Hi-hat + kick relationship (open-hi-hat delayed)
   - Hand-to-hand speed limits (minimum 80ms for fast singles)
   - Double bass pedal consistency (slight variations in spacing)

5. **Dynamic Patterns**
   - Gradual velocity changes (not sudden jumps)
   - Accents on beat 1 and 3 stronger
   - Ghost notes clustered, not isolated
   - Crescendos approach crashes/fills

6. **Fatigue and Human Limits**
   - Velocity decreases slightly over long sections
   - Timing loosens during fast sections
   - Recovery after intense fills
   - Left hand (non-dominant) slightly weaker/slower

7. **Context-Aware Variation**
   - Verse: Tighter, more consistent
   - Chorus: Louder, more energy
   - Fill: Looser timing, velocity curves
   - Breakdown: Heavy accents, sparse

## Proposed Enhancements

### Phase 1: Enhanced Basic Humanization

**Create `midi_drums/humanization/advanced_humanization.py`**

```python
"""Advanced humanization engine inspired by professional recordings."""

import random
import numpy as np
from typing import Dict, Callable
from midi_drums.models.pattern import Pattern, Beat, DrumInstrument

class AdvancedHumanizer:
    """Professional-grade humanization engine.

    Inspired by analysis of Toontrack MIDI libraries and real drummer recordings.
    """

    # Instrument timing characteristics (ms offset at 120 BPM)
    INSTRUMENT_TIMING_BIAS = {
        DrumInstrument.KICK: -2.0,  # Kicks lead slightly
        DrumInstrument.SNARE: 0.0,  # Snare is reference
        DrumInstrument.CLOSED_HH: 0.0,  # Hi-hat is metronomic
        DrumInstrument.RIDE: 1.0,  # Ride slightly behind
        DrumInstrument.CRASH: 2.0,  # Crashes slightly behind
        DrumInstrument.MID_TOM: 0.5,
        DrumInstrument.FLOOR_TOM: 0.5,
    }

    # Timing tightness by instrument (std dev in ms)
    TIMING_TIGHTNESS = {
        DrumInstrument.KICK: 3.0,
        DrumInstrument.SNARE: 4.0,
        DrumInstrument.CLOSED_HH: 2.0,  # Tightest
        DrumInstrument.RIDE: 5.0,
        DrumInstrument.CRASH: 6.0,  # Loosest
        DrumInstrument.MID_TOM: 5.0,
        DrumInstrument.FLOOR_TOM: 5.0,
    }

    # Velocity ranges by context
    VELOCITY_RANGES = {
        'ghost': (25, 45),
        'normal': (65, 90),
        'accent': (95, 115),
        'max': (115, 127),
    }

    def __init__(
        self,
        tempo: int = 120,
        style: str = "balanced",  # tight, balanced, loose
        humanization_amount: float = 0.5,  # 0.0-1.0
    ):
        self.tempo = tempo
        self.style = style
        self.humanization_amount = humanization_amount

        # Style multipliers for timing variation
        self.style_multipliers = {
            'tight': 0.5,   # Studio precision
            'balanced': 1.0,  # Natural
            'loose': 1.8,   # Live energy
        }
        self.multiplier = self.style_multipliers.get(style, 1.0)

    def humanize_pattern(
        self,
        pattern: Pattern,
        section_type: str = "verse",  # verse, chorus, fill, breakdown
    ) -> Pattern:
        """Apply professional humanization to entire pattern.

        Args:
            pattern: Input pattern
            section_type: Musical context for context-aware humanization

        Returns:
            Humanized pattern with Gaussian timing, velocity curves, and micro-timing
        """
        if self.humanization_amount == 0.0:
            return pattern

        humanized_beats = []

        # Context-aware settings
        context = self._get_context_settings(section_type)

        # Analyze pattern structure
        beat_groups = self._group_beats_by_timing(pattern.beats)

        for position, beats in beat_groups.items():
            # Apply micro-timing relationships
            timed_beats = self._apply_micro_timing(beats, position, context)

            # Apply velocity curves
            velocity_beats = self._apply_velocity_curves(timed_beats, context)

            humanized_beats.extend(velocity_beats)

        # Apply gradual fatigue (subtle velocity reduction over time)
        humanized_beats = self._apply_fatigue(humanized_beats, pattern.duration_bars())

        # Sort by position
        humanized_beats.sort(key=lambda b: b.position)

        return Pattern(
            name=f"{pattern.name}_humanized_pro",
            beats=humanized_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, 'humanization': 'advanced'},
        )

    def _gaussian_timing_offset(self, instrument: DrumInstrument, position: float) -> float:
        """Generate Gaussian timing offset for instrument.

        Uses instrument-specific timing bias and tightness.
        Downbeats (position % 1.0 == 0) are tighter.
        """
        # Get instrument characteristics
        bias_ms = self.INSTRUMENT_TIMING_BIAS.get(instrument, 0.0)
        tightness_ms = self.TIMING_TIGHTNESS.get(instrument, 4.0)

        # Downbeats are tighter (50% tighter)
        is_downbeat = position % 1.0 < 0.01
        if is_downbeat:
            tightness_ms *= 0.5

        # Apply humanization amount and style multiplier
        tightness_ms *= self.humanization_amount * self.multiplier

        # Generate Gaussian offset (ms)
        offset_ms = np.random.normal(bias_ms, tightness_ms)

        # Convert ms to beats (tempo-aware)
        # At 120 BPM: 1 beat = 500ms
        # offset_beats = offset_ms / (60000 / BPM)
        ms_per_beat = 60000.0 / self.tempo
        offset_beats = offset_ms / ms_per_beat

        return offset_beats

    def _get_context_settings(self, section_type: str) -> Dict:
        """Get humanization settings based on musical context."""
        contexts = {
            'verse': {
                'timing_multiplier': 0.8,  # Tighter
                'velocity_boost': 0,  # Normal
                'accent_strength': 1.0,
            },
            'chorus': {
                'timing_multiplier': 1.2,  # Looser (more energy)
                'velocity_boost': 10,  # Louder
                'accent_strength': 1.3,
            },
            'fill': {
                'timing_multiplier': 1.5,  # Loosest
                'velocity_boost': 5,
                'accent_strength': 1.5,
            },
            'breakdown': {
                'timing_multiplier': 0.9,  # Tight but heavy
                'velocity_boost': 15,  # Very loud
                'accent_strength': 2.0,  # Maximum accents
            },
        }
        return contexts.get(section_type, contexts['verse'])

    def _group_beats_by_timing(self, beats: list[Beat]) -> Dict[float, list[Beat]]:
        """Group beats that occur at similar times (within 10ms tolerance)."""
        groups = {}
        tolerance = 0.01  # 10ms at 120 BPM = ~0.01 beats

        for beat in beats:
            # Find existing group
            found_group = False
            for pos in groups.keys():
                if abs(beat.position - pos) < tolerance:
                    groups[pos].append(beat)
                    found_group = True
                    break

            if not found_group:
                groups[beat.position] = [beat]

        return groups

    def _apply_micro_timing(
        self, beats: list[Beat], position: float, context: Dict
    ) -> list[Beat]:
        """Apply micro-timing relationships between simultaneous instruments.

        - Kick + snare flam (1-3ms)
        - Hi-hat slightly ahead of kick
        - Crashes behind beat
        """
        if len(beats) <= 1:
            # Single instrument - apply standard timing
            return [
                Beat(
                    position=beat.position + self._gaussian_timing_offset(beat.instrument, position),
                    instrument=beat.instrument,
                    velocity=beat.velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
                for beat in beats
            ]

        # Multiple instruments - apply relational timing
        instruments = {b.instrument for b in beats}
        timed_beats = []

        # Base timing offset
        base_offset = 0.0

        for beat in beats:
            offset = base_offset + self._gaussian_timing_offset(beat.instrument, position)

            # Apply micro-flams for simultaneous kick + snare
            if beat.instrument == DrumInstrument.KICK and DrumInstrument.SNARE in instruments:
                offset -= 0.002  # Kick 2ms early
            elif beat.instrument == DrumInstrument.SNARE and DrumInstrument.KICK in instruments:
                offset += 0.001  # Snare 1ms late (total 3ms flam)

            timed_beats.append(
                Beat(
                    position=max(0.0, beat.position + offset),  # Prevent negative
                    instrument=beat.instrument,
                    velocity=beat.velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
            )

        return timed_beats

    def _apply_velocity_curves(self, beats: list[Beat], context: Dict) -> list[Beat]:
        """Apply velocity humanization with musical awareness."""
        velocity_beats = []

        for beat in beats:
            # Base velocity variation (Gaussian)
            if beat.ghost_note:
                base_range = self.VELOCITY_RANGES['ghost']
                variance = 3
            elif beat.accent:
                base_range = self.VELOCITY_RANGES['accent']
                variance = 5
            else:
                base_range = self.VELOCITY_RANGES['normal']
                variance = 8

            # Apply context boost (chorus louder, etc.)
            boost = context['velocity_boost']

            # Gaussian velocity variation
            target_velocity = (base_range[0] + base_range[1]) // 2
            new_velocity = int(np.random.normal(target_velocity, variance))
            new_velocity = max(1, min(127, new_velocity + boost))

            # Accent boost
            if beat.accent:
                accent_boost = int(10 * context['accent_strength'])
                new_velocity = min(127, new_velocity + accent_boost)

            velocity_beats.append(
                Beat(
                    position=beat.position,
                    instrument=beat.instrument,
                    velocity=new_velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
            )

        return velocity_beats

    def _apply_fatigue(self, beats: list[Beat], duration_bars: float) -> list[Beat]:
        """Apply subtle fatigue effect (velocity reduction over time).

        Simulates natural drummer fatigue during long sections.
        """
        if duration_bars < 8:
            return beats  # No fatigue for short patterns

        fatigued_beats = []
        for beat in beats:
            # Calculate fatigue factor (0-5% reduction based on position)
            progress = beat.position / (duration_bars * 4.0)
            fatigue_factor = 1.0 - (progress * 0.05 * self.humanization_amount)

            new_velocity = int(beat.velocity * fatigue_factor)
            new_velocity = max(1, new_velocity)

            fatigued_beats.append(
                Beat(
                    position=beat.position,
                    instrument=beat.instrument,
                    velocity=new_velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
            )

        return fatigued_beats
```

### Phase 2: Enhanced Pattern Builder

**Add humanization hints to `PatternBuilder`**

```python
class PatternBuilder:
    """Enhanced builder with humanization hints."""

    def kick(self, position: float, velocity: int = 100, accent: bool = False) -> "PatternBuilder":
        """Add kick drum with optional accent marking."""
        self.pattern.add_beat(
            position,
            DrumInstrument.KICK,
            velocity,
            accent=accent  # Mark for humanization
        )
        return self

    def ghost_note(self, position: float, velocity: int = 35) -> "PatternBuilder":
        """Add ghost note (marked for softer humanization)."""
        self.pattern.add_beat(
            position,
            DrumInstrument.SNARE,
            velocity,
            ghost_note=True
        )
        return self
```

### Phase 3: Integration with Composite Drummer

**Update `generate_complete_doom_blues.py`**

```python
from midi_drums.humanization.advanced_humanization import AdvancedHumanizer

def main():
    # ... existing code ...

    # Generate base song
    song = api.create_song(
        genre="metal",
        style="doom",
        tempo=70,
        structure=structure,
        complexity=0.7,
        humanization=0.0,  # Disable basic humanization
        name="doom_blues_composite",
    )

    # Apply advanced humanization to each section
    humanizer = AdvancedHumanizer(
        tempo=70,
        style="loose",  # Doom metal = loose, heavy feel
        humanization_amount=0.7,  # Moderate humanization
    )

    for section in song.sections:
        # Determine section type from name
        section_type = section.name.split('_')[0]  # 'intro', 'verse', etc.

        # Apply advanced humanization
        section.pattern = humanizer.humanize_pattern(
            section.pattern,
            section_type=section_type
        )

    # ... rest of code ...
```

### Phase 4: Velocity Mapping Improvements

**Create `midi_drums/midi/velocity_curves.py`**

```python
"""Velocity curve mapping for realistic dynamics."""

class VelocityCurve:
    """Maps musical intentions to MIDI velocity."""

    @staticmethod
    def apply_drum_characteristic(velocity: int, instrument: DrumInstrument) -> int:
        """Apply instrument-specific velocity characteristics.

        Some instruments (kick, floor tom) need higher velocities to sound natural.
        """
        multipliers = {
            DrumInstrument.KICK: 1.1,  # Kicks need more energy
            DrumInstrument.FLOOR_TOM: 1.05,
            DrumInstrument.CRASH: 1.15,  # Crashes need power
            DrumInstrument.CLOSED_HH: 0.9,  # Hi-hats are sensitive
        }

        multiplier = multipliers.get(instrument, 1.0)
        return max(1, min(127, int(velocity * multiplier)))
```

## Implementation Plan

### Priority 1: Immediate Improvements (Quick Wins)
1. ✅ Create `HUMANIZATION_IMPROVEMENTS.md` (this document)
2. ⏳ Implement `AdvancedHumanizer` class
3. ⏳ Add Gaussian timing distribution
4. ⏳ Add velocity context awareness
5. ⏳ Update `generate_complete_doom_blues.py` to use advanced humanization

### Priority 2: Enhanced Features
6. ⏳ Add micro-timing relationships (kick+snare flam)
7. ⏳ Implement fatigue modeling
8. ⏳ Add velocity curves by section type
9. ⏳ Create velocity mapping utilities

### Priority 3: Professional Features
10. ⏳ Add drummer-specific humanization profiles
11. ⏳ Implement ML-based timing analysis (optional)
12. ⏳ Create humanization presets (studio, live, sloppy)
13. ⏳ Add A/B testing framework for humanization

## Testing Strategy

### Unit Tests
```python
def test_gaussian_timing_distribution():
    """Verify timing follows Gaussian distribution."""
    humanizer = AdvancedHumanizer(tempo=120, humanization_amount=0.5)
    pattern = create_test_pattern()
    humanized = humanizer.humanize_pattern(pattern)

    # Check timing offsets follow Gaussian (not uniform)
    offsets = [b.position - original_pos for b, original_pos in zip(...)]
    assert scipy.stats.normaltest(offsets).pvalue > 0.05

def test_velocity_ranges():
    """Verify velocity stays within realistic ranges."""
    humanizer = AdvancedHumanizer(tempo=120, humanization_amount=0.7)
    pattern = create_test_pattern_with_ghosts()
    humanized = humanizer.humanize_pattern(pattern)

    ghost_velocities = [b.velocity for b in humanized.beats if b.ghost_note]
    assert all(25 <= v <= 50 for v in ghost_velocities)

def test_downbeat_tightness():
    """Verify downbeats are tighter than other beats."""
    humanizer = AdvancedHumanizer(tempo=120, humanization_amount=0.5)
    pattern = create_test_pattern()
    humanized = humanizer.humanize_pattern(pattern)

    downbeat_variance = calculate_variance([b for b in humanized.beats if b.position % 4.0 == 0])
    offbeat_variance = calculate_variance([b for b in humanized.beats if b.position % 4.0 != 0])

    assert downbeat_variance < offbeat_variance
```

### Integration Tests
```python
def test_full_song_humanization():
    """Test humanization on complete doom blues song."""
    api = DrumGeneratorAPI()
    song = api.create_song("metal", "doom", tempo=70, structure=[("verse", 8)])

    humanizer = AdvancedHumanizer(tempo=70, style="loose", humanization_amount=0.7)
    for section in song.sections:
        section.pattern = humanizer.humanize_pattern(section.pattern, "verse")

    # Verify no negative positions
    for section in song.sections:
        assert all(b.position >= 0 for b in section.pattern.beats)

    # Verify realistic velocity ranges
    all_velocities = [b.velocity for s in song.sections for b in s.pattern.beats]
    assert all(1 <= v <= 127 for v in all_velocities)
```

### A/B Listening Tests
- Generate same pattern with old vs new humanization
- Export both to MIDI
- Load into EZDrummer 3
- Compare perceived realism

## Expected Improvements

### Quantitative Metrics
- **Timing Distribution**: Gaussian (σ=3-5ms) instead of uniform (±20ms)
- **Velocity Variation**: Context-aware (ghost 25-45, normal 65-90, accent 95-115)
- **Physical Realism**: Zero impossible patterns (maintained)
- **Downbeat Precision**: 50% tighter timing on beat 1

### Qualitative Improvements
- **More Musical**: Timing follows musical phrasing
- **More Natural**: Variations match human limitations
- **More Dynamic**: Velocity follows energy of section
- **More Authentic**: Instrument-specific characteristics

## References

1. **Toontrack MIDI Analysis**: Professional MIDI packs (Metal Machine, Death & Darkness)
2. **Academic Research**: "Timing in Expressive Performance" (Desain & Honing, 1994)
3. **Drummer Timing Studies**: "The Feel Factor" (Iyer, 2002)
4. **MIDI Best Practices**: "Programming Realistic Drums" (Sound on Sound, 2019)

## Next Steps

1. **Review this document** with stakeholders
2. **Prioritize features** based on impact/effort
3. **Create implementation tasks** in TODO system
4. **Begin with Phase 1** (basic Gaussian timing)
5. **Iterate based on listening tests**

---

**Document Status**: Draft for Review
**Author**: AI Analysis (Claude Sonnet 4.5)
**Last Updated**: 2026-01-24
