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

from midi_drums.modifications.cymbal_accent_reaction import CymbalAccentReaction
from midi_drums.modifications.density_control import adjust_density
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
    # Cymbal-accent-reaction (riff accents -> hi-hat/crash/ride reinforce/
    # stab reaction). Same reasoning as SnareAccentReaction above -
    # requires riff_accents/kit_piece arguments with no sensible default,
    # so it's intentionally NOT registered in MODIFICATION_REGISTRY.
    # Construct and call it directly.
    "CymbalAccentReaction",
    # Density control (ADR 0010, Step Editor's Amount knob round-trip).
    # A plain function, not a DrummerModification subclass - it operates
    # on the Step Editor's flat per-note dict shape (bar/step/velocity),
    # not Pattern/Beat, so it doesn't fit the class hierarchy above.
    "adjust_density",
    # Registry
    "ModificationRegistry",
]
