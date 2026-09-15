"""Tests for midi_drums.modifications.density_control (ADR 0010).

adjust_density operates on the Step Editor's flat per-note dict shape
(bar/step/velocity/off_grid/_idx), not Pattern/Beat, so these fixtures are
plain lists of dicts rather than PatternBuilder output.
"""

import pytest

from midi_drums.modifications.density_control import (
    GHOST_VELOCITY,
    adjust_density,
    steps_per_bar,
)


def note(bar, step, velocity=100, idx=0):
    return {
        "bar": bar,
        "step": step,
        "velocity": velocity,
        "off_grid": False,
        "_idx": idx,
    }


class TestStepsPerBar:
    def test_16th_in_4_4(self):
        assert steps_per_bar("16th", 4, 4) == 16

    def test_8th_triplet_in_4_4(self):
        assert steps_per_bar("8th_triplet", 4, 4) == 12

    def test_16th_in_3_4(self):
        assert steps_per_bar("16th", 3, 4) == 12

    def test_unknown_resolution_raises(self):
        with pytest.raises(ValueError, match="Unknown grid_resolution"):
            steps_per_bar("bogus", 4, 4)


class TestAdjustDensityValidation:
    def test_amount_out_of_range_raises(self):
        with pytest.raises(ValueError, match="amount must be between"):
            adjust_density([], amount=1.5, kind="main", grid_resolution="16th")

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError, match="Unknown kind"):
            adjust_density([], amount=0.5, kind="bogus", grid_resolution="16th")

    def test_bars_below_one_raises(self):
        with pytest.raises(ValueError, match="bars must be"):
            adjust_density(
                [], amount=0.5, kind="main", grid_resolution="16th", bars=0
            )

    def test_unknown_grid_resolution_raises(self):
        with pytest.raises(ValueError, match="Unknown grid_resolution"):
            adjust_density([], amount=0.5, kind="main", grid_resolution="bogus")


class TestAdjustDensityNoOp:
    def test_zero_amount_returns_notes_unchanged(self):
        notes = [note(0, 0), note(0, 4)]
        result = adjust_density(
            notes, amount=0.0, kind="main", grid_resolution="16th"
        )
        assert result == notes

    def test_zero_amount_returns_a_copy_not_the_same_list(self):
        notes = [note(0, 0)]
        result = adjust_density(
            notes, amount=0.0, kind="main", grid_resolution="16th"
        )
        assert result == notes
        assert result is not notes


class TestAdjustDensityInsertion:
    def test_amount_1_0_fills_every_open_slot(self):
        # probability 1.0 (complexity defaults to 1.0 when no context is
        # given) means every open grid slot gets filled deterministically.
        notes = [note(0, 0)]
        result = adjust_density(
            notes, amount=1.0, kind="main", grid_resolution="16th", bars=1
        )
        assert len(result) == steps_per_bar("16th", 4, 4)
        steps = sorted(n["step"] for n in result)
        assert steps == list(range(16))

    def test_never_duplicates_an_occupied_slot(self):
        notes = [note(0, s) for s in range(16)]  # every slot already full
        result = adjust_density(
            notes, amount=1.0, kind="main", grid_resolution="16th", bars=1
        )
        assert len(result) == 16

    def test_ghost_kind_uses_ghost_velocity(self):
        notes = []
        result = adjust_density(
            notes, amount=1.0, kind="ghost", grid_resolution="16th", bars=1
        )
        assert all(n["velocity"] == GHOST_VELOCITY for n in result)

    def test_main_kind_uses_average_existing_velocity(self):
        notes = [note(0, 0, velocity=80), note(0, 8, velocity=120)]
        result = adjust_density(
            notes, amount=1.0, kind="main", grid_resolution="16th", bars=1
        )
        new_notes = [n for n in result if n not in notes]
        assert new_notes
        assert all(n["velocity"] == 100 for n in new_notes)

    def test_new_notes_have_no_real_idx(self):
        result = adjust_density(
            [], amount=1.0, kind="main", grid_resolution="16th", bars=1
        )
        assert all(n["_idx"] is None for n in result)

    def test_new_notes_carry_no_ppqpos(self):
        result = adjust_density(
            [], amount=1.0, kind="main", grid_resolution="16th", bars=1
        )
        assert all("ppqpos" not in n for n in result)

    def test_bars_greater_than_one_spans_every_bar(self):
        result = adjust_density(
            [], amount=1.0, kind="main", grid_resolution="16th", bars=2
        )
        bars_present = {n["bar"] for n in result}
        assert bars_present == {0, 1}

    def test_low_complexity_context_does_not_raise_or_disable_insertion(self):
        result = adjust_density(
            [],
            amount=1.0,
            kind="main",
            grid_resolution="16th",
            bars=1,
            context={"complexity": 0.0},
        )
        # 0.5 floor means insertion still happens even at complexity 0.0.
        assert len(result) > 0

    def test_missing_context_degrades_to_context_free_heuristic(self):
        # Per ADR 0010: context is optional and must not raise.
        result = adjust_density(
            [],
            amount=1.0,
            kind="main",
            grid_resolution="16th",
            bars=1,
            context=None,
        )
        assert len(result) == steps_per_bar("16th", 4, 4)


class TestAdjustDensityRemoval:
    def test_amount_negative_1_0_removes_every_note(self):
        notes = [note(0, s, velocity=100) for s in range(4)]
        result = adjust_density(
            notes, amount=-1.0, kind="main", grid_resolution="16th"
        )
        assert result == []

    def test_removal_prefers_lowest_velocity_first(self):
        notes = [
            note(0, 0, velocity=20),
            note(0, 4, velocity=127),
            note(0, 8, velocity=127),
            note(0, 12, velocity=127),
        ]
        result = adjust_density(
            notes, amount=-0.25, kind="main", grid_resolution="16th"
        )
        remaining_steps = {n["step"] for n in result}
        assert 0 not in remaining_steps
        assert len(result) == 3

    def test_removal_on_empty_notes_is_a_noop(self):
        result = adjust_density(
            [], amount=-0.5, kind="main", grid_resolution="16th"
        )
        assert result == []

    def test_kind_is_irrelevant_to_removal(self):
        notes = [note(0, 0, velocity=10), note(0, 4, velocity=120)]
        result_main = adjust_density(
            notes, amount=-0.5, kind="main", grid_resolution="16th"
        )
        result_ghost = adjust_density(
            notes, amount=-0.5, kind="ghost", grid_resolution="16th"
        )
        assert result_main == result_ghost
