"""MIDI Drums - Comprehensive drum track generation system."""

from midi_drums.core.models.pattern import Beat, Pattern
from midi_drums.core.models.song import Section, Song
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.core.value_objects.time_signature import TimeSignature
from midi_drums.generation.engines.drum_generator import DrumGenerator

__version__ = "0.1.0"
__all__ = [
    "DrumGenerator",
    "Pattern",
    "Beat",
    "TimeSignature",
    "Song",
    "Section",
    "GenerationParameters",
]
