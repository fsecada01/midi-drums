"""MIDI Drums - Comprehensive drum track generation system."""

from .core.engine import DrumGenerator
from .models.pattern import Pattern, Beat, TimeSignature
from .models.song import Song, Section, GenerationParameters

__version__ = "1.0.0"
__all__ = ["DrumGenerator", "Pattern", "Beat", "TimeSignature", "Song", "Section", "GenerationParameters"]