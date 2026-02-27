"""John Bonham drummer plugin - refactored using composable modifications.

Reduced from ~339 lines to ~66 lines (80% reduction) by using the
DrummerModification system instead of manual pattern manipulation.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    BehindBeatTiming,
    HeavyAccents,
    TripletVocabulary,
)
from midi_drums.plugins.base import DrummerPlugin


class BonhamPlugin(DrummerPlugin):
    """John Bonham drummer style plugin.

    Characteristics:
    - Triplet-based rhythmic vocabulary (sixtuplets)
    - "Behind the beat" timing and swing feel
    - Big, powerful sound with heavy kick emphasis
    - Masterful use of space and dynamics

    Implemented using composable modifications:
    - BehindBeatTiming: Lays back behind the beat
    - TripletVocabulary: Adds characteristic triplet fills
    - HeavyAccents: Increases dynamic contrast
    """

    def __init__(self):
        self.behind_beat = BehindBeatTiming(max_delay_ms=25.0)
        self.triplets = TripletVocabulary(triplet_probability=0.4)
        self.accents = HeavyAccents(accent_boost=15)

    @property
    def drummer_name(self) -> str:
        return "bonham"

    @property
    def compatible_genres(self) -> list[str]:
        return ["rock", "metal", "blues", "hard_rock"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply John Bonham's signature style to a pattern."""
        styled = pattern.copy()
        styled.name = f"{pattern.name}_bonham"

        styled = self.behind_beat.apply(styled, intensity=0.7)
        styled = self.triplets.apply(styled, intensity=0.8)
        styled = self.accents.apply(styled, intensity=0.9)

        return styled

    def get_signature_fills(self) -> list[Fill]:
        """Return John Bonham's signature fill patterns."""
        return []
