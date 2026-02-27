"""Jason Roeder drummer plugin - refactored using composable modifications.

Reduced from ~371 lines to ~63 lines (83% reduction) by using the
DrummerModification system instead of manual pattern manipulation.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    HeavyAccents,
    MinimalCreativity,
)
from midi_drums.plugins.base import DrummerPlugin


class RoederPlugin(DrummerPlugin):
    """Jason Roeder drummer style plugin.

    Characteristics:
    - Atmospheric sludge and doom metal approach
    - Minimal, sparse cymbal work for heavy atmosphere
    - Crushing, powerful accents on kick and snare
    - Patience and restraint in pattern density

    Implemented using composable modifications:
    - MinimalCreativity: Thins out non-essential cymbal hits
    - HeavyAccents: Adds crushing power to remaining hits
    """

    def __init__(self):
        self.minimal = MinimalCreativity(sparseness=0.7)
        self.accents = HeavyAccents(accent_boost=20)

    @property
    def drummer_name(self) -> str:
        return "roeder"

    @property
    def compatible_genres(self) -> list[str]:
        return ["metal", "sludge", "post_metal", "doom", "atmospheric"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Jason Roeder's signature style to a pattern."""
        styled = pattern.copy()
        styled.name = f"{pattern.name}_roeder"

        styled = self.minimal.apply(styled, intensity=0.8)
        styled = self.accents.apply(styled, intensity=0.9)

        return styled

    def get_signature_fills(self) -> list[Fill]:
        """Return Jason Roeder's signature fill patterns."""
        return []


# backward-compat alias for existing test imports
RoederPluginRefactored = RoederPlugin
