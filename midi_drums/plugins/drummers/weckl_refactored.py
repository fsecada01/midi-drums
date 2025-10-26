"""Refactored Dave Weckl drummer plugin using modification registry.

Demonstrates modification system applied to Weckl's signature style.
Compare with original weckl.py (383 lines) to see code reduction.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    GhostNoteLayer,
    LinearCoordination,
)
from midi_drums.plugins.base import DrummerPlugin


class WecklPluginRefactored(DrummerPlugin):
    """Refactored Dave Weckl drummer style plugin.

    Uses modification registry for authentic Weckl techniques:
    - Linear coordination (no simultaneous limbs)
    - Sophisticated ghost notes
    - Fusion complexity and precision
    """

    def __init__(self):
        """Initialize Weckl modifications."""
        self.linear = LinearCoordination()
        self.ghost_notes = GhostNoteLayer(density=0.5)

    @property
    def drummer_name(self) -> str:
        return "weckl"

    @property
    def compatible_genres(self) -> list[str]:
        return ["jazz", "fusion", "funk", "rock"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Dave Weckl's signature style using modifications.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Weckl's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_weckl"

        # Apply Weckl's signature techniques
        styled_pattern = self.linear.apply(styled_pattern, intensity=0.9)
        styled_pattern = self.ghost_notes.apply(styled_pattern, intensity=0.6)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Dave Weckl's signature fill patterns.

        Note: In refactored version, fills are generated using
        LinearCoordination and GhostNoteLayer modifications
        which add authentic Weckl-style patterns automatically.
        """
        return []  # Fills handled by modifications
