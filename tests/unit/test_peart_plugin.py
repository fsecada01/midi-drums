"""Unit tests for the Neil Peart drummer plugin."""

import pytest

from midi_drums.core.models.song import Fill
from midi_drums.generation.builders.pattern_builder import PatternBuilder
from midi_drums.plugins.drummers.peart import PeartPlugin
from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin


def _test_pattern():
    builder = PatternBuilder("test_pattern")
    builder.kick(0.0, 100).kick(2.0, 100)
    builder.snare(1.0, 110).snare(3.0, 110)
    for i in range(8):
        builder.hihat(i * 0.5, 80)
    return builder.build()


class TestPeartPlugin:
    def test_implements_drummer_plugin_interface(self):
        assert issubclass(PeartPlugin, DrummerPlugin)

    def test_drummer_name(self):
        assert PeartPlugin().drummer_name == "peart"

    def test_compatible_genres_declared(self):
        genres = PeartPlugin().compatible_genres
        assert isinstance(genres, list)
        assert len(genres) > 0
        assert "rock" in genres

    def test_apply_style_returns_modified_pattern(self):
        plugin = PeartPlugin()
        pattern = _test_pattern()
        styled = plugin.apply_style(pattern)

        assert styled is not None
        assert len(styled.beats) > 0
        assert "peart" in styled.name

    def test_apply_style_does_not_mutate_original(self):
        plugin = PeartPlugin()
        pattern = _test_pattern()
        original_beat_count = len(pattern.beats)

        plugin.apply_style(pattern)

        assert len(pattern.beats) == original_beat_count

    def test_signature_fills_implemented(self):
        fills = PeartPlugin().get_signature_fills()

        assert len(fills) > 0
        for fill in fills:
            assert isinstance(fill, Fill)
            assert len(fill.pattern.beats) > 0
            assert 0.0 <= fill.trigger_probability <= 1.0
            assert fill.section_position in ("start", "middle", "end")

    def test_signature_fill_beats_fit_within_render_window(self):
        # midi_drums/export/midi/engine.py's fill-rendering step only emits
        # beats with position < 1.0 (a fill occupies exactly one beat at the
        # end of a bar) - a beat at or past that boundary is silently
        # dropped rather than rendered.
        for fill in PeartPlugin().get_signature_fills():
            for beat in fill.pattern.beats:
                assert beat.position < 1.0, (
                    f"beat at position {beat.position} in "
                    f"'{fill.pattern.name}' falls outside the fill-render "
                    "window and would be silently dropped"
                )

    @pytest.mark.parametrize("genre", ["rock", "progressive", "metal"])
    def test_compatible_with_declared_genres(self, genre):
        plugin = PeartPlugin()
        assert plugin.is_compatible_with_genre(genre)


class TestPeartPluginDiscovery:
    def test_peart_auto_discovered_by_registry(self):
        from midi_drums import DrumGenerator

        generator = DrumGenerator()
        assert "peart" in generator.get_available_drummers()

    def test_peart_style_applies_via_generator(self):
        from midi_drums import DrumGenerator

        generator = DrumGenerator()
        pattern = generator.generate_pattern("rock", "verse", style="classic")
        styled = generator.apply_drummer_style(pattern, "peart")

        assert styled is not None
        assert len(styled.beats) > 0
