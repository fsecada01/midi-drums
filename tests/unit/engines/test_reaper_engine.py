"""Unit tests for Reaper engine."""

import pytest
import rpp

from midi_drums.engines.reaper_engine import ReaperEngine, bars_to_seconds
from midi_drums.models.reaper_models import Marker
from midi_drums.models.song import Pattern, Section, Song, TimeSignature


class TestBarsToSeconds:
    """Test bars to seconds time conversion."""

    def test_basic_conversion_4_4_time(self):
        """Test 4/4 time signature conversion."""
        # 4 bars @ 120 BPM (4/4) = 8 seconds
        result = bars_to_seconds(4, 120, TimeSignature(4, 4))
        assert result == 8.0

    def test_8_bars_conversion(self):
        """Test 8 bars conversion."""
        # 8 bars @ 120 BPM (4/4) = 16 seconds
        result = bars_to_seconds(8, 120, TimeSignature(4, 4))
        assert result == 16.0

    def test_fast_tempo(self):
        """Test conversion at fast tempo."""
        # 4 bars @ 180 BPM (4/4) ≈ 5.33 seconds
        result = bars_to_seconds(4, 180, TimeSignature(4, 4))
        assert abs(result - 5.333333) < 0.0001

    def test_3_4_time_signature(self):
        """Test 3/4 time signature."""
        # 4 bars @ 120 BPM (3/4) = 6 seconds
        # (4 bars * 3 beats/bar / 120 BPM * 60 = 6)
        result = bars_to_seconds(4, 120, TimeSignature(3, 4))
        assert result == 6.0

    def test_zero_bars(self):
        """Test zero bars returns 0 seconds."""
        result = bars_to_seconds(0, 120, TimeSignature(4, 4))
        assert result == 0.0

    def test_negative_bars_raises_error(self):
        """Test negative bars raises ValueError."""
        with pytest.raises(ValueError, match="must be non-negative"):
            bars_to_seconds(-1, 120, TimeSignature(4, 4))

    def test_zero_tempo_raises_error(self):
        """Test zero tempo raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            bars_to_seconds(4, 0, TimeSignature(4, 4))

    def test_negative_tempo_raises_error(self):
        """Test negative tempo raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            bars_to_seconds(4, -120, TimeSignature(4, 4))


class TestReaperEngine:
    """Test ReaperEngine class."""

    def test_initialization(self):
        """Test engine initializes with default tempo."""
        engine = ReaperEngine()
        assert engine.default_tempo == 120

    def test_initialization_custom_tempo(self):
        """Test engine with custom default tempo."""
        engine = ReaperEngine(default_tempo=140)
        assert engine.default_tempo == 140

    def test_create_minimal_project(self):
        """Test creating minimal project structure."""
        engine = ReaperEngine()
        project = engine.create_minimal_project()

        assert project.tag == "REAPER_PROJECT"
        assert isinstance(project, rpp.Element)

        # Check for basic project elements
        children = list(project)
        assert any(c[0] == "TEMPO" for c in children if isinstance(c, list))

    def test_create_minimal_project_custom_tempo(self):
        """Test project creation with custom tempo."""
        engine = ReaperEngine()
        project = engine.create_minimal_project(tempo=180)

        tempo_elem = next(
            c for c in project if isinstance(c, list) and c[0] == "TEMPO"
        )
        assert tempo_elem[1] == "180"

    def test_create_minimal_project_custom_time_signature(self):
        """Test project with custom time signature."""
        engine = ReaperEngine()
        project = engine.create_minimal_project(
            time_signature=TimeSignature(3, 4)
        )

        tempo_elem = next(
            c for c in project if isinstance(c, list) and c[0] == "TEMPO"
        )
        assert tempo_elem[2] == "3"  # numerator
        assert tempo_elem[3] == "4"  # denominator

    def test_add_single_marker(self):
        """Test adding single marker to project."""
        engine = ReaperEngine()
        project = engine.create_minimal_project()

        marker = Marker(0.0, "Intro", marker_id=1)
        engine.add_markers(project, [marker])

        markers = [
            c for c in project if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert len(markers) == 1
        assert markers[0][3] == "Intro"  # name

    def test_add_multiple_markers(self):
        """Test adding multiple markers."""
        engine = ReaperEngine()
        project = engine.create_minimal_project()

        markers = [
            Marker(0.0, "Intro", marker_id=1),
            Marker(8.0, "Verse", marker_id=2),
            Marker(24.0, "Chorus", marker_id=3),
        ]
        engine.add_markers(project, markers)

        project_markers = [
            c for c in project if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert len(project_markers) == 3

    def test_marker_auto_id_assignment(self):
        """Test markers get auto-assigned IDs if not provided."""
        engine = ReaperEngine()
        project = engine.create_minimal_project()

        # Markers without IDs
        markers = [
            Marker(0.0, "Intro"),
            Marker(8.0, "Verse"),
        ]
        engine.add_markers(project, markers)

        assert markers[0].marker_id == 1
        assert markers[1].marker_id == 2

    def test_save_and_load_project(self, tmp_path):
        """Test saving and loading project."""
        engine = ReaperEngine()
        project = engine.create_minimal_project()

        marker = Marker(0.0, "Test", marker_id=1)
        engine.add_markers(project, [marker])

        # Save
        output_path = tmp_path / "test.rpp"
        engine.save_project(project, str(output_path))

        # Verify file exists
        assert output_path.exists()

        # Load back
        loaded_project = engine.load_project(str(output_path))
        assert loaded_project.tag == "REAPER_PROJECT"

        # Verify marker survived round-trip
        markers = [
            c
            for c in loaded_project
            if isinstance(c, list) and c[0] == "MARKER"
        ]
        assert len(markers) == 1
        assert markers[0][3] == "Test"

    def test_load_nonexistent_project_raises_error(self):
        """Test loading non-existent file raises FileNotFoundError."""
        engine = ReaperEngine()
        with pytest.raises(FileNotFoundError):
            engine.load_project("nonexistent.rpp")

    def test_calculate_marker_positions_from_song(self):
        """Test calculating marker positions from Song."""
        engine = ReaperEngine()

        # Create test song
        song = Song(
            name="Test",
            tempo=120,
            time_signature=TimeSignature(4, 4),
            sections=[
                Section(
                    name="intro",
                    bars=4,
                    pattern=Pattern("intro_pattern"),
                ),
                Section(
                    name="verse",
                    bars=8,
                    pattern=Pattern("verse_pattern"),
                ),
                Section(
                    name="chorus",
                    bars=8,
                    pattern=Pattern("chorus_pattern"),
                ),
            ],
        )

        markers = engine.calculate_marker_positions_from_song(song)

        assert len(markers) == 3
        assert markers[0].name == "intro"
        assert markers[0].position_seconds == 0.0
        assert markers[1].name == "verse"
        assert markers[1].position_seconds == 8.0  # 4 bars @ 120 BPM
        assert markers[2].name == "chorus"
        assert markers[2].position_seconds == 24.0  # 12 bars @ 120 BPM

    def test_calculate_positions_assigns_marker_ids(self):
        """Test marker IDs are auto-assigned sequentially."""
        engine = ReaperEngine()

        song = Song(
            name="Test",
            tempo=120,
            sections=[
                Section(name="intro", bars=4, pattern=Pattern("p1")),
                Section(name="verse", bars=8, pattern=Pattern("p2")),
            ],
        )

        markers = engine.calculate_marker_positions_from_song(song)

        assert markers[0].marker_id == 1
        assert markers[1].marker_id == 2
