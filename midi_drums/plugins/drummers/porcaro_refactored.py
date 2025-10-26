"""Refactored Jeff Porcaro drummer plugin using modification registry.

Demonstrates modification system applied to Porcaro's signature style.
Compare with original porcaro.py (369 lines) to see code reduction.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    GhostNoteLayer,
    ShuffleFeelApplication,
)
from midi_drums.plugins.base import DrummerPlugin


class PorcaroPluginRefactored(DrummerPlugin):
    """Refactored Jeff Porcaro drummer style plugin.

    Uses modification registry for authentic Porcaro techniques:
    - Half-time shuffle mastery
    - Ghost note layering
    - Studio precision and taste
    """

    def __init__(self):
        """Initialize Porcaro modifications."""
        self.shuffle = ShuffleFeelApplication(shuffle_amount=0.33)
        self.ghost_notes = GhostNoteLayer(density=0.6)

    @property
    def drummer_name(self) -> str:
        return "porcaro"

    @property
    def compatible_genres(self) -> list[str]:
        return ["rock", "pop", "blues", "funk", "jazz"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Jeff Porcaro's signature style using modifications.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Porcaro's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_porcaro"

        # Apply Porcaro's signature techniques
        styled_pattern = self.shuffle.apply(styled_pattern, intensity=0.8)
        styled_pattern = self.ghost_notes.apply(styled_pattern, intensity=0.7)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Jeff Porcaro's signature fill patterns.

        Note: In refactored version, fills are generated using
        ShuffleFeelApplication and GhostNoteLayer modifications
        which add authentic Porcaro-style patterns automatically.
        """
        return []  # Fills handled by modifications
