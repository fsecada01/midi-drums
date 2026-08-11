"""Generation strategy interfaces."""

from midi_drums.generation.strategies.fill_strategy import FillStrategy
from midi_drums.generation.strategies.pattern_strategy import PatternStrategy

__all__ = ["PatternStrategy", "FillStrategy"]
