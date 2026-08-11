"""Unit tests for MIDIExporter (issue #10 review follow-up).

Covers two behaviors added to bring MIDIExporter in line with the
ReaperExporter it's documented to mirror: rejecting a Song with no
sections, and creating the destination directory if it doesn't exist
(export_patterns already did this; export_song/export_pattern didn't).
"""

from __future__ import annotations

import pytest

from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Section, Song
from midi_drums.export.midi.exporter import MIDIExporter


class TestExportSongEmptySections:
    def test_raises_on_song_with_no_sections(self, tmp_path):
        song = Song(name="empty", tempo=120)
        exporter = MIDIExporter()

        with pytest.raises(ValueError, match="at least one section"):
            exporter.export_song(song, tmp_path / "song.mid")


class TestExportCreatesDestinationDirectory:
    def test_export_song_creates_missing_parent_directory(self, tmp_path):
        song = Song(name="song", tempo=120)
        song.add_section(
            Section(name="verse", pattern=Pattern(name="verse"), bars=1)
        )
        exporter = MIDIExporter()
        output_path = tmp_path / "nested" / "dir" / "song.mid"

        exporter.export_song(song, output_path)

        assert output_path.exists()

    def test_export_pattern_creates_missing_parent_directory(self, tmp_path):
        pattern = Pattern(name="pattern")
        exporter = MIDIExporter()
        output_path = tmp_path / "nested" / "dir" / "pattern.mid"

        exporter.export_pattern(pattern, output_path)

        assert output_path.exists()
