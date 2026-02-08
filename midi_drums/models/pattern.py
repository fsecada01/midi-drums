"""Pattern data models and core drum pattern structures."""

import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DrumInstrument(Enum):
    """Standard drum kit instruments with MIDI note mappings."""

    KICK = 36
    SNARE = 38
    RIM = 40
    CLOSED_HH = 42  # GM standard
    CLOSED_HH_EDGE = 22  # EZDrummer specific
    CLOSED_HH_TIP = 61  # EZDrummer specific
    TIGHT_HH_EDGE = 62  # EZDrummer specific
    TIGHT_HH_TIP = 63  # EZDrummer specific
    PEDAL_HH = 44
    OPEN_HH = 46  # GM standard
    OPEN_HH_1 = 24  # EZDrummer specific
    OPEN_HH_2 = 25  # EZDrummer specific
    OPEN_HH_3 = 26  # EZDrummer specific
    OPEN_HH_MAX = 60  # EZDrummer specific - fully open
    MID_TOM = 47
    FLOOR_TOM = 43
    CRASH = 49
    RIDE = 51
    RIDE_BELL = 53
    SPLASH = 55
    CHINA = 52


@dataclass
class TimeSignature:
    """Time signature representation."""

    numerator: int = 4
    denominator: int = 4

    @property
    def beats_per_bar(self) -> float:
        return self.numerator * (4.0 / self.denominator)

    def __str__(self) -> str:
        return f"{self.numerator}/{self.denominator}"


@dataclass
class Beat:
    """Individual drum hit within a pattern."""

    position: float  # Beat position (0.0-4.0 for 4/4)
    instrument: DrumInstrument
    velocity: int = 100  # MIDI velocity 0-127
    duration: float = 0.25  # Note duration in beats
    ghost_note: bool = False  # Quiet accent note
    accent: bool = False  # Emphasized note

    def __post_init__(self):
        """Validate beat parameters."""
        if not 0 <= self.velocity <= 127:
            raise ValueError(f"Velocity must be 0-127, got {self.velocity}")
        if self.position < 0:
            raise ValueError(
                f"Position cannot be negative, got {self.position}"
            )


@dataclass
class Pattern:
    """Complete drum pattern with timing and metadata."""

    name: str
    beats: list[Beat] = field(default_factory=list)
    time_signature: TimeSignature = field(default_factory=TimeSignature)
    subdivision: int = 16  # 16th note resolution
    swing_ratio: float = 0.0  # 0.0 = straight, 0.5 = triplet swing
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_beat(
        self,
        position: float,
        instrument: DrumInstrument,
        velocity: int = 100,
        **kwargs,
    ) -> "Pattern":
        """Add a beat to the pattern."""
        beat = Beat(
            position=position,
            instrument=instrument,
            velocity=velocity,
            **kwargs,
        )
        self.beats.append(beat)
        return self

    def get_beats_at_position(
        self, position: float, tolerance: float = 0.01
    ) -> list[Beat]:
        """Get all beats at a specific position."""
        return [
            beat
            for beat in self.beats
            if abs(beat.position - position) <= tolerance
        ]

    def get_beats_by_instrument(self, instrument: DrumInstrument) -> list[Beat]:
        """Get all beats for a specific instrument."""
        return [beat for beat in self.beats if beat.instrument == instrument]

    def duration_bars(self) -> float:
        """Calculate pattern duration in bars."""
        if not self.beats:
            return 1.0
        max_position = max(beat.position for beat in self.beats)
        return max(
            1.0, (max_position + 1.0) / self.time_signature.beats_per_bar
        )

    def humanize(
        self, timing_variance: float = 0.02, velocity_variance: float = 10
    ) -> "Pattern":
        """Apply humanization to timing and velocity."""
        humanized_beats = []
        for beat in self.beats:
            # Add slight timing variations
            timing_offset = random.uniform(-timing_variance, timing_variance)
            new_position = max(0, beat.position + timing_offset)

            # Add velocity variations
            velocity_offset = random.randint(
                -velocity_variance, velocity_variance
            )
            new_velocity = max(1, min(127, beat.velocity + velocity_offset))

            humanized_beat = Beat(
                position=new_position,
                instrument=beat.instrument,
                velocity=new_velocity,
                duration=beat.duration,
                ghost_note=beat.ghost_note,
                accent=beat.accent,
            )
            humanized_beats.append(humanized_beat)

        return Pattern(
            name=f"{self.name}_humanized",
            beats=humanized_beats,
            time_signature=self.time_signature,
            subdivision=self.subdivision,
            swing_ratio=self.swing_ratio,
            metadata={**self.metadata, "humanized": True},
        )

    def copy(self) -> "Pattern":
        """Create a deep copy of the pattern.

        Logs warning if pattern has no beats to aid debugging.
        """
        if not self.beats:
            logger.warning(
                f"Pattern '{self.name}' has no beats - copying empty pattern. "
                "This may cause issues with drummer plugins."
            )

        return Pattern(
            name=self.name,
            beats=[
                Beat(
                    position=beat.position,
                    instrument=beat.instrument,
                    velocity=beat.velocity,
                    duration=beat.duration,
                    ghost_note=beat.ghost_note,
                    accent=beat.accent,
                )
                for beat in self.beats
            ],
            time_signature=TimeSignature(
                self.time_signature.numerator, self.time_signature.denominator
            ),
            subdivision=self.subdivision,
            swing_ratio=self.swing_ratio,
            metadata=self.metadata.copy(),
        )


class PatternBuilder:
    """Builder pattern for creating drum patterns."""

    def __init__(self, name: str, time_signature: TimeSignature | None = None):
        self.pattern = Pattern(
            name=name, time_signature=time_signature or TimeSignature()
        )

    def kick(self, position: float, velocity: int = 100) -> "PatternBuilder":
        """Add kick drum at position."""
        self.pattern.add_beat(position, DrumInstrument.KICK, velocity)
        return self

    def snare(self, position: float, velocity: int = 100) -> "PatternBuilder":
        """Add snare at position."""
        self.pattern.add_beat(position, DrumInstrument.SNARE, velocity)
        return self

    def hihat(
        self, position: float, velocity: int = 80, open: bool = False
    ) -> "PatternBuilder":
        """Add hi-hat at position."""
        instrument = (
            DrumInstrument.OPEN_HH if open else DrumInstrument.CLOSED_HH
        )
        self.pattern.add_beat(position, instrument, velocity)
        return self

    def ride(self, position: float, velocity: int = 80) -> "PatternBuilder":
        """Add ride cymbal at position."""
        self.pattern.add_beat(position, DrumInstrument.RIDE, velocity)
        return self

    def crash(self, position: float, velocity: int = 110) -> "PatternBuilder":
        """Add crash cymbal at position."""
        self.pattern.add_beat(position, DrumInstrument.CRASH, velocity)
        return self

    def build(self) -> Pattern:
        """Build and return the pattern."""
        return self.pattern
