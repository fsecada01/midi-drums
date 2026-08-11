"""Strategy interface for drum fill generation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from midi_drums.core.models.song import Fill
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)


class FillStrategy(ABC):
    """Strategy interface for generating drum fills for a genre.

    Implementations decide which fills are available for a genre - e.g.
    today's plugin-driven ``get_common_fills()`` lookup, or a future
    complexity-/section-aware strategy - without
    :class:`~midi_drums.generation.engines.drum_generator.DrumGenerator`
    needing to know which.
    """

    @abstractmethod
    def generate(
        self, genre: str, parameters: GenerationParameters
    ) -> list[Fill]:
        """Generate fill patterns for the given genre.

        Args:
            genre: Genre name (e.g. 'metal', 'rock').
            parameters: Generation parameters for this song/pattern.

        Returns:
            Fills available for this genre.
        """
