"""Drum kit configuration and instrument mapping."""

from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional
from .pattern import DrumInstrument


@dataclass
class VelocityRange:
    """Velocity range for realistic drum dynamics."""
    min_velocity: int = 1
    max_velocity: int = 127
    default_velocity: int = 100

    def __post_init__(self):
        """Validate velocity values."""
        for vel in [self.min_velocity, self.max_velocity, self.default_velocity]:
            if not 1 <= vel <= 127:
                raise ValueError(f"Velocity must be 1-127, got {vel}")
        if self.min_velocity > self.max_velocity:
            raise ValueError("Min velocity cannot be greater than max velocity")


@dataclass
class DrumKit:
    """Drum kit configuration with instrument mappings and velocity ranges."""
    name: str = "Standard Kit"
    channel: int = 9  # MIDI channel 10 (0-indexed)

    # Velocity ranges for different instrument types
    velocity_ranges: Dict[str, VelocityRange] = field(default_factory=lambda: {
        'kick': VelocityRange(95, 120, 110),
        'snare': VelocityRange(90, 127, 115),
        'hihat': VelocityRange(60, 100, 80),
        'toms': VelocityRange(85, 115, 100),
        'cymbals': VelocityRange(70, 120, 95),
        'ride': VelocityRange(65, 100, 80)
    })

    # Custom instrument mappings (overrides default DrumInstrument values)
    custom_mappings: Dict[DrumInstrument, int] = field(default_factory=dict)

    def get_midi_note(self, instrument: DrumInstrument) -> int:
        """Get MIDI note number for an instrument."""
        return self.custom_mappings.get(instrument, instrument.value)

    def get_velocity_range(self, instrument: DrumInstrument) -> VelocityRange:
        """Get velocity range for an instrument category."""
        # Map instruments to velocity categories
        category_map = {
            DrumInstrument.KICK: 'kick',
            DrumInstrument.SNARE: 'snare',
            DrumInstrument.RIM: 'snare',
            DrumInstrument.CLOSED_HH: 'hihat',
            DrumInstrument.PEDAL_HH: 'hihat',
            DrumInstrument.OPEN_HH: 'hihat',
            DrumInstrument.MID_TOM: 'toms',
            DrumInstrument.FLOOR_TOM: 'toms',
            DrumInstrument.CRASH: 'cymbals',
            DrumInstrument.SPLASH: 'cymbals',
            DrumInstrument.CHINA: 'cymbals',
            DrumInstrument.RIDE: 'ride',
            DrumInstrument.RIDE_BELL: 'ride',
        }

        category = category_map.get(instrument, 'toms')
        return self.velocity_ranges.get(category, VelocityRange())

    def randomize_velocity(self, instrument: DrumInstrument) -> int:
        """Get a randomized velocity within the instrument's range."""
        import random
        velocity_range = self.get_velocity_range(instrument)
        return random.randint(velocity_range.min_velocity, velocity_range.max_velocity)

    @classmethod
    def create_ezdrummer3_kit(cls) -> 'DrumKit':
        """Create an EZDrummer 3 compatible kit configuration."""
        return cls(
            name="EZDrummer 3 Kit",
            channel=9,
            # EZDrummer 3 uses standard GM mappings, so no custom mappings needed
            custom_mappings={}
        )

    @classmethod
    def create_metal_kit(cls) -> 'DrumKit':
        """Create a metal-optimized kit configuration."""
        return cls(
            name="Metal Kit",
            channel=9,
            velocity_ranges={
                'kick': VelocityRange(100, 127, 120),  # Powerful kicks
                'snare': VelocityRange(110, 127, 120), # Loud snares
                'hihat': VelocityRange(40, 90, 65),    # Quieter hihats
                'toms': VelocityRange(90, 120, 105),   # Punchy toms
                'cymbals': VelocityRange(90, 127, 110), # Loud crashes
                'ride': VelocityRange(60, 100, 80)     # Controlled ride
            }
        )

    @classmethod
    def create_jazz_kit(cls) -> 'DrumKit':
        """Create a jazz-optimized kit configuration."""
        return cls(
            name="Jazz Kit",
            channel=9,
            velocity_ranges={
                'kick': VelocityRange(70, 100, 85),    # Softer kicks
                'snare': VelocityRange(60, 110, 85),   # Dynamic snares
                'hihat': VelocityRange(40, 85, 65),    # Subtle hihats
                'toms': VelocityRange(60, 105, 80),    # Warm toms
                'cymbals': VelocityRange(50, 100, 75), # Controlled crashes
                'ride': VelocityRange(45, 90, 70)      # Prominent ride
            }
        )