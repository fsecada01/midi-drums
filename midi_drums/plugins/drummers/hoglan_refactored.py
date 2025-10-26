"""Refactored Gene Hoglan drummer plugin using modification registry.

Demonstrates modification system applied to Hoglan's signature style.
Compare with original hoglan.py (389 lines) to see code reduction.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    HeavyAccents,
    MechanicalPrecision,
)
from midi_drums.plugins.base import DrummerPlugin


class HoglanPluginRefactored(DrummerPlugin):
    """Refactored Gene Hoglan drummer style plugin.

    Uses modification registry for authentic Hoglan techniques:
    - Mechanical precision and extreme quantization
    - Heavy accents for crushing power
    - Progressive complexity with blast beats
    """

    def __init__(self):
        """Initialize Hoglan modifications."""
        self.mechanical = MechanicalPrecision(quantize_amount=0.95)
        self.heavy = HeavyAccents(accent_boost=25)

    @property
    def drummer_name(self) -> str:
        return "hoglan"

    @property
    def compatible_genres(self) -> list[str]:
        return ["metal", "death", "thrash", "progressive"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Gene Hoglan's signature style using modifications.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Hoglan's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_hoglan"

        # Apply Hoglan's signature techniques
        styled_pattern = self.mechanical.apply(styled_pattern, intensity=1.0)
        styled_pattern = self.heavy.apply(styled_pattern, intensity=0.9)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Gene Hoglan's signature fill patterns.

        Note: In refactored version, fills are generated using
        MechanicalPrecision modification which creates precise,
        powerful fills automatically.
        """
        return []  # Fills handled by modifications
