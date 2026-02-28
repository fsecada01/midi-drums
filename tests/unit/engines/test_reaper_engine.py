"""Unit tests for Reaper engine."""

from __future__ import annotations

import pytest
import rpp

from midi_drums.engines.reaper_engine import ReaperEngine, bars_to_seconds
from midi_drums.models.reaper_models import (
    GENRE_STRUCTURE_PRESETS,
    GenreStructurePreset,
    Marker,
    get_genre_preset,
    get_section_color,
    list_genre_presets,
)
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

    def test_calculate_marker_positions_uses_section_colors(self):
        """Markers produced from a song carry per-section colors."""
        engine = ReaperEngine()

        song = Song(
            name="Colored",
            tempo=120,
            sections=[
                Section(name="verse", bars=4, pattern=Pattern("p1")),
                Section(name="chorus", bars=4, pattern=Pattern("p2")),
            ],
        )

        markers = engine.calculate_marker_positions_from_song(song)

        assert markers[0].color == get_section_color("verse")
        assert markers[1].color == get_section_color("chorus")
        # Verse and chorus should have distinct colors
        assert markers[0].color != markers[1].color


class TestReaperEngineGenrePreset:
    """Test genre-preset methods on ReaperEngine."""

    def test_get_genre_preset_exact_match(self):
        """Engine returns exact preset for known genre/style."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("metal", "heavy")
        assert isinstance(preset, GenreStructurePreset)
        assert preset.genre == "metal"
        assert preset.style == "heavy"

    def test_get_genre_preset_fallback(self):
        """Engine returns a fallback preset for unknown genre/style."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("orchestral", "romantic")
        assert isinstance(preset, GenreStructurePreset)

    def test_get_genre_preset_case_insensitive(self):
        """Genre/style look-up is case-insensitive."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("METAL", "HEAVY")
        assert preset.genre == "metal"
        assert preset.style == "heavy"

    def test_create_song_from_preset_returns_song(self):
        """create_song_from_preset returns a valid Song."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("metal", "doom")
        song = engine.create_song_from_preset(preset)

        assert isinstance(song, Song)
        assert len(song.sections) == len(preset.sections)

    def test_create_song_from_preset_uses_preset_tempo(self):
        """Song uses preset default_tempo when none is given."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("metal", "doom")
        song = engine.create_song_from_preset(preset)

        assert song.tempo == preset.default_tempo

    def test_create_song_from_preset_respects_override_tempo(self):
        """Explicit tempo overrides preset default."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("jazz", "swing")
        song = engine.create_song_from_preset(preset, tempo=180)

        assert song.tempo == 180

    def test_create_song_from_preset_sets_time_signature(self):
        """Song time signature matches preset."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("jazz", "swing")
        song = engine.create_song_from_preset(preset)

        num, den = preset.time_signature
        assert song.time_signature.numerator == num
        assert song.time_signature.denominator == den

    def test_create_song_from_preset_section_names(self):
        """Section names in the created Song match the preset."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("rock", "classic")
        song = engine.create_song_from_preset(preset)

        preset_names = [s.name for s in preset.sections]
        song_names = [s.name for s in song.sections]
        assert song_names == preset_names

    def test_create_song_from_preset_has_genre_metadata(self):
        """Song metadata includes genre and style from preset."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("funk", "classic")
        song = engine.create_song_from_preset(preset, name="Funk Test")

        assert song.metadata.get("genre") == "funk"
        assert song.metadata.get("style") == "classic"
        assert song.name == "Funk Test"

    def test_calculate_marker_positions_from_preset_count(self):
        """One marker per section in the preset."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("metal", "heavy")
        markers = engine.calculate_marker_positions_from_preset(
            preset, tempo=155
        )

        assert len(markers) == len(preset.sections)

    def test_calculate_marker_positions_from_preset_first_is_zero(self):
        """First marker is always at position 0.0 seconds."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("metal", "death")
        markers = engine.calculate_marker_positions_from_preset(
            preset, tempo=200
        )

        assert markers[0].position_seconds == 0.0

    def test_calculate_marker_positions_from_preset_ascending_order(self):
        """Markers are in ascending time order."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("jazz", "swing")
        markers = engine.calculate_marker_positions_from_preset(
            preset, tempo=160
        )

        positions = [m.position_seconds for m in markers]
        assert positions == sorted(positions)

    def test_calculate_marker_positions_from_preset_uses_labels(self):
        """Marker names are the section labels (e.g. 'Verse 1' not 'verse')."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("rock", "classic")
        markers = engine.calculate_marker_positions_from_preset(
            preset, tempo=140
        )

        marker_names = {m.name for m in markers}
        # Labels are human-readable; at least one should have a space or capital
        assert any(n[0].isupper() or " " in n for n in marker_names)

    def test_calculate_marker_positions_from_preset_colors_match_theme(self):
        """Marker colors come from the preset's marker theme."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("metal", "doom")
        markers = engine.calculate_marker_positions_from_preset(
            preset, tempo=70
        )

        for marker, section_tmpl in zip(markers, preset.sections, strict=False):
            expected_color = preset.section_color(section_tmpl.name)
            assert marker.color == expected_color

    def test_calculate_marker_positions_from_preset_invalid_tempo(self):
        """Negative tempo raises ValueError."""
        engine = ReaperEngine()
        preset = engine.get_genre_preset("metal", "heavy")
        with pytest.raises(ValueError, match="must be positive"):
            engine.calculate_marker_positions_from_preset(preset, tempo=-1)

    def test_calculate_marker_positions_accuracy(self):
        """Marker positions are mathematically accurate."""
        engine = ReaperEngine()
        # Use a simple preset-like structure: intro (4 bars) then verse (8 bars)
        # At 120 BPM 4/4: intro ends at 8s, verse ends at 24s
        preset = engine.get_genre_preset("metal", "heavy")
        markers = engine.calculate_marker_positions_from_preset(
            preset, tempo=120, time_sig=(4, 4)
        )

        # First marker at 0s
        assert markers[0].position_seconds == 0.0
        # Second marker: after intro (4 bars @ 120 BPM 4/4 = 8s)
        intro_bars = preset.sections[0].bars
        expected_second = bars_to_seconds(intro_bars, 120, TimeSignature(4, 4))
        assert abs(markers[1].position_seconds - expected_second) < 0.0001


class TestSectionColors:
    """Test the section color registry helpers."""

    def test_known_section_types_return_non_default(self):
        """Well-known section types return specific colors."""
        known_types = [
            "verse",
            "chorus",
            "intro",
            "outro",
            "bridge",
            "solo",
            "breakdown",
            "blast_section",
            "head",
            "groove",
        ]
        default = "#FF5733"
        for section_type in known_types:
            color = get_section_color(section_type)
            assert isinstance(color, str)
            assert color.startswith("#")
            assert (
                color != default
            ), f"Section '{section_type}' should have a dedicated color"

    def test_unknown_section_returns_default(self):
        """Unknown section types fall back to the default color."""
        from midi_drums.models.reaper_models import DEFAULT_SECTION_COLOR

        color = get_section_color("xyzzy_unknown")
        assert color == DEFAULT_SECTION_COLOR

    def test_case_insensitive_lookup(self):
        """Color look-up is case-insensitive."""
        assert get_section_color("VERSE") == get_section_color("verse")
        assert get_section_color("Chorus") == get_section_color("chorus")


class TestGenreStructurePreset:
    """Test GenreStructurePreset model."""

    def test_default_tempo_is_midpoint(self):
        """default_tempo property returns midpoint of tempo_range."""
        preset = GENRE_STRUCTURE_PRESETS[("metal", "heavy")]
        lo, hi = preset.tempo_range
        assert preset.default_tempo == (lo + hi) // 2

    def test_section_color_uses_theme(self):
        """section_color respects marker_theme overrides."""
        preset = GENRE_STRUCTURE_PRESETS[("metal", "doom")]
        # The doom preset has a custom theme for "verse"
        color = preset.section_color("verse")
        assert color == preset.marker_theme.get(
            "verse", get_section_color("verse")
        )

    def test_section_color_falls_back_to_registry(self):
        """section_color falls back to get_section_color for unmapped types."""
        preset = GENRE_STRUCTURE_PRESETS[("jazz", "swing")]
        # "breakdown" is not in jazz/swing theme
        color = preset.section_color("breakdown")
        assert color == get_section_color("breakdown")

    def test_presets_are_frozen(self):
        """Presets cannot be mutated."""
        import dataclasses

        preset = GENRE_STRUCTURE_PRESETS[("metal", "heavy")]
        with pytest.raises(dataclasses.FrozenInstanceError):
            preset.genre = "rock"  # type: ignore[misc]

    def test_sections_are_frozen(self):
        """SectionTemplate cannot be mutated."""
        import dataclasses

        preset = GENRE_STRUCTURE_PRESETS[("metal", "heavy")]
        section = preset.sections[0]
        with pytest.raises(dataclasses.FrozenInstanceError):
            section.bars = 99  # type: ignore[misc]


class TestListGenrePresets:
    """Test list_genre_presets registry helper."""

    def test_returns_dict(self):
        """Result is a dict."""
        result = list_genre_presets()
        assert isinstance(result, dict)

    def test_contains_expected_genres(self):
        """Expected genres are present."""
        result = list_genre_presets()
        for genre in ("metal", "rock", "jazz", "funk"):
            assert genre in result

    def test_styles_are_sorted(self):
        """Styles within each genre are alphabetically sorted."""
        result = list_genre_presets()
        for genre, styles in result.items():
            assert styles == sorted(
                styles
            ), f"Styles for '{genre}' are not sorted"

    def test_metal_has_expected_styles(self):
        """Metal genre includes all defined styles."""
        result = list_genre_presets()
        expected = {
            "heavy",
            "death",
            "doom",
            "thrash",
            "power",
            "progressive",
            "breakdown",
        }
        assert expected.issubset(set(result["metal"]))


class TestGetGenrePreset:
    """Test get_genre_preset look-up function."""

    def test_exact_match_metal_heavy(self):
        preset = get_genre_preset("metal", "heavy")
        assert preset.genre == "metal"
        assert preset.style == "heavy"

    def test_exact_match_jazz_swing(self):
        preset = get_genre_preset("jazz", "swing")
        assert preset.genre == "jazz"
        assert preset.style == "swing"

    def test_wildcard_returns_a_preset(self):
        """Wildcard style returns any preset for the genre."""
        preset = get_genre_preset("metal", "*")
        assert preset.genre == "metal"

    def test_unknown_genre_returns_fallback(self):
        """Completely unknown genre returns a generic fallback."""
        preset = get_genre_preset("unknown_genre", "unknown_style")
        assert isinstance(preset, GenreStructurePreset)
        assert len(preset.sections) > 0

    def test_case_insensitive(self):
        """Look-up is case-insensitive."""
        p1 = get_genre_preset("Metal", "Heavy")
        p2 = get_genre_preset("metal", "heavy")
        assert p1.genre == p2.genre
        assert p1.style == p2.style
