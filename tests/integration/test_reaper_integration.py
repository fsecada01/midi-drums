"""Integration tests for Reaper export workflow."""

from __future__ import annotations

import pytest

from midi_drums import DrumGenerator
from midi_drums.engines.reaper_engine import ReaperEngine
from midi_drums.exporters import ReaperExporter
from midi_drums.models.reaper_models import (
    GenreStructurePreset,
    get_genre_preset,
)


class TestReaperExportWorkflow:
    """Test complete Reaper export workflows."""

    def test_full_export_workflow_minimal(self, tmp_path):
        """Test complete workflow: Generate song -> Export to Reaper."""
        # 1. Generate song
        generator = DrumGenerator()
        song = generator.create_song(
            genre="metal",
            style="doom",
            tempo=120,
            structure=[
                ("intro", 4),
                ("verse", 8),
                ("chorus", 8),
                ("bridge", 4),
            ],
        )

        # 2. Export to Reaper
        output_path = tmp_path / "doom_metal.rpp"
        exporter = ReaperExporter()
        exporter.export_with_markers(song=song, output_rpp=str(output_path))

        # 3. Verify .rpp file was created
        assert output_path.exists()

        # 4. Verify file can be loaded
        engine = ReaperEngine()
        project = engine.load_project(str(output_path))
        assert project.tag == "REAPER_PROJECT"

        # 5. Verify markers were added
        markers = [
            c for c in project if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert len(markers) == 4

        # Verify marker names
        marker_names = [m[3] for m in markers]
        assert "intro" in marker_names
        assert "verse" in marker_names
        assert "chorus" in marker_names
        assert "bridge" in marker_names

    def test_export_with_existing_template(self, tmp_path):
        """Test export using existing template project."""
        # Create a template .rpp file
        engine = ReaperEngine()
        template = engine.create_minimal_project(tempo=140)
        template_path = tmp_path / "template.rpp"
        engine.save_project(template, str(template_path))

        # Generate song
        generator = DrumGenerator()
        song = generator.create_song(
            genre="metal", style="heavy", tempo=120, structure=[("verse", 8)]
        )

        # Export using template
        output_path = tmp_path / "from_template.rpp"
        exporter = ReaperExporter()
        exporter.export_with_markers(
            song=song,
            output_rpp=str(output_path),
            input_rpp=str(template_path),
        )

        # Verify template wasn't modified
        template_project = engine.load_project(str(template_path))
        template_markers = [
            c
            for c in template_project
            if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert len(template_markers) == 0  # Template unchanged

        # Verify output has markers
        output_project = engine.load_project(str(output_path))
        output_markers = [
            c
            for c in output_project
            if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert len(output_markers) == 1

    def test_export_with_midi(self, tmp_path):
        """Test export with both .rpp and .mid files."""
        generator = DrumGenerator()
        song = generator.create_song(
            genre="metal", style="doom", tempo=120, structure=[("intro", 4)]
        )

        rpp_path = tmp_path / "project.rpp"
        midi_path = tmp_path / "drums.mid"

        exporter = ReaperExporter()
        exporter.export_with_midi(
            song=song,
            output_rpp=str(rpp_path),
            output_midi=str(midi_path),
        )

        # Verify both files created
        assert rpp_path.exists()
        assert midi_path.exists()

        # Verify .rpp has markers
        engine = ReaperEngine()
        project = engine.load_project(str(rpp_path))
        markers = [
            c for c in project if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert len(markers) == 1

    def test_marker_positions_accuracy(self, tmp_path):
        """Test that marker positions are calculated correctly."""
        generator = DrumGenerator()
        song = generator.create_song(
            genre="metal",
            style="doom",
            tempo=120,
            structure=[
                ("intro", 4),  # 0-8 seconds
                ("verse", 8),  # 8-24 seconds
                ("chorus", 8),  # 24-40 seconds
            ],
        )

        output_path = tmp_path / "positions.rpp"
        exporter = ReaperExporter()
        exporter.export_with_markers(song=song, output_rpp=str(output_path))

        # Load and check marker positions
        engine = ReaperEngine()
        project = engine.load_project(str(output_path))
        markers = [
            c for c in project if isinstance(c, list) and c[0] == "MARKER"
        ]

        # Check positions
        assert float(markers[0][2]) == 0.0  # intro @ 0s
        assert float(markers[1][2]) == 8.0  # verse @ 8s
        assert float(markers[2][2]) == 24.0  # chorus @ 24s

    def test_multiple_songs_same_directory(self, tmp_path):
        """Test exporting multiple songs to same directory."""
        generator = DrumGenerator()

        songs = [
            ("doom_song.rpp", "doom"),
            ("death_song.rpp", "death"),
            ("power_song.rpp", "power"),
        ]

        exporter = ReaperExporter()

        for filename, style in songs:
            song = generator.create_song(
                genre="metal",
                style=style,
                tempo=120,
                structure=[("verse", 8)],
            )

            output_path = tmp_path / filename
            exporter.export_with_markers(song=song, output_rpp=str(output_path))

        # Verify all files created
        for filename, _ in songs:
            assert (tmp_path / filename).exists()

    def test_error_on_empty_song(self):
        """Test that exporting song with no sections raises error."""
        from midi_drums.models.song import Song, TimeSignature

        song = Song(
            name="empty",
            tempo=120,
            time_signature=TimeSignature(4, 4),
            sections=[],  # No sections!
        )

        exporter = ReaperExporter()

        with pytest.raises(ValueError, match="at least one section"):
            exporter.export_with_markers(song=song, output_rpp="test.rpp")


class TestExportWithGenrePreset:
    """Integration tests for ReaperExporter.export_with_genre_preset."""

    def test_creates_rpp_file(self, tmp_path):
        """export_with_genre_preset writes a .rpp file."""
        output_path = tmp_path / "doom.rpp"
        exporter = ReaperExporter()
        exporter.export_with_genre_preset(
            genre="metal",
            style="doom",
            output_rpp=str(output_path),
            tempo=70,
        )
        assert output_path.exists()

    def test_returns_preset(self, tmp_path):
        """export_with_genre_preset returns the GenreStructurePreset used."""
        output_path = tmp_path / "swing.rpp"
        exporter = ReaperExporter()
        preset = exporter.export_with_genre_preset(
            genre="jazz",
            style="swing",
            output_rpp=str(output_path),
        )
        assert isinstance(preset, GenreStructurePreset)
        assert preset.genre == "jazz"
        assert preset.style == "swing"

    def test_markers_count_matches_preset_sections(self, tmp_path):
        """The number of markers equals the number of preset sections."""
        output_path = tmp_path / "heavy.rpp"
        exporter = ReaperExporter()
        preset = exporter.export_with_genre_preset(
            genre="metal",
            style="heavy",
            output_rpp=str(output_path),
            tempo=155,
        )

        engine = ReaperEngine()
        project = engine.load_project(str(output_path))
        markers = [
            c for c in project if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert len(markers) == len(preset.sections)

    def test_first_marker_at_zero(self, tmp_path):
        """First marker is at position 0."""
        output_path = tmp_path / "first_zero.rpp"
        exporter = ReaperExporter()
        exporter.export_with_genre_preset(
            genre="rock",
            style="classic",
            output_rpp=str(output_path),
            tempo=140,
        )

        engine = ReaperEngine()
        project = engine.load_project(str(output_path))
        markers = [
            c for c in project if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert float(markers[0][2]) == 0.0

    def test_uses_preset_default_tempo_when_none(self, tmp_path):
        """RPP tempo element reflects preset default when no tempo given."""
        output_path = tmp_path / "default_tempo.rpp"
        exporter = ReaperExporter()
        preset = exporter.export_with_genre_preset(
            genre="metal",
            style="doom",
            output_rpp=str(output_path),
            tempo=None,
        )

        engine = ReaperEngine()
        project = engine.load_project(str(output_path))
        tempo_elem = next(
            c for c in project if isinstance(c, list) and c[0] == "TEMPO"
        )
        assert int(tempo_elem[1]) == preset.default_tempo

    def test_template_not_modified(self, tmp_path):
        """Input template file is not mutated."""
        # Create template with no markers
        engine = ReaperEngine()
        template = engine.create_minimal_project(tempo=100)
        template_path = tmp_path / "template.rpp"
        engine.save_project(template, str(template_path))

        output_path = tmp_path / "output.rpp"
        exporter = ReaperExporter()
        exporter.export_with_genre_preset(
            genre="funk",
            style="classic",
            output_rpp=str(output_path),
            tempo=110,
            input_rpp=str(template_path),
        )

        # Template still has no markers
        template_project = engine.load_project(str(template_path))
        template_markers = [
            c
            for c in template_project
            if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert len(template_markers) == 0

        # Output does have markers
        output_project = engine.load_project(str(output_path))
        output_markers = [
            c
            for c in output_project
            if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert len(output_markers) > 0

    def test_unknown_genre_still_creates_file(self, tmp_path):
        """Fallback preset ensures a file is always created."""
        output_path = tmp_path / "unknown.rpp"
        exporter = ReaperExporter()
        preset = exporter.export_with_genre_preset(
            genre="orchestral",
            style="romantic",
            output_rpp=str(output_path),
        )
        assert output_path.exists()
        assert isinstance(preset, GenreStructurePreset)


class TestExportComplete:
    """Integration tests for ReaperExporter.export_complete."""

    def test_creates_rpp_file(self, tmp_path):
        """export_complete writes a .rpp file."""
        generator = DrumGenerator()
        song = generator.create_song(
            genre="rock",
            style="classic",
            tempo=140,
            structure=[("verse", 8)],
        )
        song.metadata["genre"] = "rock"
        song.metadata["style"] = "classic"

        output_path = tmp_path / "complete.rpp"
        exporter = ReaperExporter()
        exporter.export_complete(song=song, output_rpp=str(output_path))

        assert output_path.exists()

    def test_creates_midi_when_requested(self, tmp_path):
        """export_complete writes a MIDI file when output_midi is given."""
        generator = DrumGenerator()
        song = generator.create_song(
            genre="metal",
            style="heavy",
            tempo=155,
            structure=[("verse", 8)],
        )

        rpp_path = tmp_path / "with_midi.rpp"
        midi_path = tmp_path / "drums.mid"
        exporter = ReaperExporter()
        exporter.export_complete(
            song=song,
            output_rpp=str(rpp_path),
            output_midi=str(midi_path),
        )

        assert rpp_path.exists()
        assert midi_path.exists()

    def test_no_midi_when_not_requested(self, tmp_path):
        """export_complete does not write a MIDI file by default."""
        generator = DrumGenerator()
        song = generator.create_song(
            genre="jazz",
            style="swing",
            tempo=160,
            structure=[("head", 8)],
        )

        rpp_path = tmp_path / "no_midi.rpp"
        exporter = ReaperExporter()
        exporter.export_complete(song=song, output_rpp=str(rpp_path))

        assert rpp_path.exists()
        midi_path = tmp_path / "no_midi.mid"
        assert not midi_path.exists()

    def test_markers_match_song_sections(self, tmp_path):
        """Markers in the .rpp match the song sections."""
        generator = DrumGenerator()
        song = generator.create_song(
            genre="metal",
            style="doom",
            tempo=70,
            structure=[
                ("intro", 8),
                ("verse", 16),
                ("outro", 8),
            ],
        )
        song.metadata["genre"] = "metal"
        song.metadata["style"] = "doom"

        output_path = tmp_path / "doom_complete.rpp"
        exporter = ReaperExporter()
        exporter.export_complete(song=song, output_rpp=str(output_path))

        engine = ReaperEngine()
        project = engine.load_project(str(output_path))
        markers = [
            c for c in project if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert len(markers) == 3

    def test_raises_on_empty_song(self, tmp_path):
        """export_complete raises ValueError for songs with no sections."""
        from midi_drums.models.song import Song

        empty_song = Song(name="empty", tempo=120, sections=[])
        exporter = ReaperExporter()
        with pytest.raises(ValueError, match="at least one section"):
            exporter.export_complete(
                song=empty_song,
                output_rpp=str(tmp_path / "should_fail.rpp"),
            )


class TestDrumGeneratorAPIReaper:
    """Integration tests for DrumGeneratorAPI Reaper convenience methods."""

    def test_create_reaper_from_preset_creates_file(self, tmp_path):
        """create_reaper_from_preset writes a .rpp file and returns its path."""
        from midi_drums.api.python_api import DrumGeneratorAPI

        api = DrumGeneratorAPI()
        output_path = tmp_path / "preset_only.rpp"
        returned_path = api.create_reaper_from_preset(
            genre="metal",
            style="doom",
            tempo=70,
            output_rpp=str(output_path),
        )

        assert output_path.exists()
        assert "preset_only.rpp" in returned_path

    def test_list_genre_presets_returns_expected_genres(self):
        """list_genre_presets includes metal, rock, jazz, funk."""
        from midi_drums.api.python_api import DrumGeneratorAPI

        api = DrumGeneratorAPI()
        presets = api.list_genre_presets()

        for genre in ("metal", "rock", "jazz", "funk"):
            assert genre in presets
            assert isinstance(presets[genre], list)
            assert len(presets[genre]) > 0

    def test_list_genre_presets_styles_sorted(self):
        """Styles within each genre are alphabetically sorted."""
        from midi_drums.api.python_api import DrumGeneratorAPI

        api = DrumGeneratorAPI()
        presets = api.list_genre_presets()

        for genre, styles in presets.items():
            assert styles == sorted(styles), (
                f"Styles for '{genre}' are not sorted"
            )

    def test_create_reaper_from_preset_markers_correct_count(self, tmp_path):
        """Number of markers equals preset section count."""
        from midi_drums.api.python_api import DrumGeneratorAPI

        api = DrumGeneratorAPI()
        output_path = tmp_path / "jazz_preset.rpp"
        api.create_reaper_from_preset(
            genre="jazz",
            style="swing",
            output_rpp=str(output_path),
        )

        engine = ReaperEngine()
        project = engine.load_project(str(output_path))
        markers = [
            c for c in project if isinstance(c, list) and c[0] == "MARKER"
        ]
        preset = get_genre_preset("jazz", "swing")
        assert len(markers) == len(preset.sections)
