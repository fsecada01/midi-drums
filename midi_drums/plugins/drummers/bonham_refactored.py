"""Refactored John Bonham drummer plugin using modification registry.

Demonstrates modification system applied to Bonham's signature style.
Compare with original bonham.py (339 lines) to see code reduction.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    BehindBeatTiming,
    HeavyAccents,
    TripletVocabulary,
)
from midi_drums.plugins.base import DrummerPlugin


class BonhamPluginRefactored(DrummerPlugin):
    """Refactored John Bonham drummer style plugin.

    Uses modification registry for authentic Bonham techniques:
    - Behind-the-beat timing
    - Triplet vocabulary
    - Heavy accents and powerful sound
    """

    def __init__(self):
        """Initialize Bonham modifications."""
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
        """Apply John Bonham's signature style using modifications.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Bonham's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_bonham"

        # Apply Bonham's signature techniques
        styled_pattern = self.behind_beat.apply(styled_pattern, intensity=0.7)
        styled_pattern = self.triplets.apply(styled_pattern, intensity=0.8)
        styled_pattern = self.accents.apply(styled_pattern, intensity=0.9)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return John Bonham's signature fill patterns.

        Note: In refactored version, fills are generated using
        TripletVocabulary modification which adds authentic
        Bonham-style triplet fills automatically.
        """
        return []  # Fills handled by TripletVocabulary modification
