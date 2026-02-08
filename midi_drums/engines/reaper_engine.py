"""Reaper .RPP file manipulation engine."""

from pathlib import Path
from typing import List

import rpp

from midi_drums.models.reaper_models import Marker
from midi_drums.models.song import Song, TimeSignature


def bars_to_seconds(
    bars: int, tempo: int, time_signature: TimeSignature
) -> float:
    """Convert bars to seconds for marker positioning.

    Formula:
        total_beats = bars * beats_per_bar
        total_seconds = (total_beats / tempo) * 60

    Args:
        bars: Number of bars
        tempo: Tempo in BPM
        time_signature: Time signature (for beats_per_bar)

    Returns:
        Position in seconds

    Examples:
        >>> from midi_drums.models.song import TimeSignature
        >>> bars_to_seconds(4, 120, TimeSignature(4, 4))
        8.0
        >>> bars_to_seconds(8, 120, TimeSignature(4, 4))
        16.0
        >>> bars_to_seconds(4, 180, TimeSignature(4, 4))
        5.333333333333333
    """
    if tempo <= 0:
        raise ValueError(f"Tempo must be positive, got {tempo}")
    if bars < 0:
        raise ValueError(f"Bars must be non-negative, got {bars}")

    beats_per_bar = time_signature.numerator
    total_beats = bars * beats_per_bar
    return (total_beats / tempo) * 60.0


class ReaperEngine:
    """Low-level Reaper .RPP file manipulation.

    Provides core functionality for creating and modifying Reaper project
    files, including marker management and basic project structure.

    Example:
        >>> engine = ReaperEngine()
        >>> markers = [
        ...     Marker(0.0, "Intro", marker_id=1),
        ...     Marker(8.0, "Verse", marker_id=2),
        ... ]
        >>> project = engine.create_minimal_project()
        >>> engine.add_markers(project, markers)
        >>> output = rpp.dumps(project)
    """

    def __init__(self, default_tempo: int = 120):
        """Initialize Reaper engine.

        Args:
            default_tempo: Default tempo for new projects (BPM)
        """
        self.default_tempo = default_tempo

    def create_minimal_project(
        self, tempo: int = None, time_signature: TimeSignature = None
    ) -> rpp.Element:
        """Create minimal Reaper project structure.

        Args:
            tempo: Project tempo in BPM (uses default if not provided)
            time_signature: Time signature (defaults to 4/4)

        Returns:
            rpp.Element representing the project
        """
        tempo = tempo or self.default_tempo
        time_sig = time_signature or TimeSignature(4, 4)

        project = rpp.Element(
            tag="REAPER_PROJECT",
            attrib=["0.1", "7.0", "1234567890"],
        )

        # Add basic project settings
        project.append(["RIPPLE", "0"])
        project.append(["GROUPOVERRIDE", "0", "0", "0"])
        project.append(["AUTOXFADE", "1"])
        project.append(
            [
                "TEMPO",
                str(tempo),
                str(time_sig.numerator),
                str(time_sig.denominator),
            ]
        )

        return project

    def add_markers(self, project: rpp.Element, markers: list[Marker]) -> None:
        """Add markers to Reaper project.

        Modifies the project in-place by appending marker entries.

        Args:
            project: RPP Element to modify
            markers: List of markers to add

        Example:
            >>> project = engine.create_minimal_project()
            >>> markers = [Marker(0.0, "Start", marker_id=1)]
            >>> engine.add_markers(project, markers)
        """
        for marker in markers:
            # Auto-assign marker IDs if not provided
            if marker.marker_id is None:
                existing_markers = [
                    c
                    for c in project
                    if isinstance(c, list) and c[0] == "MARKER"
                ]
                marker.marker_id = len(existing_markers) + 1

            project.append(marker.to_rpp_list())

    def load_project(self, rpp_path: str) -> rpp.Element:
        """Load Reaper project from .rpp file.

        Args:
            rpp_path: Path to .rpp file

        Returns:
            Parsed project Element

        Raises:
            FileNotFoundError: If .rpp file doesn't exist
            ValueError: If file has invalid RPP syntax
        """
        path = Path(rpp_path)
        if not path.exists():
            raise FileNotFoundError(f"RPP file not found: {rpp_path}")

        try:
            with open(path) as f:
                return rpp.loads(f.read())
        except Exception as e:
            raise ValueError(f"Invalid RPP file: {e}") from e

    def save_project(self, project: rpp.Element, output_path: str) -> None:
        """Save Reaper project to .rpp file.

        Args:
            project: RPP Element to save
            output_path: Destination .rpp file path

        Example:
            >>> project = engine.create_minimal_project()
            >>> engine.save_project(project, "output.rpp")
        """
        output = rpp.dumps(project)
        with open(output_path, "w") as f:
            f.write(output)

    def calculate_marker_positions_from_song(self, song: Song) -> list[Marker]:
        """Calculate marker positions from Song structure.

        Args:
            song: Song object with sections

        Returns:
            List of Markers with calculated positions

        Example:
            >>> from midi_drums.models.song import Song, Section
            >>> song = Song(
            ...     name="Test",
            ...     tempo=120,
            ...     sections=[
            ...         Section(name="intro", bars=4),
            ...         Section(name="verse", bars=8),
            ...     ]
            ... )
            >>> markers = engine.calculate_marker_positions_from_song(song)
            >>> len(markers)
            2
        """
        markers = []
        cumulative_bars = 0
        marker_id = 1

        for section in song.sections:
            position_seconds = bars_to_seconds(
                cumulative_bars, song.tempo, song.time_signature
            )

            markers.append(
                Marker(
                    position_seconds=position_seconds,
                    name=section.name,
                    marker_id=marker_id,
                )
            )

            cumulative_bars += section.bars
            marker_id += 1

        return markers
