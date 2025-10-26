"""Refactored Dennis Chambers drummer plugin using modification registry.

Demonstrates modification system applied to Chambers' signature style.
Compare with original chambers.py (381 lines) to see code reduction.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    BehindBeatTiming,
    FastChopsTriplets,
    GhostNoteLayer,
    PocketStretching,
)
from midi_drums.plugins.base import DrummerPlugin


class ChambersPluginRefactored(DrummerPlugin):
    """Refactored Dennis Chambers drummer style plugin.

    Uses modification registry for authentic Chambers techniques:
    - Funk mastery with deep pocket
    - Incredible technical chops
    - Ghost note complexity
    - Pocket stretching and groove variations
    """

    def __init__(self):
        """Initialize Chambers modifications."""
        self.behind_beat = BehindBeatTiming(max_delay_ms=15.0)
        self.fast_chops = FastChopsTriplets()
        self.ghost_notes = GhostNoteLayer(density=0.7)
        self.pocket = PocketStretching(variation_ms=10.0)

    @property
    def drummer_name(self) -> str:
        return "chambers"

    @property
    def compatible_genres(self) -> list[str]:
        return ["funk", "jazz", "fusion", "rock", "r&b"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Dennis Chambers' signature style using modifications.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Chambers' characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_chambers"

        # Apply Chambers' signature techniques
        styled_pattern = self.behind_beat.apply(styled_pattern, intensity=0.6)
        styled_pattern = self.ghost_notes.apply(styled_pattern, intensity=0.8)
        styled_pattern = self.fast_chops.apply(styled_pattern, intensity=0.7)
        styled_pattern = self.pocket.apply(styled_pattern, intensity=0.5)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Dennis Chambers' signature fill patterns.

        Note: In refactored version, fills are generated using
        FastChopsTriplets modification which adds authentic
        Chambers-style technical fills automatically.
        """
        return []  # Fills handled by modifications
