"""Tests for intelligent ride/hi-hat switching (issue #1).

Real drummers use hi-hat for lower-energy sections (verse, intro) and
switch to ride cymbal for higher-energy sections (chorus, bridge), adding
a hi-hat foot pedal ("chick" on beats 2 and 4) once riding. This module
covers GenrePlugin._apply_ride_hihat_logic and its wiring into the four
genre plugins named in issue #1: metal, rock, jazz, funk.
"""

import pytest

from midi_drums.models.pattern import DrumInstrument, PatternBuilder
from midi_drums.models.song import GenerationParameters
from midi_drums.plugins.genres.funk_refactored import FunkGenrePlugin
from midi_drums.plugins.genres.jazz_refactored import JazzGenrePlugin
from midi_drums.plugins.genres.metal_refactored import MetalGenrePlugin
from midi_drums.plugins.genres.rock_refactored import RockGenrePlugin

HIHAT_INSTRUMENTS = {DrumInstrument.CLOSED_HH, DrumInstrument.OPEN_HH}

# Genres/styles whose verse and chorus patterns use hi-hat exclusively for
# timekeeping at baseline (no genre-authentic ride usage to preserve).
HIHAT_BASELINE_GENRES = [
    (MetalGenrePlugin, "heavy"),
    (RockGenrePlugin, "classic"),
    (FunkGenrePlugin, "classic"),
]

ALL_GENRES = HIHAT_BASELINE_GENRES + [(JazzGenrePlugin, "swing")]


def _instruments(pattern):
    return {beat.instrument for beat in pattern.beats}


@pytest.mark.unit
class TestGenerationParametersRideThreshold:
    def test_default_ride_threshold_is_in_valid_range(self):
        params = GenerationParameters(genre="rock")
        assert 0.0 <= params.ride_threshold <= 1.0

    def test_ride_threshold_rejects_out_of_range_values(self):
        with pytest.raises(ValueError):
            GenerationParameters(genre="rock", ride_threshold=1.5)


@pytest.mark.unit
class TestPatternBuilderHihatFoot:
    def test_hihat_foot_adds_pedal_hh_beat(self):
        pattern = PatternBuilder("test").hihat_foot(1.0).build()

        assert len(pattern.beats) == 1
        assert pattern.beats[0].instrument == DrumInstrument.PEDAL_HH
        assert pattern.beats[0].position == 1.0


@pytest.mark.unit
@pytest.mark.parametrize("plugin_cls,style", HIHAT_BASELINE_GENRES)
class TestHihatToRideSwitching:
    """Genres whose verse patterns use hi-hat exclusively at baseline."""

    def test_verse_uses_hihat_timekeeping(self, plugin_cls, style):
        plugin = plugin_cls()
        params = GenerationParameters(
            genre=plugin.genre_name, style=style, complexity=0.5
        )
        pattern = plugin.generate_pattern("verse", params)
        instruments = _instruments(pattern)

        assert DrumInstrument.RIDE not in instruments
        assert instruments & HIHAT_INSTRUMENTS

    def test_chorus_uses_ride_timekeeping(self, plugin_cls, style):
        plugin = plugin_cls()
        params = GenerationParameters(
            genre=plugin.genre_name, style=style, complexity=0.5
        )
        pattern = plugin.generate_pattern("chorus", params)
        instruments = _instruments(pattern)

        assert DrumInstrument.RIDE in instruments
        assert not (instruments & HIHAT_INSTRUMENTS)

    def test_hihat_foot_pedal_added_when_riding(self, plugin_cls, style):
        plugin = plugin_cls()
        params = GenerationParameters(
            genre=plugin.genre_name, style=style, complexity=0.5
        )
        pattern = plugin.generate_pattern("chorus", params)
        pedal_beats = [
            beat
            for beat in pattern.beats
            if beat.instrument == DrumInstrument.PEDAL_HH
        ]

        assert pedal_beats
        # Pedal chick lands on beats 2 and 4 of each bar.
        assert all(beat.position % 2.0 == 1.0 for beat in pedal_beats)

    def test_energy_threshold_switching(self, plugin_cls, style):
        plugin = plugin_cls()

        low_threshold = GenerationParameters(
            genre=plugin.genre_name,
            style=style,
            complexity=0.5,
            ride_threshold=0.1,
        )
        forced_ride = plugin.generate_pattern("verse", low_threshold)
        assert DrumInstrument.RIDE in _instruments(forced_ride)

        high_threshold = GenerationParameters(
            genre=plugin.genre_name,
            style=style,
            complexity=0.5,
            ride_threshold=0.95,
        )
        stays_hihat = plugin.generate_pattern("verse", high_threshold)
        assert DrumInstrument.RIDE not in _instruments(stays_hihat)


@pytest.mark.unit
def test_jazz_verse_already_riding_is_left_untouched():
    """Jazz's swing verse already rides via JazzRidePattern - the shared
    switching logic must not force it onto hi-hat. It only ever promotes
    hi-hat to ride, never the reverse.
    """
    plugin = JazzGenrePlugin()
    params = GenerationParameters(genre="jazz", style="swing", complexity=0.5)
    pattern = plugin.generate_pattern("verse", params)

    assert DrumInstrument.RIDE in _instruments(pattern)


@pytest.mark.unit
@pytest.mark.parametrize("plugin_cls,style", ALL_GENRES)
def test_all_genres_chorus_uses_ride(plugin_cls, style):
    """Test Coverage: 'All genres behave correctly.'"""
    plugin = plugin_cls()
    params = GenerationParameters(
        genre=plugin.genre_name, style=style, complexity=0.5
    )
    pattern = plugin.generate_pattern("chorus", params)

    assert DrumInstrument.RIDE in _instruments(pattern)
