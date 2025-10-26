"""Refactored Jason Roeder drummer plugin using modification registry.

Demonstrates modification system applied to Roeder's signature style.
Compare with original roeder.py (371 lines) to see code reduction.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    HeavyAccents,
    MinimalCreativity,
)
from midi_drums.plugins.base import DrummerPlugin


class RoederPluginRefactored(DrummerPlugin):
    """Refactored Jason Roeder drummer style plugin.

    Uses modification registry for authentic Roeder techniques:
    - Atmospheric sludge metal approach
    - Minimal creativity with maximum impact
    - Heavy, crushing accents
    """

    def __init__(self):
        """Initialize Roeder modifications."""
        self.minimal = MinimalCreativity(sparseness=0.4)
        self.heavy = HeavyAccents(accent_boost=20)

    @property
    def drummer_name(self) -> str:
        return "roeder"

    @property
    def compatible_genres(self) -> list[str]:
        return ["metal", "sludge", "post_metal", "doom", "atmospheric"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Jason Roeder's signature style using modifications.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Roeder's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_roeder"

        # Apply Roeder's signature techniques
        styled_pattern = self.minimal.apply(styled_pattern, intensity=0.8)
        styled_pattern = self.heavy.apply(styled_pattern, intensity=1.0)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Jason Roeder's signature fill patterns.

        Note: In refactored version, fills are generated using
        MinimalCreativity modification which creates atmospheric,
        sparse fills automatically.
        """
        return []  # Fills handled by modifications
