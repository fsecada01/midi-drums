"""Strategy interface for single-pattern generation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from midi_drums.core.models.pattern import Pattern
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)


class PatternStrategy(ABC):
    """Strategy interface for generating a single Pattern.

    Implementations decide how a genre/section pair becomes a concrete
    Pattern - e.g. today's plugin-driven generation
    (:class:`~midi_drums.plugins.registry.plugin_registry.PluginManager`),
    or a future template- or AI-driven strategy - without
    :class:`~midi_drums.generation.engines.drum_generator.DrumGenerator`
    needing to know which.
    """

    @abstractmethod
    def generate(
        self, genre: str, section: str, parameters: GenerationParameters
    ) -> Pattern | None:
        """Generate a Pattern for the given genre/section.

        Args:
            genre: Genre name (e.g. 'metal', 'rock').
            section: Section type (e.g. 'verse', 'chorus').
            parameters: Generation parameters for this pattern.

        Returns:
            Generated Pattern, or None if generation is not possible.
        """
