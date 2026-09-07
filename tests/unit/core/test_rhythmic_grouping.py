"""Tests for additive rhythmic-grouping -> TimeSignature resolution."""

from midi_drums.core.value_objects.rhythmic_grouping import (
    parse_groups,
    resolve_grouping,
    split_into_bars,
)
from midi_drums.core.value_objects.time_signature import TimeSignature


class TestSplitIntoBars:
    def test_splits_by_maximal_runs_of_identical_values(self):
        assert split_into_bars([3, 3, 3, 3, 2, 2]) == [[3, 3, 3, 3], [2, 2]]

    def test_single_run(self):
        assert split_into_bars([4, 4, 4, 4]) == [[4, 4, 4, 4]]

    def test_empty(self):
        assert split_into_bars([]) == []


class TestParseGroups:
    def test_dash_separated(self):
        assert parse_groups("3-3-3-3-2-2") == [[3, 3, 3, 3, 2, 2]]

    def test_plus_separated(self):
        assert parse_groups("2+2+3") == [[2, 2, 3]]

    def test_pipe_splits_into_explicit_bars(self):
        assert parse_groups("3+3+3+3|2+2") == [[3, 3, 3, 3], [2, 2]]


class TestResolveGroupingAutoSplit:
    def test_confirmed_worked_example(self):
        """3-3-3-3-2-2 at a 16th grid -> 6/8 then 2/8 (user-confirmed)."""
        bars = resolve_grouping("3-3-3-3-2-2", grid_denominator=16)

        assert len(bars) == 2
        assert bars[0].time_signature == TimeSignature(6, 8)
        assert bars[0].groups == (3, 3, 3, 3)
        assert bars[1].time_signature == TimeSignature(2, 8)
        assert bars[1].groups == (2, 2)

    def test_simple_duple_grouping_reduces_to_natural_meter(self):
        """Four groups of 4 sixteenths is just 4/4, not 16/16 or 8/8."""
        bars = resolve_grouping("4-4-4-4", grid_denominator=16)

        assert len(bars) == 1
        assert bars[0].time_signature == TimeSignature(4, 4)

    def test_two_groups_of_2_eighths_reduces_to_2_4(self):
        bars = resolve_grouping("2-2", grid_denominator=8)

        assert len(bars) == 1
        assert bars[0].time_signature == TimeSignature(2, 4)


class TestResolveGroupingExplicitBars:
    def test_heterogeneous_bar_no_reduction(self):
        """Classic Balkan additive notation: 2+2+3 @ 8th grid -> 7/8, as written.

        A trailing '|' with nothing after it forces single-explicit-bar
        reading (an empty final segment is dropped) without needing a
        second bar.
        """
        bars = resolve_grouping("2+2+3|", grid_denominator=8)

        assert len(bars) == 1
        assert bars[0].time_signature == TimeSignature(7, 8)
        assert bars[0].groups == (2, 2, 3)

    def test_explicit_pipe_matches_auto_split_reading(self):
        auto = resolve_grouping("3-3-3-3-2-2", grid_denominator=16)
        explicit = resolve_grouping("3+3+3+3|2+2", grid_denominator=16)

        assert [b.time_signature for b in auto] == [
            b.time_signature for b in explicit
        ]
        assert [b.groups for b in auto] == [b.groups for b in explicit]

    def test_pipe_disambiguates_from_auto_split_of_same_digits(self):
        """Without '|', '2-2-3' auto-splits (identical-run detection);
        with '|' present, the same digits read as one heterogeneous bar."""
        auto = resolve_grouping("2-2-3", grid_denominator=8)
        explicit = resolve_grouping("2+2+3|3", grid_denominator=8)

        # Auto-split treats the run of two 2's and the lone 3 as two bars.
        assert len(auto) == 2
        # Explicit-bar reading: first segment is one heterogeneous 7/8 bar.
        assert explicit[0].time_signature == TimeSignature(7, 8)
        assert explicit[0].groups == (2, 2, 3)
