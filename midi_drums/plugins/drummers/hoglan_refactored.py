"""Gene Hoglan drummer plugin - refactored using composable modifications.

Reduced from ~389 lines to ~63 lines (84% reduction) by using the
DrummerModification system instead of manual pattern manipulation.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    HeavyAccents,
    MechanicalPrecision,
)
from midi_drums.plugins.base import DrummerPlugin


class HoglanPlugin(DrummerPlugin):
    """Gene Hoglan drummer style plugin.

    Characteristics:
    - Mechanical precision and extreme consistency
    - Blast beats and progressive complexity
    - Heavy accents for extreme metal power
    - Machine-like quantization and uniformity

    Implemented using composable modifications:
    - MechanicalPrecision: Extreme quantization for machine-like feel
    - HeavyAccents: Boosts accent contrast for extreme metal power
    """

    def __init__(self):
        self.precision = MechanicalPrecision(quantize_amount=0.98)
        self.accents = HeavyAccents(accent_boost=18)

    @property
    def drummer_name(self) -> str:
        return "hoglan"

    @property
    def compatible_genres(self) -> list[str]:
        return ["metal", "death_metal", "thrash"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Gene Hoglan's signature style to a pattern."""
        styled = pattern.copy()
        styled.name = f"{pattern.name}_hoglan"

        styled = self.precision.apply(styled, intensity=1.0)
        styled = self.accents.apply(styled, intensity=0.9)

        return styled

    def get_signature_fills(self) -> list[Fill]:
        """Return Gene Hoglan's signature fill patterns."""
        return []
