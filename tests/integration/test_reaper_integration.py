"""Integration tests for Reaper export workflow."""

import pytest

from midi_drums import DrumGenerator
from midi_drums.engines.reaper_engine import ReaperEngine
from midi_drums.exporters import ReaperExporter


class TestReaperExportWorkflow:
    """Test complete Reaper export workflows."""

    def test_full_export_workflow_minimal(self, tmp_path):
        """Test complete workflow: Generate song → Export to Reaper."""
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
