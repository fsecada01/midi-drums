"""Jeff Porcaro drummer plugin - refactored using composable modifications.

Reduced from ~369 lines to ~63 lines (83% reduction) by using the
DrummerModification system instead of manual pattern manipulation.
"""

from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Fill
from midi_drums.modifications import (
    GhostNoteLayer,
    ShuffleFeelApplication,
)
from midi_drums.plugins.base import DrummerPlugin


class PorcaroPlugin(DrummerPlugin):
    """Jeff Porcaro drummer style plugin.

    Characteristics:
    - Half-time shuffle mastery (Rosanna shuffle)
    - Ghost notes for groove texture
    - Studio precision and consistency
    - Sophisticated feel and dynamics

    Implemented using composable modifications:
    - ShuffleFeelApplication: Applies Porcaro's legendary shuffle feel
    - GhostNoteLayer: Adds characteristic ghost notes between main hits
    """

    def __init__(self):
        self.shuffle = ShuffleFeelApplication(shuffle_amount=0.6)
        self.ghost_notes = GhostNoteLayer(density=0.4)

    @property
    def drummer_name(self) -> str:
        return "porcaro"

    @property
    def compatible_genres(self) -> list[str]:
        return ["rock", "pop", "jazz", "funk"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Jeff Porcaro's signature style to a pattern."""
        styled = pattern.copy()
        styled.name = f"{pattern.name}_porcaro"

        styled = self.shuffle.apply(styled, intensity=0.8)
        styled = self.ghost_notes.apply(styled, intensity=0.7)

        return styled

    def get_signature_fills(self) -> list[Fill]:
        """Return Jeff Porcaro's signature fill patterns."""
        return []
