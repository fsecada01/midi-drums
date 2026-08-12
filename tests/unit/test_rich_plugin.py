"""Unit tests for the Buddy Rich drummer plugin."""

import pytest

from midi_drums.core.models.song import Fill
from midi_drums.generation.builders.pattern_builder import PatternBuilder
from midi_drums.plugins.drummers.rich import RichPlugin
from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin


def _test_pattern():
    builder = PatternBuilder("test_pattern")
    builder.kick(0.0, 100).kick(2.0, 100)
    builder.snare(1.0, 110).snare(3.0, 110)
    for i in range(8):
        builder.hihat(i * 0.5, 80)
    return builder.build()


class TestRichPlugin:
    def test_implements_drummer_plugin_interface(self):
        assert issubclass(RichPlugin, DrummerPlugin)

    def test_drummer_name(self):
        assert RichPlugin().drummer_name == "rich"

    def test_compatible_genres_declared(self):
        genres = RichPlugin().compatible_genres
        assert isinstance(genres, list)
        assert len(genres) > 0
        assert "jazz" in genres

    def test_apply_style_returns_modified_pattern(self):
        plugin = RichPlugin()
        pattern = _test_pattern()
        styled = plugin.apply_style(pattern)

        assert styled is not None
        assert len(styled.beats) > 0
        assert "rich" in styled.name

    def test_apply_style_does_not_mutate_original(self):
        plugin = RichPlugin()
        pattern = _test_pattern()
        original_beat_count = len(pattern.beats)

        plugin.apply_style(pattern)

        assert len(pattern.beats) == original_beat_count

    def test_signature_fills_implemented(self):
        fills = RichPlugin().get_signature_fills()

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
        for fill in RichPlugin().get_signature_fills():
            for beat in fill.pattern.beats:
                assert beat.position < 1.0, (
                    f"beat at position {beat.position} in "
                    f"'{fill.pattern.name}' falls outside the fill-render "
                    "window and would be silently dropped"
                )

    @pytest.mark.parametrize("genre", ["jazz", "rock"])
    def test_compatible_with_declared_genres(self, genre):
        plugin = RichPlugin()
        assert plugin.is_compatible_with_genre(genre)

    def test_fast_chops_applied_before_heavy_accents(self):
        # FastChopsTriplets creates new beats with accent=True; HeavyAccents
        # only boosts beats that already exist when it runs. If accents ran
        # first, fast_chops' newly created accented beats would never get
        # boosted, so the two modifications must run in this order.
        plugin = RichPlugin()
        call_order = []
        original_fast_chops_apply = plugin.fast_chops.apply
        original_accents_apply = plugin.accents.apply

        def tracked_fast_chops(*args, **kwargs):
            call_order.append("fast_chops")
            return original_fast_chops_apply(*args, **kwargs)

        def tracked_accents(*args, **kwargs):
            call_order.append("accents")
            return original_accents_apply(*args, **kwargs)

        plugin.fast_chops.apply = tracked_fast_chops
        plugin.accents.apply = tracked_accents

        plugin.apply_style(_test_pattern())

        assert call_order == ["fast_chops", "accents"]


class TestRichPluginDiscovery:
    def test_rich_auto_discovered_by_registry(self):
        from midi_drums import DrumGenerator

        generator = DrumGenerator()
        assert "rich" in generator.get_available_drummers()

    def test_rich_style_applies_via_generator(self):
        from midi_drums import DrumGenerator

        generator = DrumGenerator()
        pattern = generator.generate_pattern("jazz", "verse", style="swing")
        styled = generator.apply_drummer_style(pattern, "rich")

        assert styled is not None
        assert len(styled.beats) > 0
