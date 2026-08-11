"""High-level orchestration service for pattern/song generation."""

from __future__ import annotations

from pathlib import Path

from midi_drums.core.models.kit import DrumKit
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Song
from midi_drums.generation.engines.drum_generator import DrumGenerator


class GenerationService:
    """Thin orchestration layer over :class:`DrumGenerator`.

    Mirrors the engine/high-level-API split used by the export domain
    (:class:`~midi_drums.export.midi.engine.MIDIEngine` /
    :class:`~midi_drums.export.midi.exporter.MIDIExporter`): DrumGenerator
    owns pattern/song composition, GenerationService is the stable entry
    point other layers call through - and the natural place to route
    generation through a
    :class:`~midi_drums.generation.strategies.pattern_strategy.PatternStrategy`
    or :class:`~midi_drums.generation.strategies.fill_strategy.FillStrategy`
    once concrete strategies exist.

    Example:
        >>> from midi_drums.generation.services.generation_service import (
        ...     GenerationService,
        ... )
        >>> service = GenerationService()
        >>> song = service.generate_song("metal", "doom", tempo=120)
    """

    def __init__(
        self,
        config_path: Path | None = None,
        drum_generator: DrumGenerator | None = None,
    ):
        """Initialize the service with an optional pre-configured engine.

        Args:
            config_path: Passed through to a new DrumGenerator. Ignored if
                drum_generator is also given - the pre-built instance wins.
            drum_generator: Use this engine instead of constructing one.
        """
        self.drum_generator = drum_generator or DrumGenerator(config_path)

    def generate_song(
        self,
        genre: str,
        style: str = "default",
        tempo: int = 120,
        structure: list[tuple[str, int]] | None = None,
        drum_kit: DrumKit | None = None,
        **kwargs,
    ) -> Song:
        """Generate a complete song. See DrumGenerator.create_song."""
        return self.drum_generator.create_song(
            genre, style, tempo, structure, drum_kit, **kwargs
        )

    def generate_pattern(
        self, genre: str, section: str = "verse", bars: int = 4, **kwargs
    ) -> Pattern | None:
        """Generate a single pattern. See DrumGenerator.generate_pattern."""
        return self.drum_generator.generate_pattern(
            genre, section, bars, **kwargs
        )
