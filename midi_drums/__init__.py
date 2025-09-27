"""MIDI Drums - Comprehensive drum track generation system."""

from midi_drums.core.engine import DrumGenerator
from midi_drums.models.pattern import Pattern, Beat, TimeSignature
from midi_drums.models.song import Song, Section, GenerationParameters

__version__ = "1.0.0"
__all__ = ["DrumGenerator", "Pattern", "Beat", "TimeSignature", "Song", "Section", "GenerationParameters"]