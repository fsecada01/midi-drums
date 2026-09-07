"""Tests for the drummer_intensity blend knob.

Covers the mix-knob feature added so a drummer's signature style can be
dialed back relative to the genre plugin's own pattern (e.g. a subtle
Porcaro feel over a Death Metal pattern, rather than Porcaro fully
overriding it) - see GenerationParameters.drummer_intensity,
DrummerPlugin.apply_style's intensity parameter, and
PluginManager.apply_drummer_style.
"""

import random

import pytest

from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.generation.builders.pattern_builder import PatternBuilder
from midi_drums.plugins.drummers.porcaro import PorcaroPlugin
from midi_drums.plugins.registry.plugin_registry import PluginManager


def _make_pattern():
    builder = PatternBuilder("test_pattern")
    builder.kick(0.0, 100).kick(2.0, 100)
    builder.snare(1.0, 110).snare(3.0, 110)
    for i in range(8):
        builder.hihat(i * 0.5, 80)
    return builder.build()


class TestGenerationParametersDrummerIntensity:
    def test_defaults_to_full_intensity(self):
        params = GenerationParameters(genre="metal")
        assert params.drummer_intensity == 1.0

    @pytest.mark.parametrize("value", [-0.01, 1.01, -1.0, 2.0])
    def test_out_of_range_raises(self, value):
        with pytest.raises(ValueError, match="drummer_intensity"):
            GenerationParameters(genre="metal", drummer_intensity=value)

    @pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
    def test_in_range_accepted(self, value):
        params = GenerationParameters(genre="metal", drummer_intensity=value)
        assert params.drummer_intensity == value


class TestDrummerPluginIntensityScaling:
    def test_zero_intensity_leaves_pattern_unchanged(self):
        plugin = PorcaroPlugin()
        pattern = _make_pattern()

        random.seed(1)
        styled = plugin.apply_style(pattern, intensity=0.0)

        def snap(p):
            return sorted(
                (round(b.position, 6), str(b.instrument), b.velocity)
                for b in p.beats
            )

        assert snap(styled) == snap(pattern)

    def test_default_intensity_matches_full_intensity(self):
        plugin = PorcaroPlugin()
        pattern = _make_pattern()

        random.seed(7)
        default_styled = plugin.apply_style(pattern)
        random.seed(7)
        full_styled = plugin.apply_style(pattern, intensity=1.0)

        assert len(default_styled.beats) == len(full_styled.beats)
        for a, b in zip(default_styled.beats, full_styled.beats, strict=True):
            assert a.position == b.position
            assert a.velocity == b.velocity

    def test_partial_intensity_is_between_zero_and_full(self):
        plugin = PorcaroPlugin()
        pattern = _make_pattern()

        random.seed(3)
        zero = plugin.apply_style(pattern, intensity=0.0)
        random.seed(3)
        half = plugin.apply_style(pattern, intensity=0.5)
        random.seed(3)
        full = plugin.apply_style(pattern, intensity=1.0)

        assert len(zero.beats) <= len(half.beats) <= len(full.beats)


class TestPluginManagerDrummerIntensity:
    def test_apply_drummer_style_threads_intensity_through(self):
        manager = PluginManager()
        manager.discover_plugins()
        pattern = _make_pattern()

        random.seed(11)
        zero = manager.apply_drummer_style(pattern, "porcaro", intensity=0.0)

        assert zero is not None

        def snap(p):
            return sorted(
                (round(b.position, 6), str(b.instrument), b.velocity)
                for b in p.beats
            )

        assert snap(zero) == snap(pattern)
