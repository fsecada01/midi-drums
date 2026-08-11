"""DrummerPlugin interface - base class for drummer style modifiers."""

from abc import ABC, abstractmethod

from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Fill


class DrummerPlugin(ABC):
    """Base class for drummer style modifiers."""

    @property
    @abstractmethod
    def drummer_name(self) -> str:
        """Name of the drummer this plugin emulates."""
        pass

    @property
    @abstractmethod
    def compatible_genres(self) -> list[str]:
        """List of genres this drummer style works well with."""
        pass

    @abstractmethod
    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply drummer-specific style modifications to a pattern.

        Args:
            pattern: Base pattern to modify

        Returns:
            Modified pattern with drummer's style applied
        """
        pass

    @abstractmethod
    def get_signature_fills(self) -> list[Fill]:
        """Get fill patterns characteristic of this drummer."""
        pass

    def is_compatible_with_genre(self, genre: str) -> bool:
        """Check if this drummer style is compatible with the genre."""
        return genre in self.compatible_genres

    def get_style_parameters(self) -> dict[str, float]:
        """Get style-specific parameter adjustments.

        Returns dict with parameter names and their adjusted values.
        Default implementation returns empty dict.
        """
        return {}
