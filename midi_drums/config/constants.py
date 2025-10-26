"""Centralized constants for MIDI Drums Generator.

This module eliminates magic numbers throughout the codebase by providing
named constants for velocities, timing, and generation defaults.

Usage:
    from midi_drums.config.constants import VELOCITY, TIMING, DEFAULTS

    builder.kick(TIMING.QUARTER * 0, VELOCITY.KICK_NORMAL)
    builder.snare(TIMING.QUARTER * 1, VELOCITY.SNARE_HEAVY)
"""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class VelocityRanges:
    """MIDI velocity ranges for different dynamics.

    All values are in MIDI velocity units (0-127).

    Usage guidelines:
    - WHISPER/GHOST: Very quiet, barely audible (20-50)
    - LIGHT: Soft playing (60-85)
    - NORMAL: Standard playing dynamics (90-110)
    - HEAVY: Loud, powerful hits (115-120)
    - ACCENT: Maximum emphasis (125-127)
    """

    # Kick drum velocities
    KICK_WHISPER: Final[int] = 60
    KICK_LIGHT: Final[int] = 95
    KICK_NORMAL: Final[int] = 110
    KICK_HEAVY: Final[int] = 120
    KICK_ACCENT: Final[int] = 127

    # Snare drum velocities
    SNARE_GHOST: Final[int] = 40
    SNARE_LIGHT: Final[int] = 90
    SNARE_NORMAL: Final[int] = 115
    SNARE_HEAVY: Final[int] = 127
    SNARE_RIMSHOT: Final[int] = 125
    SNARE_ACCENT: Final[int] = 127

    # Hi-hat velocities
    HIHAT_WHISPER: Final[int] = 40
    HIHAT_LIGHT: Final[int] = 60
    HIHAT_NORMAL: Final[int] = 80
    HIHAT_ACCENT: Final[int] = 100
    HIHAT_OPEN: Final[int] = 100
    HIHAT_PEDAL: Final[int] = 70

    # Cymbal velocities
    RIDE_WHISPER: Final[int] = 50
    RIDE_LIGHT: Final[int] = 70
    RIDE_NORMAL: Final[int] = 90
    RIDE_ACCENT: Final[int] = 105
    RIDE_BELL: Final[int] = 100
    RIDE_BELL_ACCENT: Final[int] = 110

    CRASH_LIGHT: Final[int] = 100
    CRASH_NORMAL: Final[int] = 110
    CRASH_ACCENT: Final[int] = 120
    CRASH_HEAVY: Final[int] = 127

    CHINA_NORMAL: Final[int] = 105
    CHINA_ACCENT: Final[int] = 115

    SPLASH_LIGHT: Final[int] = 85
    SPLASH_NORMAL: Final[int] = 95
    SPLASH_ACCENT: Final[int] = 105

    # Tom velocities
    TOM_WHISPER: Final[int] = 70
    TOM_LIGHT: Final[int] = 85
    TOM_NORMAL: Final[int] = 100
    TOM_HEAVY: Final[int] = 115
    TOM_ACCENT: Final[int] = 125

    # Rim shots and special techniques
    RIM_NORMAL: Final[int] = 90
    RIM_ACCENT: Final[int] = 105


@dataclass(frozen=True)
class TimingConstants:
    """Beat position constants for rhythmic notation.

    All values are in beats (quarter notes) for 4/4 time signature.
    Position 0.0 = downbeat, 4.0 = next bar.

    Usage:
        # Quarter notes on beats 1, 2, 3, 4
        positions = [0.0, 1.0, 2.0, 3.0]
        # Or using constants
        positions = [TIMING.QUARTER * i for i in range(4)]

        # Eighth note pattern
        for i in range(8):
            pos = i * TIMING.EIGHTH
    """

    # Standard note values (in quarter note beats)
    WHOLE: Final[float] = 4.0
    HALF: Final[float] = 2.0
    QUARTER: Final[float] = 1.0
    EIGHTH: Final[float] = 0.5
    SIXTEENTH: Final[float] = 0.25
    THIRTY_SECOND: Final[float] = 0.125
    SIXTY_FOURTH: Final[float] = 0.0625

    # Triplet subdivisions
    HALF_TRIPLET: Final[float] = 4.0 / 3.0  # ~1.333
    QUARTER_TRIPLET: Final[float] = 2.0 / 3.0  # ~0.667
    EIGHTH_TRIPLET: Final[float] = 1.0 / 3.0  # ~0.333
    SIXTEENTH_TRIPLET: Final[float] = 1.0 / 6.0  # ~0.167

    # Dotted notes
    DOTTED_WHOLE: Final[float] = 6.0
    DOTTED_HALF: Final[float] = 3.0
    DOTTED_QUARTER: Final[float] = 1.5
    DOTTED_EIGHTH: Final[float] = 0.75
    DOTTED_SIXTEENTH: Final[float] = 0.375

    # Quintuplet subdivisions (5 notes per beat)
    QUARTER_QUINTUPLET: Final[float] = 4.0 / 5.0  # 0.8
    EIGHTH_QUINTUPLET: Final[float] = 2.0 / 5.0  # 0.4
    SIXTEENTH_QUINTUPLET: Final[float] = 1.0 / 5.0  # 0.2

    # Septuplet subdivisions (7 notes per beat)
    EIGHTH_SEPTUPLET: Final[float] = 2.0 / 7.0  # ~0.286
    SIXTEENTH_SEPTUPLET: Final[float] = 1.0 / 7.0  # ~0.143

    # Humanization defaults
    HUMANIZATION_TIMING_VAR_MIN: Final[float] = 0.01
    HUMANIZATION_TIMING_VAR_DEFAULT: Final[float] = 0.02
    HUMANIZATION_TIMING_VAR_MAX: Final[float] = 0.1

    HUMANIZATION_VELOCITY_VAR_MIN: Final[int] = 5
    HUMANIZATION_VELOCITY_VAR_DEFAULT: Final[int] = 10
    HUMANIZATION_VELOCITY_VAR_MAX: Final[int] = 20


@dataclass(frozen=True)
class GenerationDefaults:
    """Default parameters for pattern and song generation.

    These values are used when parameters are not explicitly provided
    by the user or API calls.
    """

    # Tempo constraints (BPM)
    TEMPO_MIN: Final[int] = 60
    TEMPO_MAX: Final[int] = 300
    TEMPO_DEFAULT: Final[int] = 120

    # Common tempo ranges
    TEMPO_SLOW: Final[int] = 80  # Ballads, doom metal
    TEMPO_MEDIUM: Final[int] = 120  # Rock, pop
    TEMPO_FAST: Final[int] = 160  # Punk, thrash
    TEMPO_VERY_FAST: Final[int] = 200  # Death metal, grindcore

    # Complexity (0.0 - 1.0)
    COMPLEXITY_MIN: Final[float] = 0.0
    COMPLEXITY_MAX: Final[float] = 1.0
    COMPLEXITY_DEFAULT: Final[float] = 0.5
    COMPLEXITY_SIMPLE: Final[float] = 0.3
    COMPLEXITY_MODERATE: Final[float] = 0.5
    COMPLEXITY_COMPLEX: Final[float] = 0.7
    COMPLEXITY_VERY_COMPLEX: Final[float] = 0.9

    # Dynamics (0.0 - 1.0)
    DYNAMICS_MIN: Final[float] = 0.0
    DYNAMICS_MAX: Final[float] = 1.0
    DYNAMICS_DEFAULT: Final[float] = 0.5

    # Humanization (0.0 - 1.0)
    HUMANIZATION_MIN: Final[float] = 0.0
    HUMANIZATION_MAX: Final[float] = 1.0
    HUMANIZATION_DEFAULT: Final[float] = 0.3
    HUMANIZATION_ROBOTIC: Final[float] = 0.0
    HUMANIZATION_SUBTLE: Final[float] = 0.3
    HUMANIZATION_NOTICEABLE: Final[float] = 0.5
    HUMANIZATION_SLOPPY: Final[float] = 0.8

    # Fill frequency (0.0 - 1.0)
    FILL_FREQUENCY_MIN: Final[float] = 0.0
    FILL_FREQUENCY_MAX: Final[float] = 1.0
    FILL_FREQUENCY_DEFAULT: Final[float] = 0.2
    FILL_FREQUENCY_RARE: Final[float] = 0.1
    FILL_FREQUENCY_OCCASIONAL: Final[float] = 0.2
    FILL_FREQUENCY_FREQUENT: Final[float] = 0.4
    FILL_FREQUENCY_CONSTANT: Final[float] = 0.8

    # Swing ratio (0.0 - 1.0, where 0.5 = triplet swing)
    SWING_RATIO_MIN: Final[float] = 0.0
    SWING_RATIO_MAX: Final[float] = 1.0
    SWING_RATIO_STRAIGHT: Final[float] = 0.0
    SWING_RATIO_LIGHT: Final[float] = 0.2
    SWING_RATIO_TRIPLET: Final[float] = 0.33
    SWING_RATIO_HEAVY: Final[float] = 0.5

    # Bar constraints
    BARS_MIN: Final[int] = 1
    BARS_MAX: Final[int] = 256
    BARS_DEFAULT: Final[int] = 4

    # Common bar counts
    BARS_INTRO: Final[int] = 4
    BARS_VERSE: Final[int] = 8
    BARS_CHORUS: Final[int] = 8
    BARS_BRIDGE: Final[int] = 4
    BARS_BREAKDOWN: Final[int] = 4
    BARS_OUTRO: Final[int] = 4
    BARS_SOLO: Final[int] = 16

    # Pattern subdivision (notes per quarter note)
    SUBDIVISION_DEFAULT: Final[int] = 16  # 16th note resolution
    SUBDIVISION_EIGHTH: Final[int] = 8
    SUBDIVISION_SIXTEENTH: Final[int] = 16
    SUBDIVISION_THIRTY_SECOND: Final[int] = 32

    # MIDI constraints
    MIDI_VELOCITY_MIN: Final[int] = 0
    MIDI_VELOCITY_MAX: Final[int] = 127
    MIDI_CHANNEL_DRUMS: Final[int] = (
        9  # GM drums (0-indexed channel 9 = channel 10)
    )

    # Beat duration defaults (in quarter notes)
    BEAT_DURATION_MIN: Final[float] = 0.05
    BEAT_DURATION_DEFAULT: Final[float] = 0.2
    BEAT_DURATION_NORMAL: Final[float] = 0.25


# Singleton instances for easy import
VELOCITY = VelocityRanges()
TIMING = TimingConstants()
DEFAULTS = GenerationDefaults()


# Convenience velocity ranges for common use cases
class VelocityPresets:
    """Common velocity ranges for different playing styles."""

    # Metal genres - higher velocities overall
    METAL_KICK = (VELOCITY.KICK_HEAVY, VELOCITY.KICK_ACCENT)
    METAL_SNARE = (VELOCITY.SNARE_HEAVY, VELOCITY.SNARE_ACCENT)
    METAL_HIHAT = (VELOCITY.HIHAT_NORMAL, VELOCITY.HIHAT_ACCENT)
    METAL_CRASH = (VELOCITY.CRASH_NORMAL, VELOCITY.CRASH_HEAVY)

    # Jazz - more dynamic range, lower overall
    JAZZ_RIDE = (VELOCITY.RIDE_LIGHT, VELOCITY.RIDE_NORMAL)
    JAZZ_KICK = (VELOCITY.KICK_WHISPER, VELOCITY.KICK_LIGHT)
    JAZZ_SNARE = (VELOCITY.SNARE_GHOST, VELOCITY.SNARE_LIGHT)
    JAZZ_HIHAT = (VELOCITY.HIHAT_WHISPER, VELOCITY.HIHAT_LIGHT)

    # Rock - moderate, balanced
    ROCK_KICK = (VELOCITY.KICK_NORMAL, VELOCITY.KICK_HEAVY)
    ROCK_SNARE = (VELOCITY.SNARE_NORMAL, VELOCITY.SNARE_HEAVY)
    ROCK_HIHAT = (VELOCITY.HIHAT_NORMAL, VELOCITY.HIHAT_ACCENT)
    ROCK_CRASH = (VELOCITY.CRASH_NORMAL, VELOCITY.CRASH_ACCENT)

    # Funk - emphasis on ghost notes
    FUNK_KICK = (VELOCITY.KICK_NORMAL, VELOCITY.KICK_HEAVY)
    FUNK_SNARE_MAIN = (VELOCITY.SNARE_NORMAL, VELOCITY.SNARE_HEAVY)
    FUNK_SNARE_GHOST = (VELOCITY.SNARE_GHOST, VELOCITY.SNARE_LIGHT)
    FUNK_HIHAT = (VELOCITY.HIHAT_LIGHT, VELOCITY.HIHAT_NORMAL)


# Export all constants
__all__ = [
    # Classes
    "VelocityRanges",
    "TimingConstants",
    "GenerationDefaults",
    "VelocityPresets",
    # Singleton instances
    "VELOCITY",
    "TIMING",
    "DEFAULTS",
]
