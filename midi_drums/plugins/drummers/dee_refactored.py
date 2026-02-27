"""Mikkey Dee drummer plugin - refactored using composable modifications.

Reduced from ~360 lines to ~63 lines (82% reduction) by using the
DrummerModification system instead of manual pattern manipulation.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    SpeedPrecision,
    TwistedAccents,
)
from midi_drums.plugins.base import DrummerPlugin


class DeePlugin(DrummerPlugin):
    """Mikkey Dee drummer style plugin.

    Characteristics:
    - Speed and precision (Motorhead, Scorpions)
    - Versatile power across rock and metal
    - Twisted, displaced backbeats for interest
    - Extremely consistent timing and dynamics

    Implemented using composable modifications:
    - SpeedPrecision: Normalizes velocities and tightens timing
    - TwistedAccents: Displaces accents to unexpected positions
    """

    def __init__(self):
        self.precision = SpeedPrecision(consistency=0.95)
        self.twisted = TwistedAccents(displacement=0.25)

    @property
    def drummer_name(self) -> str:
        return "dee"

    @property
    def compatible_genres(self) -> list[str]:
        return ["metal", "speed_metal", "punk", "hard_rock", "horror_metal"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Mikkey Dee's signature style to a pattern."""
        styled = pattern.copy()
        styled.name = f"{pattern.name}_dee"

        styled = self.precision.apply(styled, intensity=0.9)
        styled = self.twisted.apply(styled, intensity=0.7)

        return styled

    def get_signature_fills(self) -> list[Fill]:
        """Return Mikkey Dee's signature fill patterns."""
        return []


# backward-compat alias for existing test imports
DeePluginRefactored = DeePlugin
