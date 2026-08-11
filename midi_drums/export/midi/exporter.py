"""High-level API for MIDI file export."""

from __future__ import annotations

from pathlib import Path

from midi_drums.core.models.kit import DrumKit
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Song
from midi_drums.export.midi.engine import MIDIEngine


class MIDIExporter:
    """High-level API for exporting patterns and songs to MIDI files.

    Thin convenience wrapper around :class:`MIDIEngine`, mirroring the
    engine/exporter split used by the Reaper export domain
    (:class:`~midi_drums.export.reaper.engine.ReaperEngine` /
    :class:`~midi_drums.export.reaper.exporter.ReaperExporter`).

    Example:
        >>> from midi_drums import DrumGenerator
        >>> from midi_drums.export.midi.exporter import MIDIExporter
        >>>
        >>> generator = DrumGenerator()
        >>> song = generator.create_song("metal", "doom", tempo=120)
        >>> exporter = MIDIExporter()
        >>> exporter.export_song(song, "doom_metal.mid")
    """

    def __init__(self, drum_kit: DrumKit | None = None):
        """Initialize MIDI exporter with optional drum kit configuration."""
        self.midi_engine = MIDIEngine(drum_kit)

    def export_song(self, song: Song, output_path: str | Path) -> None:
        """Export a complete song as a MIDI file.

        Args:
            song: Song to export.
            output_path: Destination ``.mid`` file path.

        Raises:
            ValueError: If song has no sections.
        """
        if not song.sections:
            raise ValueError("Song must have at least one section")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.midi_engine.save_song_midi(song, output_path)

    def export_pattern(
        self, pattern: Pattern, output_path: str | Path, tempo: int = 120
    ) -> None:
        """Export a single pattern as a MIDI file.

        Args:
            pattern: Pattern to export.
            output_path: Destination ``.mid`` file path.
            tempo: Tempo in BPM.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.midi_engine.save_pattern_midi(pattern, output_path, tempo)

    def export_patterns(
        self,
        patterns: list[Pattern],
        output_dir: str | Path,
        tempo: int = 120,
    ) -> list[Path]:
        """Export multiple patterns to separate MIDI files.

        Args:
            patterns: Patterns to export.
            output_dir: Destination directory (created if missing).
            tempo: Tempo in BPM.

        Returns:
            Paths to the written MIDI files.
        """
        return self.midi_engine.export_patterns_to_separate_files(
            patterns, Path(output_dir), tempo
        )
