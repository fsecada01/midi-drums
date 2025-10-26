"""Reusable drummer style modifications.

This module provides composable modifications that represent authentic
drummer techniques and characteristics. These can be combined to create
complex drummer personalities without code duplication.

Each modification represents a specific drumming technique or characteristic:
- Timing variations (behind-beat, shuffle, etc.)
- Rhythmic vocabulary (triplets, linear, etc.)
- Dynamics and accents
- Genre-specific techniques
"""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from midi_drums.config import TIMING, VELOCITY
from midi_drums.models.pattern import Beat, DrumInstrument, Pattern


class DrummerModification(ABC):
    """Base class for drummer style modifications.

    All modifications implement the apply() method which receives a pattern
    and returns a modified version (immutable - returns new pattern).
    """

    @abstractmethod
    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Apply modification to pattern.

        Args:
            pattern: Input pattern to modify
            intensity: Modification strength (0.0-1.0)

        Returns:
            Modified pattern (new instance, original unchanged)
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Modification name for logging and identification."""
        pass


@dataclass
class BehindBeatTiming(DrummerModification):
    """Apply behind-the-beat timing (Bonham, Chambers style).

    Shifts snare hits slightly behind the beat for a laid-back feel.
    This creates the characteristic "dragging" sound that makes grooves
    feel powerful and heavy.

    Example:
        BehindBeatTiming(max_delay_ms=25.0).apply(pattern, intensity=0.8)
    """

    max_delay_ms: float = 20.0  # Maximum delay in milliseconds

    @property
    def name(self) -> str:
        return "behind_beat_timing"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Shift snare hits slightly behind the beat."""
        modified_beats = []

        # Calculate delay in beats (tempo-independent)
        # Assuming 120 BPM as baseline: delay_beats = (ms / 1000) * (BPM / 60)
        # For 20ms at 120 BPM: 0.04 beats
        delay = (self.max_delay_ms / 1000.0) * 2.0 * intensity

        for beat in pattern.beats:
            if beat.instrument == DrumInstrument.SNARE and not beat.ghost_note:
                # Shift snare behind the beat
                new_beat = Beat(
                    position=beat.position + delay,
                    instrument=beat.instrument,
                    velocity=beat.velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
                modified_beats.append(new_beat)
            else:
                modified_beats.append(beat)

        return Pattern(
            name=f"{pattern.name}_behind_beat",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )


@dataclass
class TripletVocabulary(DrummerModification):
    """Add triplet-based fills and embellishments (Bonham style).

    Adds characteristic triplet patterns during transitions and fills.
    This creates the "rolling" feel associated with rock drummers.

    Example:
        TripletVocabulary(triplet_probability=0.4).apply(pattern, intensity=0.9)
    """

    triplet_probability: float = 0.3

    @property
    def name(self) -> str:
        return "triplet_vocabulary"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Add triplet-based rhythmic vocabulary."""
        modified_beats = list(pattern.beats)

        # Look for opportunities to add triplets (beat 4 of each bar)
        duration = pattern.duration_bars()
        for bar in range(int(duration)):
            bar_start = bar * 4.0

            # Probabilistically add triplet fill on beat 4
            if random.random() < (self.triplet_probability * intensity):
                # Add descending triplet fill starting at beat 3.5
                fill_start = bar_start + 3.5

                # Remove any existing beats in this space
                modified_beats = [
                    b
                    for b in modified_beats
                    if not (fill_start <= b.position < bar_start + 4.0)
                ]

                # Add triplet fill (6 notes = 2 triplets)
                instruments = [
                    DrumInstrument.MID_TOM,
                    DrumInstrument.MID_TOM,
                    DrumInstrument.FLOOR_TOM,
                    DrumInstrument.FLOOR_TOM,
                    DrumInstrument.FLOOR_TOM,
                    DrumInstrument.KICK,
                ]

                for i in range(6):
                    pos = fill_start + (i * TIMING.SIXTEENTH_TRIPLET)
                    modified_beats.append(
                        Beat(
                            position=pos,
                            instrument=instruments[i],
                            velocity=VELOCITY.TOM_HEAVY,
                            duration=TIMING.SIXTEENTH_TRIPLET,
                            ghost_note=False,
                            accent=i % 3 == 0,  # Accent every 3rd
                        )
                    )

        # Sort by position
        modified_beats.sort(key=lambda b: b.position)

        return Pattern(
            name=f"{pattern.name}_triplets",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )


@dataclass
class GhostNoteLayer(DrummerModification):
    """Add ghost notes on snare (Porcaro, Chambers style).

    Adds subtle ghost notes between main snare hits for texture and groove.
    Essential for funk, R&B, and sophisticated rock drumming.

    Example:
        GhostNoteLayer(density=0.6).apply(pattern, intensity=0.8)
    """

    density: float = 0.6  # How many 16ths get ghost notes

    @property
    def name(self) -> str:
        return "ghost_note_layer"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Add subtle ghost notes between main snare hits."""
        modified_beats = list(pattern.beats)

        # Find main snare hit positions
        main_snare_positions = {
            b.position
            for b in pattern.beats
            if b.instrument == DrumInstrument.SNARE and not b.ghost_note
        }

        # Add ghost notes on 16ths that don't have main snares
        duration = pattern.duration_bars()
        for bar in range(int(duration)):
            bar_start = bar * 4.0

            for i in range(16):
                pos = bar_start + (i * TIMING.SIXTEENTH)

                # Skip if main snare already exists
                if pos in main_snare_positions:
                    continue

                # Probabilistically add ghost note
                if random.random() < (self.density * intensity):
                    modified_beats.append(
                        Beat(
                            position=pos,
                            instrument=DrumInstrument.SNARE,
                            velocity=VELOCITY.SNARE_GHOST,
                            duration=TIMING.SIXTEENTH,
                            ghost_note=True,
                            accent=False,
                        )
                    )

        # Sort by position
        modified_beats.sort(key=lambda b: b.position)

        return Pattern(
            name=f"{pattern.name}_ghost_notes",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )


@dataclass
class LinearCoordination(DrummerModification):
    """Apply linear playing style (Weckl style - no simultaneous limbs).

    Removes overlapping hits to create linear patterns where only one
    sound happens at a time. This creates a sophisticated, flowing feel.

    Example:
        LinearCoordination().apply(pattern, intensity=1.0)
    """

    @property
    def name(self) -> str:
        return "linear_coordination"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Remove overlapping hits to create linear patterns."""
        from collections import defaultdict

        # Group beats by position (quantize to 32nd notes)
        position_groups = defaultdict(list)
        for beat in pattern.beats:
            quantized_pos = round(beat.position * 8) / 8  # 32nd note resolution
            position_groups[quantized_pos].append(beat)

        modified_beats = []

        # Priority system for linear playing
        priority = {
            DrumInstrument.SNARE: 5,
            DrumInstrument.KICK: 4,
            DrumInstrument.CRASH: 3,
            DrumInstrument.RIDE: 3,
            DrumInstrument.MID_TOM: 2,
            DrumInstrument.FLOOR_TOM: 2,
            DrumInstrument.CLOSED_HH: 1,
        }

        for pos in sorted(position_groups.keys()):
            beats = position_groups[pos]

            if len(beats) == 1:
                # Single hit - keep it
                modified_beats.append(beats[0])
            else:
                # Multiple hits - apply linear logic based on intensity
                if random.random() < intensity:
                    # Keep only highest priority hit
                    kept_beat = max(
                        beats, key=lambda b: priority.get(b.instrument, 0)
                    )
                    modified_beats.append(kept_beat)
                else:
                    # Keep all hits (less linear)
                    modified_beats.extend(beats)

        return Pattern(
            name=f"{pattern.name}_linear",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )


@dataclass
class HeavyAccents(DrummerModification):
    """Apply heavy accenting and dynamics (metal drummers).

    Increases the contrast between accented and non-accented hits
    for a more powerful, aggressive sound.

    Example:
        HeavyAccents(accent_boost=20).apply(pattern, intensity=0.8)
    """

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
                new_velocity = min(
                    127, beat.velocity + int(self.accent_boost * intensity)
                )
            elif beat.ghost_note:
                # Reduce ghost notes for more contrast
                new_velocity = max(20, beat.velocity - int(10 * intensity))

            modified_beats.append(
                Beat(
                    position=beat.position,
                    instrument=beat.instrument,
                    velocity=new_velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
            )

        return Pattern(
            name=f"{pattern.name}_heavy_accents",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )


@dataclass
class ShuffleFeelApplication(DrummerModification):
    """Apply shuffle feel (Porcaro's half-time shuffle).

    Converts straight 16ths to shuffle feel with triplet-based swing.

    Example:
        ShuffleFeelApplication(shuffle_amount=0.33).apply(pattern, 0.8)
    """

    shuffle_amount: float = 0.33  # 0.33 = triplet feel

    @property
    def name(self) -> str:
        return "shuffle_feel"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Apply shuffle/swing feel to straight notes."""
        modified_beats = []

        for beat in pattern.beats:
            # Apply shuffle to off-beat 16ths (positions x.25, x.75, etc.)
            beat_within_quarter = beat.position % 1.0
            is_offbeat_16th = (
                abs(beat_within_quarter - 0.25) < 0.01
                or abs(beat_within_quarter - 0.75) < 0.01
            )

            if is_offbeat_16th:
                # Push offbeat notes later (shuffle feel)
                swing_amount = self.shuffle_amount * 0.25 * intensity
                new_position = beat.position + swing_amount

                modified_beats.append(
                    Beat(
                        position=new_position,
                        instrument=beat.instrument,
                        velocity=beat.velocity,
                        duration=beat.duration,
                        ghost_note=beat.ghost_note,
                        accent=beat.accent,
                    )
                )
            else:
                modified_beats.append(beat)

        return Pattern(
            name=f"{pattern.name}_shuffle",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=max(pattern.swing_ratio, self.shuffle_amount),
            metadata={**pattern.metadata, "modification": self.name},
        )


@dataclass
class FastChopsTriplets(DrummerModification):
    """Add fast triplet chops (Chambers style).

    Adds rapid triplet-based fills and embellishments for technical display.

    Example:
        FastChopsTriplets(probability=0.3).apply(pattern, 0.9)
    """

    probability: float = 0.25

    @property
    def name(self) -> str:
        return "fast_chops_triplets"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Add fast triplet-based technical fills."""
        modified_beats = list(pattern.beats)

        duration = pattern.duration_bars()
        for bar in range(int(duration)):
            bar_start = bar * 4.0

            # Add fast chops on beat 3 occasionally
            if random.random() < (self.probability * intensity):
                chop_start = bar_start + 2.5

                # Fast triplet snare roll
                for i in range(6):
                    pos = chop_start + (i * TIMING.SIXTEENTH_TRIPLET)
                    velocity = (
                        VELOCITY.SNARE_HEAVY
                        if i % 2 == 0
                        else VELOCITY.SNARE_NORMAL
                    )

                    modified_beats.append(
                        Beat(
                            position=pos,
                            instrument=DrumInstrument.SNARE,
                            velocity=velocity,
                            duration=TIMING.SIXTEENTH_TRIPLET,
                            ghost_note=False,
                            accent=i == 0,
                        )
                    )

        modified_beats.sort(key=lambda b: b.position)

        return Pattern(
            name=f"{pattern.name}_fast_chops",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )


@dataclass
class PocketStretching(DrummerModification):
    """Apply pocket stretching (Chambers funk mastery).

    Subtle timing variations that create groove tension and release.

    Example:
        PocketStretching(variation_ms=5.0).apply(pattern, 0.7)
    """

    variation_ms: float = 5.0

    @property
    def name(self) -> str:
        return "pocket_stretching"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Apply subtle pocket variations for groove."""
        modified_beats = []

        variation = (self.variation_ms / 1000.0) * 2.0 * intensity

        for beat in pattern.beats:
            # Apply random pocket variation to hi-hats and ghost notes
            if beat.instrument == DrumInstrument.CLOSED_HH or beat.ghost_note:
                offset = random.uniform(-variation, variation)
                new_position = max(
                    0.0, beat.position + offset
                )  # Clamp to non-negative

                modified_beats.append(
                    Beat(
                        position=new_position,
                        instrument=beat.instrument,
                        velocity=beat.velocity,
                        duration=beat.duration,
                        ghost_note=beat.ghost_note,
                        accent=beat.accent,
                    )
                )
            else:
                modified_beats.append(beat)

        return Pattern(
            name=f"{pattern.name}_pocket",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )


@dataclass
class MinimalCreativity(DrummerModification):
    """Apply minimal, sparse approach (Roeder sludge style).

    Removes non-essential hits for atmospheric, minimal feel.

    Example:
        MinimalCreativity(sparseness=0.7).apply(pattern, 0.8)
    """

    sparseness: float = 0.6  # Higher = more sparse

    @property
    def name(self) -> str:
        return "minimal_creativity"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Remove non-essential hits for minimal feel."""
        modified_beats = []

        # Keep kick and snare, thin out cymbals
        for beat in pattern.beats:
            is_cymbal = beat.instrument in [
                DrumInstrument.CLOSED_HH,
                DrumInstrument.OPEN_HH,
                DrumInstrument.RIDE,
            ]

            if is_cymbal:
                # Probabilistically remove cymbal hits
                if random.random() > (self.sparseness * intensity):
                    modified_beats.append(beat)
            else:
                # Keep drums
                modified_beats.append(beat)

        return Pattern(
            name=f"{pattern.name}_minimal",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )


@dataclass
class SpeedPrecision(DrummerModification):
    """Apply speed and precision (Dee style).

    Ensures consistent velocities and tight timing for precision feel.

    Example:
        SpeedPrecision(consistency=0.9).apply(pattern, 1.0)
    """

    consistency: float = 0.9  # 0-1, higher = more consistent

    @property
    def name(self) -> str:
        return "speed_precision"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Apply mechanical precision to timing and velocities."""
        modified_beats = []

        for beat in pattern.beats:
            # Reduce velocity variation
            target_velocity = {
                DrumInstrument.KICK: VELOCITY.KICK_HEAVY,
                DrumInstrument.SNARE: VELOCITY.SNARE_HEAVY,
                DrumInstrument.CLOSED_HH: VELOCITY.HIHAT_NORMAL,
            }.get(beat.instrument, beat.velocity)

            # Blend current velocity with target
            blend = self.consistency * intensity
            new_velocity = int(
                beat.velocity * (1 - blend) + target_velocity * blend
            )

            modified_beats.append(
                Beat(
                    position=beat.position,  # Keep timing precise
                    instrument=beat.instrument,
                    velocity=new_velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
            )

        return Pattern(
            name=f"{pattern.name}_precision",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )


@dataclass
class TwistedAccents(DrummerModification):
    """Apply twisted/displaced accents (Dee style).

    Moves accents to unexpected positions for interest.

    Example:
        TwistedAccents(displacement=0.5).apply(pattern, 0.8)
    """

    displacement: float = 0.5  # Probability of displacing accent

    @property
    def name(self) -> str:
        return "twisted_accents"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Displace accents to unexpected positions."""
        modified_beats = []

        for _i, beat in enumerate(pattern.beats):
            new_accent = beat.accent

            # Probabilistically move accents
            if beat.accent and random.random() < (
                self.displacement * intensity
            ):
                # Remove this accent
                new_accent = False

            # Add accent to unexpected beat
            if (
                not beat.accent
                and beat.instrument == DrumInstrument.SNARE
                and random.random() < (self.displacement * intensity * 0.3)
            ):
                new_accent = True

            modified_beats.append(
                Beat(
                    position=beat.position,
                    instrument=beat.instrument,
                    velocity=beat.velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=new_accent,
                )
            )

        return Pattern(
            name=f"{pattern.name}_twisted",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )


@dataclass
class MechanicalPrecision(DrummerModification):
    """Apply mechanical precision (Hoglan style).

    Extremely consistent timing and velocities for machine-like feel.

    Example:
        MechanicalPrecision(quantize_amount=0.95).apply(pattern, 1.0)
    """

    quantize_amount: float = 0.95  # 0-1, higher = more quantized

    @property
    def name(self) -> str:
        return "mechanical_precision"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Apply extreme quantization and consistency."""
        modified_beats = []

        for beat in pattern.beats:
            # Quantize position to grid
            grid = TIMING.THIRTY_SECOND  # 32nd note grid
            quantized_pos = round(beat.position / grid) * grid

            # Blend original and quantized
            blend = self.quantize_amount * intensity
            new_position = beat.position * (1 - blend) + quantized_pos * blend

            # Normalize velocities
            velocity_target = {
                DrumInstrument.KICK: VELOCITY.KICK_HEAVY,
                DrumInstrument.SNARE: VELOCITY.SNARE_HEAVY,
            }.get(beat.instrument, beat.velocity)

            new_velocity = int(
                beat.velocity * (1 - blend * 0.5)
                + velocity_target * blend * 0.5
            )

            modified_beats.append(
                Beat(
                    position=new_position,
                    instrument=beat.instrument,
                    velocity=new_velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
            )

        return Pattern(
            name=f"{pattern.name}_mechanical",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )


class ModificationRegistry:
    """Registry of available drummer modifications.

    Provides centralized access to all modification types.
    """

    def __init__(self):
        self._modifications: dict[str, type[DrummerModification]] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register all standard modifications."""
        self.register(BehindBeatTiming)
        self.register(TripletVocabulary)
        self.register(GhostNoteLayer)
        self.register(LinearCoordination)
        self.register(HeavyAccents)
        self.register(ShuffleFeelApplication)
        self.register(FastChopsTriplets)
        self.register(PocketStretching)
        self.register(MinimalCreativity)
        self.register(SpeedPrecision)
        self.register(TwistedAccents)
        self.register(MechanicalPrecision)

    def register(self, mod_class: type[DrummerModification]):
        """Register a modification class.

        Args:
            mod_class: DrummerModification subclass to register
        """
        # Create temporary instance to get name
        instance = mod_class()
        self._modifications[instance.name] = mod_class

    def get(self, name: str) -> type[DrummerModification] | None:
        """Get modification class by name.

        Args:
            name: Modification name

        Returns:
            DrummerModification class or None if not found
        """
        return self._modifications.get(name)

    def list_modifications(self) -> list[str]:
        """List all registered modification names.

        Returns:
            List of modification names
        """
        return list(self._modifications.keys())

    def create(self, name: str, **kwargs) -> DrummerModification | None:
        """Create modification instance by name.

        Args:
            name: Modification name
            **kwargs: Parameters for modification constructor

        Returns:
            DrummerModification instance or None if not found
        """
        mod_class = self.get(name)
        if mod_class:
            return mod_class(**kwargs)
        return None


# Global registry instance
MODIFICATION_REGISTRY = ModificationRegistry()
