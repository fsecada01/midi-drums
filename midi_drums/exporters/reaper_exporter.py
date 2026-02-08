"""High-level API for Reaper DAW integration."""

from pathlib import Path
from typing import Optional

from midi_drums.engines.midi_engine import MIDIEngine
from midi_drums.engines.reaper_engine import ReaperEngine
from midi_drums.models.song import Song


class ReaperExporter:
    """High-level API for exporting to Reaper projects.

    Provides convenient methods for integrating MIDI drum generation
    with Reaper DAW projects through .RPP file manipulation.

    Example:
        >>> from midi_drums import DrumGenerator
        >>> from midi_drums.exporters import ReaperExporter
        >>>
        >>> # Generate drums
        >>> generator = DrumGenerator()
        >>> song = generator.create_song("metal", "doom", tempo=120)
        >>>
        >>> # Export to Reaper with markers
        >>> exporter = ReaperExporter()
        >>> exporter.export_with_markers(
        ...     song=song,
        ...     output_rpp="doom_metal.rpp"
        ... )
    """

    def __init__(self):
        """Initialize Reaper exporter."""
        self.reaper_engine = ReaperEngine()
        self.midi_engine = MIDIEngine()

    def export_with_markers(
        self,
        song: Song,
        output_rpp: str,
        input_rpp: str | None = None,
        add_midi_track: bool = False,
        marker_color: str = "#FF5733",
    ) -> None:
        """Export song with markers to Reaper project.

        Creates a new Reaper project file with section markers corresponding
        to the song structure. Optionally adds a MIDI track with the drum
        performance.

        This operation is immutable - if input_rpp is provided, it is not
        modified. A new file is always created at output_rpp.

        Args:
            song: Song object with sections to export
            output_rpp: Path to output .rpp file
            input_rpp: Path to existing .rpp to use as base (optional)
            add_midi_track: Also add MIDI track with performance
            marker_color: Hex color for markers (e.g., "#FF5733")

        Raises:
            FileNotFoundError: If input_rpp doesn't exist
            ValueError: If song has no sections

        Example:
            >>> exporter = ReaperExporter()
            >>> exporter.export_with_markers(
            ...     song=my_song,
            ...     output_rpp="project_with_drums.rpp",
            ...     input_rpp="template.rpp",
            ...     add_midi_track=True
            ... )
        """
        if not song.sections:
            raise ValueError("Song must have at least one section")

        # Load existing project or create new one
        if input_rpp:
            project = self.reaper_engine.load_project(input_rpp)
        else:
            project = self.reaper_engine.create_minimal_project(
                tempo=song.tempo, time_signature=song.time_signature
            )

        # Calculate and add markers
        markers = self.reaper_engine.calculate_marker_positions_from_song(song)

        # Apply custom color to markers
        for marker in markers:
            marker.color = marker_color

        self.reaper_engine.add_markers(project, markers)

        # TODO: Add MIDI track if requested (Phase 2)
        if add_midi_track:
            # This would require implementing MIDI track creation in RPP
            # For now, we'll just save the MIDI file separately
            midi_path = str(Path(output_rpp).with_suffix(".mid"))
            self.midi_engine.save_song_midi(song, midi_path)

        # Save project
        self.reaper_engine.save_project(project, output_rpp)

    def export_minimal_project(self, song: Song, output_rpp: str) -> None:
        """Export song as minimal Reaper project with just markers.

        Convenience method for quick exports without base template.

        Args:
            song: Song to export
            output_rpp: Output .rpp file path

        Example:
            >>> exporter.export_minimal_project(song, "quick_export.rpp")
        """
        self.export_with_markers(
            song=song, output_rpp=output_rpp, add_midi_track=False
        )

    def export_with_midi(
        self, song: Song, output_rpp: str, output_midi: str
    ) -> None:
        """Export both Reaper project and MIDI file.

        Convenience method to export both project with markers and
        separate MIDI file in one call.

        Args:
            song: Song to export
            output_rpp: Output .rpp file path
            output_midi: Output MIDI file path

        Example:
            >>> exporter.export_with_midi(
            ...     song,
            ...     "project.rpp",
            ...     "drums.mid"
            ... )
        """
        # Export Reaper project with markers
        self.export_with_markers(song=song, output_rpp=output_rpp)

        # Export MIDI separately
        self.midi_engine.save_song_midi(song, output_midi)
