"""Tests for the Electronic genre plugin (issue #30).

Covers house, techno, drum_and_bass, and dubstep pattern generation via
ElectronicGenrePlugin, mirroring the structure and @pytest.mark.unit
conventions of tests/unit/test_ride_hihat_switching.py.
"""

import pytest

from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.plugins.genres.electronic import ElectronicGenrePlugin

SECTIONS = ["intro", "verse", "chorus", "breakdown", "bridge", "outro"]


def _kick_positions(pattern):
    return {
        b.position for b in pattern.beats if b.instrument == DrumInstrument.KICK
    }


def _snare_positions(pattern):
    return {
        b.position
        for b in pattern.beats
        if b.instrument == DrumInstrument.SNARE
    }


def _hihat_count(pattern):
    return sum(
        1
        for b in pattern.beats
        if b.instrument in {DrumInstrument.CLOSED_HH, DrumInstrument.OPEN_HH}
    )


@pytest.mark.unit
class TestElectronicBasicStructure:
    def test_genre_name(self):
        plugin = ElectronicGenrePlugin()
        assert plugin.genre_name == "electronic"

    def test_supports_at_least_three_styles(self):
        plugin = ElectronicGenrePlugin()
        assert len(plugin.supported_styles) >= 3
        for required in ("house", "techno", "drum_and_bass"):
            assert required in plugin.supported_styles

    def test_intensity_profile_has_expected_dimensions(self):
        plugin = ElectronicGenrePlugin()
        profile = plugin.intensity_profile
        for key in (
            "aggression",
            "speed",
            "density",
            "power",
            "complexity",
            "darkness",
        ):
            assert key in profile
            assert 0.0 <= profile[key] <= 1.0


@pytest.mark.unit
class TestElectronicAllCombinations:
    def test_every_style_and_section_produces_beats(self):
        plugin = ElectronicGenrePlugin()
        count = 0
        for style in plugin.supported_styles:
            for section in SECTIONS:
                params = GenerationParameters(
                    genre="electronic",
                    style=style,
                    complexity=0.7,
                    humanization=0.3,
                )
                pattern = plugin.generate_pattern(section, params)
                assert pattern is not None
                assert len(pattern.beats) > 0
                count += 1
        assert count == len(plugin.supported_styles) * len(SECTIONS)


@pytest.mark.unit
class TestHouseStyle:
    def test_four_on_the_floor_kick(self):
        plugin = ElectronicGenrePlugin()
        params = GenerationParameters(
            genre="electronic", style="house", complexity=0.6, humanization=0.2
        )
        verse = plugin.generate_pattern("verse", params)

        kicks = _kick_positions(verse)
        assert {0.0, 1.0, 2.0, 3.0}.issubset(kicks)

    def test_backbeat_snare(self):
        plugin = ElectronicGenrePlugin()
        params = GenerationParameters(
            genre="electronic", style="house", complexity=0.6, humanization=0.2
        )
        verse = plugin.generate_pattern("verse", params)

        snares = _snare_positions(verse)
        assert 1.0 in snares
        assert 3.0 in snares


@pytest.mark.unit
class TestTechnoStyle:
    def test_four_on_the_floor_kick(self):
        plugin = ElectronicGenrePlugin()
        params = GenerationParameters(
            genre="electronic",
            style="techno",
            complexity=0.6,
            humanization=0.2,
        )
        verse = plugin.generate_pattern("verse", params)

        kicks = _kick_positions(verse)
        assert {0.0, 1.0, 2.0, 3.0}.issubset(kicks)

    def test_minimal_snare_versus_house(self):
        plugin = ElectronicGenrePlugin()
        house_params = GenerationParameters(
            genre="electronic", style="house", complexity=0.6, humanization=0.2
        )
        techno_params = GenerationParameters(
            genre="electronic",
            style="techno",
            complexity=0.6,
            humanization=0.2,
        )

        house_verse = plugin.generate_pattern("verse", house_params)
        techno_verse = plugin.generate_pattern("verse", techno_params)

        house_snare_count = len(_snare_positions(house_verse))
        techno_snare_count = len(_snare_positions(techno_verse))

        assert techno_snare_count <= house_snare_count

    def test_driving_mechanical_hihat_density(self):
        plugin = ElectronicGenrePlugin()
        params = GenerationParameters(
            genre="electronic",
            style="techno",
            complexity=0.6,
            humanization=0.2,
        )
        verse = plugin.generate_pattern("verse", params)

        # Mechanical/driving techno should have dense (16th-note-scale)
        # hihat activity - more than a handful of hits per bar.
        assert _hihat_count(verse) >= 8


@pytest.mark.unit
class TestDrumAndBassStyle:
    def test_syncopated_snare_not_on_standard_backbeat_only(self):
        plugin = ElectronicGenrePlugin()
        params = GenerationParameters(
            genre="electronic",
            style="drum_and_bass",
            complexity=0.6,
            humanization=0.2,
        )
        verse = plugin.generate_pattern("verse", params)

        snares = _snare_positions(verse)
        # Syncopated placement means at least one snare hit falls off the
        # standard quarter-note backbeat grid (1.0, 3.0).
        assert any(pos not in {1.0, 3.0} for pos in snares)

    def test_fast_breakbeat_kick_pattern(self):
        plugin = ElectronicGenrePlugin()
        params = GenerationParameters(
            genre="electronic",
            style="drum_and_bass",
            complexity=0.6,
            humanization=0.2,
        )
        verse = plugin.generate_pattern("verse", params)

        kicks = _kick_positions(verse)
        # Breakbeat kicks are syncopated, not the plain four-on-the-floor
        # grid used by house/techno.
        assert kicks != {0.0, 1.0, 2.0, 3.0}
        assert len(kicks) >= 2


@pytest.mark.unit
class TestDubstepStyle:
    def test_half_time_sparse_snare(self):
        plugin = ElectronicGenrePlugin()
        params = GenerationParameters(
            genre="electronic",
            style="dubstep",
            complexity=0.6,
            humanization=0.2,
        )
        verse = plugin.generate_pattern("verse", params)

        snares = _snare_positions(verse)
        # Half-time feel: a single heavy snare hit (typically on beat 3),
        # not the two-and-four backbeat used by house/techno.
        assert len(snares) == 1
        assert 2.0 in snares

    def test_sparse_kick(self):
        plugin = ElectronicGenrePlugin()
        params = GenerationParameters(
            genre="electronic",
            style="dubstep",
            complexity=0.6,
            humanization=0.2,
        )
        verse = plugin.generate_pattern("verse", params)

        kicks = _kick_positions(verse)
        assert kicks != {0.0, 1.0, 2.0, 3.0}

    def test_bridge_keeps_half_time_feel(self):
        # Every other dubstep section branches away from the house/techno
        # four-on-the-floor groove; the bridge generator must too.
        plugin = ElectronicGenrePlugin()
        params = GenerationParameters(
            genre="electronic",
            style="dubstep",
            complexity=0.6,
            humanization=0.2,
        )
        bridge = plugin.generate_pattern("bridge", params)

        kicks = _kick_positions(bridge)
        assert kicks != {0.0, 1.0, 2.0, 3.0}


@pytest.mark.unit
class TestElectronicFills:
    def test_common_fills_are_non_empty(self):
        plugin = ElectronicGenrePlugin()
        fills = plugin.get_common_fills()

        assert len(fills) >= 2
        for fill in fills:
            assert fill.pattern is not None
            assert len(fill.pattern.beats) > 0
