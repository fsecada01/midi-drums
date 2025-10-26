"""Configuration module for MIDI Drums Generator.

This module provides centralized constants and configuration values used
throughout the system, eliminating magic numbers and improving maintainability.

Quick Start:
    from midi_drums.config import VELOCITY, TIMING, DEFAULTS

    # Use velocity constants
    builder.kick(0.0, VELOCITY.KICK_NORMAL)
    builder.snare(1.0, VELOCITY.SNARE_HEAVY)

    # Use timing constants
    for i in range(8):
        builder.hihat(i * TIMING.EIGHTH, VELOCITY.HIHAT_NORMAL)

    # Use generation defaults
    if complexity is None:
        complexity = DEFAULTS.COMPLEXITY_DEFAULT
"""

from midi_drums.config.constants import (
    DEFAULTS,
    TIMING,
    VELOCITY,
    GenerationDefaults,
    TimingConstants,
    VelocityPresets,
    VelocityRanges,
)

__all__ = [
    # Singleton instances (most commonly used)
    "VELOCITY",
    "TIMING",
    "DEFAULTS",
    # Classes (for type hints and advanced usage)
    "VelocityRanges",
    "TimingConstants",
    "GenerationDefaults",
    "VelocityPresets",
]
