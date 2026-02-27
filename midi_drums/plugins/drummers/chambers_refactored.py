"""Dennis Chambers drummer plugin - refactored using composable modifications.

Reduced from ~381 lines to ~70 lines (82% reduction) by using the
DrummerModification system instead of manual pattern manipulation.
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


class ChambersPlugin(DrummerPlugin):
    """Dennis Chambers drummer style plugin.

    Characteristics:
    - Funk mastery with incredible technical chops
    - Pocket stretching and groove tension/release
    - Ghost note layers for deep funk texture
    - Fast triplet chops for technical display
    - Slightly behind the beat for laid-back feel

    Implemented using composable modifications:
    - BehindBeatTiming: Subtle laid-back feel
    - FastChopsTriplets: Technical triplet fills
    - GhostNoteLayer: Deep ghost note texture
    - PocketStretching: Subtle timing variations for groove
    """

    def __init__(self):
        self.behind_beat = BehindBeatTiming(max_delay_ms=15.0)
        self.fast_chops = FastChopsTriplets(probability=0.3)
        self.ghost_notes = GhostNoteLayer(density=0.6)
        self.pocket = PocketStretching(variation_ms=8.0)

    @property
    def drummer_name(self) -> str:
        return "chambers"

    @property
    def compatible_genres(self) -> list[str]:
        return ["funk", "jazz", "fusion", "rock", "r&b"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Dennis Chambers' signature style to a pattern."""
        styled = pattern.copy()
        styled.name = f"{pattern.name}_chambers"

        styled = self.behind_beat.apply(styled, intensity=0.5)
        styled = self.fast_chops.apply(styled, intensity=0.7)
        styled = self.ghost_notes.apply(styled, intensity=0.8)
        styled = self.pocket.apply(styled, intensity=0.6)

        return styled

    def get_signature_fills(self) -> list[Fill]:
        """Return Dennis Chambers' signature fill patterns."""
        return []


# backward-compat alias for existing test imports
ChambersPluginRefactored = ChambersPlugin
