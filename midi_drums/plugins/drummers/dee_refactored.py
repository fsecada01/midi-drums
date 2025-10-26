"""Refactored Mikkey Dee drummer plugin using modification registry.

Demonstrates modification system applied to Dee's signature style.
Compare with original dee.py (360 lines) to see code reduction.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    SpeedPrecision,
    TwistedAccents,
)
from midi_drums.plugins.base import DrummerPlugin


class DeePluginRefactored(DrummerPlugin):
    """Refactored Mikkey Dee drummer style plugin.

    Uses modification registry for authentic Dee techniques:
    - Speed and precision mastery
    - Twisted accents and displaced patterns
    - Versatile power across genres
    """

    def __init__(self):
        """Initialize Dee modifications."""
        self.speed = SpeedPrecision()
        self.twisted = TwistedAccents(displacement=0.5)

    @property
    def drummer_name(self) -> str:
        return "dee"

    @property
    def compatible_genres(self) -> list[str]:
        return ["metal", "speed_metal", "punk", "hard_rock", "horror_metal"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Mikkey Dee's signature style using modifications.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Dee's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_dee"

        # Apply Dee's signature techniques
        styled_pattern = self.speed.apply(styled_pattern, intensity=0.9)
        styled_pattern = self.twisted.apply(styled_pattern, intensity=0.7)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Mikkey Dee's signature fill patterns.

        Note: In refactored version, fills are generated using
        SpeedPrecision and TwistedAccents modifications which
        add authentic Dee-style patterns automatically.
        """
        return []  # Fills handled by modifications
