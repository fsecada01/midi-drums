"""Tests for intelligent ride/hi-hat switching (issue #1).

Real drummers use hi-hat for lower-energy sections (verse, intro) and
switch to ride cymbal for higher-energy sections (chorus, bridge), adding
a hi-hat foot pedal ("chick" on beats 2 and 4) once riding. This module
covers GenrePlugin._apply_ride_hihat_logic and its wiring into the four
genre plugins named in issue #1: metal, rock, jazz, funk.
"""

import pytest

from midi_drums.core.models.pattern import Pattern
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.core.value_objects.time_signature import TimeSignature
from midi_drums.generation.builders.pattern_builder import PatternBuilder
from midi_drums.plugins.genres.funk_refactored import FunkGenrePlugin
from midi_drums.plugins.genres.jazz_refactored import JazzGenrePlugin
from midi_drums.plugins.genres.metal_refactored import MetalGenrePlugin
from midi_drums.plugins.genres.rock_refactored import RockGenrePlugin
from midi_drums.plugins.interfaces.genre_plugin import GenrePlugin

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


class _StubGenrePlugin(GenrePlugin):
    """Minimal concrete GenrePlugin for testing _apply_ride_hihat_logic
    in isolation from any genre's actual pattern generation.
    """

    @property
    def genre_name(self) -> str:
        return "stub"

    @property
    def supported_styles(self) -> list[str]:
        return ["default"]

    def generate_pattern(self, section, parameters):
        raise NotImplementedError

    def get_common_fills(self):
        return []


class _CrashTimekeeperPlugin(_StubGenrePlugin):
    """Stub that overrides the high-energy timekeeper extension point."""

    def _high_energy_timekeeper(self, section, parameters):
        return DrumInstrument.CRASH


@pytest.mark.unit
class TestApplyRideHihatLogicEdgeCases:
    """Direct tests of GenrePlugin._apply_ride_hihat_logic edge cases
    found during adversarial review of #1's implementation: hardcoded
    4/4 pedal placement and truncation of partial trailing bars.
    """

    def test_pedal_positions_respect_non_4_4_time_signature(self):
        pattern = Pattern(name="waltz", time_signature=TimeSignature(3, 4))
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH)
        pattern.add_beat(1.0, DrumInstrument.CLOSED_HH)
        pattern.add_beat(2.0, DrumInstrument.CLOSED_HH)

        plugin = _StubGenrePlugin()
        params = GenerationParameters(genre="stub")
        result = plugin._apply_ride_hihat_logic(pattern, "chorus", params)

        pedal_positions = sorted(
            beat.position
            for beat in result.beats
            if beat.instrument == DrumInstrument.PEDAL_HH
        )
        # A 3/4 bar has beats 0, 1, 2 - only position 1.0 is a valid
        # backbeat-equivalent; there is no "beat 4" to place a second
        # pedal hit at within the bar.
        assert pedal_positions == [1.0]

    def test_pedal_added_in_partial_trailing_bar(self):
        pattern = Pattern(name="partial")
        for pos in (0.0, 1.0, 4.0, 5.0, 6.5):
            pattern.add_beat(pos, DrumInstrument.CLOSED_HH)

        plugin = _StubGenrePlugin()
        params = GenerationParameters(genre="stub")
        result = plugin._apply_ride_hihat_logic(pattern, "chorus", params)

        pedal_positions = {
            beat.position
            for beat in result.beats
            if beat.instrument == DrumInstrument.PEDAL_HH
        }
        # duration_bars() is 1.875 (not an integer) - the pedal must
        # still land in the partial second bar (positions 5.0/7.0),
        # not just the first complete bar.
        assert {1.0, 3.0, 5.0}.issubset(pedal_positions)

    def test_high_energy_timekeeper_extension_point_is_used(self):
        pattern = Pattern(name="test")
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH)

        plugin = _CrashTimekeeperPlugin()
        params = GenerationParameters(genre="stub")
        result = plugin._apply_ride_hihat_logic(pattern, "chorus", params)

        instruments = _instruments(result)
        assert DrumInstrument.CRASH in instruments
        assert DrumInstrument.RIDE not in instruments

    def test_default_high_energy_timekeeper_is_ride(self):
        plugin = _StubGenrePlugin()
        params = GenerationParameters(genre="stub")
        assert (
            plugin._high_energy_timekeeper("chorus", params)
            == DrumInstrument.RIDE
        )


@pytest.mark.unit
class TestGenreSpecificHighEnergyTimekeeper:
    """Genre-aware timekeeper selection (issue #18): rock's hard/punk
    styles and metal's thrash/death styles override the RIDE default,
    per crash-riding (rock) and china-as-ride-substitute (metal)
    conventions documented in issue #18's research comment.
    """

    @pytest.mark.parametrize("style", ["hard", "punk"])
    def test_rock_high_energy_styles_use_crash(self, style):
        plugin = RockGenrePlugin()
        params = GenerationParameters(genre="rock", style=style, complexity=0.5)
        assert (
            plugin._high_energy_timekeeper("chorus", params)
            == DrumInstrument.CRASH
        )

    @pytest.mark.parametrize(
        "style", ["classic", "blues", "alternative", "progressive", "pop"]
    )
    def test_rock_other_styles_default_to_ride(self, style):
        plugin = RockGenrePlugin()
        params = GenerationParameters(genre="rock", style=style, complexity=0.5)
        assert (
            plugin._high_energy_timekeeper("chorus", params)
            == DrumInstrument.RIDE
        )

    @pytest.mark.parametrize("style", ["thrash", "death"])
    def test_metal_high_energy_styles_use_china(self, style):
        plugin = MetalGenrePlugin()
        params = GenerationParameters(
            genre="metal", style=style, complexity=0.5
        )
        assert (
            plugin._high_energy_timekeeper("chorus", params)
            == DrumInstrument.CHINA
        )

    @pytest.mark.parametrize(
        "style", ["heavy", "power", "progressive", "doom", "breakdown"]
    )
    def test_metal_other_styles_default_to_ride(self, style):
        plugin = MetalGenrePlugin()
        params = GenerationParameters(
            genre="metal", style=style, complexity=0.5
        )
        assert (
            plugin._high_energy_timekeeper("chorus", params)
            == DrumInstrument.RIDE
        )

    def test_rock_hard_style_promotes_hihat_to_crash_via_full_pipeline(self):
        plugin = RockGenrePlugin()
        params = GenerationParameters(
            genre="rock", style="hard", complexity=0.5
        )
        pattern = Pattern(name="test")
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH)

        result = plugin._apply_ride_hihat_logic(pattern, "chorus", params)

        instruments = _instruments(result)
        assert DrumInstrument.CRASH in instruments
        assert DrumInstrument.RIDE not in instruments

    def test_metal_death_style_promotes_hihat_to_china_via_full_pipeline(self):
        plugin = MetalGenrePlugin()
        params = GenerationParameters(
            genre="metal", style="death", complexity=0.5
        )
        pattern = Pattern(name="test")
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH)

        result = plugin._apply_ride_hihat_logic(pattern, "chorus", params)

        instruments = _instruments(result)
        assert DrumInstrument.CHINA in instruments
        assert DrumInstrument.RIDE not in instruments
