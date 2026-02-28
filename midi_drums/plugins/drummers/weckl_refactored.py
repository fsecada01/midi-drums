"""Dave Weckl drummer plugin - refactored using composable modifications.

Reduced from ~383 lines to ~63 lines (84% reduction) by using the
DrummerModification system instead of manual pattern manipulation.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    GhostNoteLayer,
    LinearCoordination,
)
from midi_drums.plugins.base import DrummerPlugin


class WecklPlugin(DrummerPlugin):
    """Dave Weckl drummer style plugin.

    Characteristics:
    - Linear playing (no simultaneous limbs)
    - Sophisticated coordination and independence
    - Jazz-fusion expertise
    - Technical precision with musicality

    Implemented using composable modifications:
    - LinearCoordination: Removes overlapping hits for linear flow
    - GhostNoteLayer: Adds subtle ghost notes for texture and groove
    """

    def __init__(self):
        self.linear = LinearCoordination()
        self.ghost_notes = GhostNoteLayer(density=0.5)

    @property
    def drummer_name(self) -> str:
        return "weckl"

    @property
    def compatible_genres(self) -> list[str]:
        return ["jazz", "fusion", "funk", "rock"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Dave Weckl's signature style to a pattern."""
        styled = pattern.copy()
        styled.name = f"{pattern.name}_weckl"

        styled = self.linear.apply(styled, intensity=0.8)
        styled = self.ghost_notes.apply(styled, intensity=0.7)

        return styled

    def get_signature_fills(self) -> list[Fill]:
        """Return Dave Weckl's signature fill patterns."""
        return []


# backward-compat alias for existing test imports
WecklPluginRefactored = WecklPlugin
