"""Tests for the additive-rhythm-grouping pattern builder."""

from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.generation.builders.additive_rhythm_builder import (
    build_additive_rhythm_bars,
)


def kicks(pattern):
    return [b for b in pattern.beats if b.instrument == DrumInstrument.KICK]


def hihats(pattern):
    return [b for b in pattern.beats if b.instrument == DrumInstrument.CLOSED_HH]


class TestBuildAdditiveRhythmBars:
    def test_confirmed_worked_example_produces_two_bars(self):
        patterns = build_additive_rhythm_bars("3-3-3-3-2-2", grid_denominator=16)

        assert len(patterns) == 2
        bar_1, bar_2 = patterns
        assert str(bar_1.time_signature) == "6/8"
        assert str(bar_2.time_signature) == "2/8"

    def test_kick_count_matches_group_count_per_bar(self):
        patterns = build_additive_rhythm_bars("3-3-3-3-2-2", grid_denominator=16)

        assert len(kicks(patterns[0])) == 4  # four groups of 3
        assert len(kicks(patterns[1])) == 2  # two groups of 2

    def test_hihat_count_matches_total_grid_units_per_bar(self):
        patterns = build_additive_rhythm_bars("3-3-3-3-2-2", grid_denominator=16)

        assert len(hihats(patterns[0])) == 12  # 4 groups * 3 units
        assert len(hihats(patterns[1])) == 4  # 2 groups * 2 units

    def test_beat_positions_fit_within_bar_span(self):
        patterns = build_additive_rhythm_bars("3-3-3-3-2-2", grid_denominator=16)

        for pattern in patterns:
            beats_per_bar = pattern.time_signature.beats_per_bar
            for beat in pattern.beats:
                assert 0.0 <= beat.position < beats_per_bar

    def test_kick_positions_land_on_group_starts(self):
        patterns = build_additive_rhythm_bars("3-3-3-3-2-2", grid_denominator=16)

        # First bar: groups of 3 sixteenths -> 0.75 beats apart.
        kick_positions = sorted(b.position for b in kicks(patterns[0]))
        assert kick_positions == [0.0, 0.75, 1.5, 2.25]

        # Second bar: groups of 2 sixteenths -> 0.5 beats apart.
        kick_positions_2 = sorted(b.position for b in kicks(patterns[1]))
        assert kick_positions_2 == [0.0, 0.5]
