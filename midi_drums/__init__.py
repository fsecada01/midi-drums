"""MIDI Drums - Comprehensive drum track generation system."""

from midi_drums.core.engine import DrumGenerator
from midi_drums.core.models.pattern import Beat, Pattern
from midi_drums.core.models.song import Section, Song
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.core.value_objects.time_signature import TimeSignature

__version__ = "1.0.0"
__all__ = [
    "DrumGenerator",
    "Pattern",
    "Beat",
    "TimeSignature",
    "Song",
    "Section",
    "GenerationParameters",
]
