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
from midi_drums.modifications.riff_lock import RiffLockTransform
from midi_drums.modifications.snare_accent_reaction import SnareAccentReaction

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
    # Riff-lock (audio riff -> kick-locked pattern). Intentionally NOT
    # registered in MODIFICATION_REGISTRY - it requires a riff_accents
    # argument with no sensible default, so ModificationRegistry's
    # zero-arg construction would fail. Construct and call it directly.
    "RiffLockTransform",
    # Snare-accent-reaction (riff accents -> snare reinforce/stab reaction).
    # Same reasoning as RiffLockTransform above - requires a riff_accents
    # argument with no sensible default, so it's intentionally NOT
    # registered in MODIFICATION_REGISTRY. Construct and call it directly.
    "SnareAccentReaction",
    # Registry
    "ModificationRegistry",
]
