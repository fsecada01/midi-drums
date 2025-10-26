"""Drummer modification system for composable style application.

This module provides reusable drummer modifications that can be composed
to create authentic drummer styles without code duplication.

Usage:
    from midi_drums.modifications import BehindBeatTiming, TripletVocabulary

    # Apply modifications to a pattern
    pattern = base_pattern
    pattern = BehindBeatTiming(max_delay_ms=25.0).apply(pattern, intensity=0.8)
    pattern = TripletVocabulary().apply(pattern, intensity=0.9)
"""

from midi_drums.modifications.drummer_mods import (
    BehindBeatTiming,
    DrummerModification,
    FastChopsTriplets,
    GhostNoteLayer,
    HeavyAccents,
    LinearCoordination,
    MechanicalPrecision,
    MinimalCreativity,
    ModificationRegistry,
    PocketStretching,
    ShuffleFeelApplication,
    SpeedPrecision,
    TripletVocabulary,
    TwistedAccents,
)

__all__ = [
    # Base class
    "DrummerModification",
    # Concrete modifications
    "BehindBeatTiming",
    "TripletVocabulary",
    "GhostNoteLayer",
    "LinearCoordination",
    "HeavyAccents",
    "ShuffleFeelApplication",
    "FastChopsTriplets",
    "PocketStretching",
    "MinimalCreativity",
    "SpeedPrecision",
    "TwistedAccents",
    "MechanicalPrecision",
    # Registry
    "ModificationRegistry",
]
