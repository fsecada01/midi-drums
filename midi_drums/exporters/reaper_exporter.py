"""High-level API for Reaper DAW integration."""

from __future__ import annotations

from pathlib import Path

from midi_drums.engines.midi_engine import MIDIEngine
from midi_drums.engines.reaper_engine import ReaperEngine
from midi_drums.models.reaper_models import (
    GenreStructurePreset,
)
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
            marker_color: Hex color for markers (e.g., "#FF5733").  When the
                song carries genre metadata the per-section colors from
                :func:`~midi_drums.models.reaper_models.get_section_color`
                are used instead and this parameter is ignored.

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

        # Calculate markers — use song-derived colors when genre metadata
        # is available, otherwise fall back to the caller-supplied color.
        use_genre_colors = bool(song.metadata.get("genre"))
        markers = self.reaper_engine.calculate_marker_positions_from_song(song)

        if not use_genre_colors:
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

    # ------------------------------------------------------------------
    # Genre-preset aware export methods
    # ------------------------------------------------------------------

    def export_with_genre_preset(
        self,
        genre: str,
        style: str,
        output_rpp: str,
        tempo: int | None = None,
        input_rpp: str | None = None,
        name: str | None = None,
    ) -> GenreStructurePreset:
        """Export a Reaper project with genre-smart markers without generating MIDI.

        Looks up (or falls back to) the best :class:`GenreStructurePreset`
        for the requested *genre*/*style*, builds marker positions directly
        from the preset, and writes an ``.rpp`` file.  No drum audio or MIDI
        is generated — this is purely a structural marker export.

        This operation is immutable: *input_rpp* is never modified; the
        result is always written to *output_rpp*.

        Args:
            genre: Genre name (e.g. ``"metal"``).
            style: Style within genre (e.g. ``"doom"``).
            output_rpp: Destination ``.rpp`` file path.
            tempo: Override BPM.  Uses ``preset.default_tempo`` when ``None``.
            input_rpp: Existing ``.rpp`` template to use as the project base.
                A new minimal project is created when ``None``.
            name: Song/project name (used in metadata only; not written to
                the ``.rpp`` at this time).

        Returns:
            The :class:`GenreStructurePreset` that was used, so callers can
            inspect section counts, tempo range, etc.

        Example:
            >>> exporter = ReaperExporter()
            >>> preset = exporter.export_with_genre_preset(
            ...     "metal", "doom", "doom_markers.rpp", tempo=70
            ... )
            >>> print(preset.style)
            doom
        """
        preset = self.reaper_engine.get_genre_preset(genre, style)
        resolved_tempo = tempo if tempo is not None else preset.default_tempo
        num, den = preset.time_signature
        from midi_drums.models.song import TimeSignature

        time_sig = TimeSignature(num, den)

        # Load or create project
        if input_rpp:
            project = self.reaper_engine.load_project(input_rpp)
        else:
            project = self.reaper_engine.create_minimal_project(
                tempo=resolved_tempo, time_signature=time_sig
            )

        # Build markers directly from the preset (no Song object required)
        markers = self.reaper_engine.calculate_marker_positions_from_preset(
            preset=preset,
            tempo=resolved_tempo,
            time_sig=preset.time_signature,
        )

        self.reaper_engine.add_markers(project, markers)
        self.reaper_engine.save_project(project, output_rpp)

        return preset

    def export_complete(
        self,
        song: Song,
        output_rpp: str,
        output_midi: str | None = None,
        input_rpp: str | None = None,
    ) -> None:
        """Export song to RPP (with markers) and optionally MIDI in one call.

        Uses per-section colors derived from the song's genre metadata when
        available, so each section type gets its own canonical color.

        Args:
            song: Song object with sections to export.
            output_rpp: Destination ``.rpp`` file path.
            output_midi: Optional MIDI file path.  When provided the drum
                track is also written to this file.
            input_rpp: Existing ``.rpp`` template to use as project base.

        Raises:
            ValueError: If *song* has no sections.

        Example:
            >>> exporter.export_complete(
            ...     song,
            ...     "project.rpp",
            ...     output_midi="drums.mid",
            ... )
        """
        if not song.sections:
            raise ValueError("Song must have at least one section")

        # Build project
        if input_rpp:
            project = self.reaper_engine.load_project(input_rpp)
        else:
            project = self.reaper_engine.create_minimal_project(
                tempo=song.tempo, time_signature=song.time_signature
            )

        # Markers with genre-aware colors
        genre = song.metadata.get("genre", "")
        style = song.metadata.get("style", "*")

        if genre:
            preset = self.reaper_engine.get_genre_preset(genre, style)
            markers = self.reaper_engine.calculate_marker_positions_from_song(
                song
            )
            # Apply preset section colors
            for marker in markers:
                marker.color = preset.section_color(marker.name)
        else:
            markers = self.reaper_engine.calculate_marker_positions_from_song(
                song
            )

        self.reaper_engine.add_markers(project, markers)
        self.reaper_engine.save_project(project, output_rpp)

        # Optionally write MIDI
        if output_midi:
            self.midi_engine.save_song_midi(song, output_midi)
