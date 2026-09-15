"""Tests for midi_drums.modifications.apply_drummer (ADR 0011)."""

import pytest

from midi_drums.core.models.pattern import Beat, Pattern
from midi_drums.modifications.apply_drummer import apply_drummer


def note(instrument, position_qn, velocity=100, **extra):
    return {
        "instrument": instrument,
        "position_qn": position_qn,
        "velocity": velocity,
        "ghost_note": False,
        "accent": False,
        **extra,
    }


class FakePluginManager:
    """Deterministic stand-in for PluginManager.apply_drummer_style, so
    these tests don't depend on real plugin discovery or a specific
    drummer's actual modifications."""

    def __init__(self, transform=None, return_none=False):
        self.transform = transform
        self.return_none = return_none
        self.calls = []

    def apply_drummer_style(self, pattern, drummer, intensity=1.0):
        self.calls.append((drummer, intensity))
        if self.return_none:
            return None
        if self.transform:
            return self.transform(pattern)
        return pattern


class TestApplyDrummerValidation:
    def test_intensity_out_of_range_raises(self):
        with pytest.raises(ValueError, match="intensity must be between"):
            apply_drummer(
                [],
                drummer="bonham",
                intensity=1.5,
                timing_variance=0.0,
                velocity_variance=0.0,
            )

    def test_negative_timing_variance_raises(self):
        with pytest.raises(ValueError, match="timing_variance must be"):
            apply_drummer(
                [],
                drummer=None,
                intensity=1.0,
                timing_variance=-0.1,
                velocity_variance=0.0,
            )

    def test_negative_velocity_variance_raises(self):
        with pytest.raises(ValueError, match="velocity_variance must be"):
            apply_drummer(
                [],
                drummer=None,
                intensity=1.0,
                timing_variance=0.0,
                velocity_variance=-1.0,
            )


class TestApplyDrummerPassthrough:
    def test_empty_notes_returns_empty(self):
        result = apply_drummer(
            [],
            drummer=None,
            intensity=1.0,
            timing_variance=0.0,
            velocity_variance=0.0,
        )
        assert result == []

    def test_unmapped_instrument_passes_through_untouched(self):
        notes = [note("unmapped_50", 0.0)]
        result = apply_drummer(
            notes,
            drummer=None,
            intensity=1.0,
            timing_variance=0.0,
            velocity_variance=0.0,
        )
        assert result == notes

    def test_no_drummer_no_variance_is_identity_for_mapped_notes(self):
        notes = [
            note("KICK", 0.0, velocity=105),
            note("SNARE", 1.0, velocity=100),
        ]
        result = apply_drummer(
            notes,
            drummer=None,
            intensity=1.0,
            timing_variance=0.0,
            velocity_variance=0.0,
        )
        by_instrument = {n["instrument"]: n for n in result}
        assert by_instrument["KICK"]["position_qn"] == 0.0
        assert by_instrument["KICK"]["velocity"] == 105
        assert by_instrument["SNARE"]["position_qn"] == 1.0

    def test_mixed_mapped_and_unmapped_notes(self):
        notes = [note("KICK", 0.0), note("unmapped_50", 0.5)]
        result = apply_drummer(
            notes,
            drummer=None,
            intensity=1.0,
            timing_variance=0.0,
            velocity_variance=0.0,
        )
        instruments = {n["instrument"] for n in result}
        assert instruments == {"KICK", "unmapped_50"}


class TestApplyDrummerStyling:
    def test_drummer_style_is_invoked_with_intensity(self):
        pm = FakePluginManager()
        notes = [note("KICK", 0.0)]
        apply_drummer(
            notes,
            drummer="bonham",
            intensity=0.7,
            timing_variance=0.0,
            velocity_variance=0.0,
            plugin_manager=pm,
        )
        assert pm.calls == [("bonham", 0.7)]

    def test_drummer_transform_is_reflected_in_output(self):
        def double_velocity(pattern: Pattern) -> Pattern:
            return Pattern(
                name=pattern.name,
                beats=[
                    Beat(
                        position=b.position,
                        instrument=b.instrument,
                        velocity=min(127, b.velocity * 2),
                    )
                    for b in pattern.beats
                ],
                time_signature=pattern.time_signature,
            )

        pm = FakePluginManager(transform=double_velocity)
        notes = [note("KICK", 0.0, velocity=50)]
        result = apply_drummer(
            notes,
            drummer="bonham",
            intensity=1.0,
            timing_variance=0.0,
            velocity_variance=0.0,
            plugin_manager=pm,
        )
        assert result[0]["velocity"] == 100

    def test_none_from_plugin_manager_falls_back_to_original(self):
        pm = FakePluginManager(return_none=True)
        notes = [note("KICK", 0.0, velocity=77)]
        result = apply_drummer(
            notes,
            drummer="not-a-real-drummer",
            intensity=1.0,
            timing_variance=0.0,
            velocity_variance=0.0,
            plugin_manager=pm,
        )
        assert result[0]["velocity"] == 77

    def test_falsy_drummer_skips_style_application_entirely(self):
        pm = FakePluginManager()
        apply_drummer(
            [note("KICK", 0.0)],
            drummer=None,
            intensity=1.0,
            timing_variance=0.0,
            velocity_variance=0.0,
            plugin_manager=pm,
        )
        assert pm.calls == []


class TestApplyDrummerHumanization:
    def test_zero_variances_do_not_perturb_position_or_velocity(self):
        notes = [note("KICK", 2.0, velocity=90)]
        result = apply_drummer(
            notes,
            drummer=None,
            intensity=1.0,
            timing_variance=0.0,
            velocity_variance=0.0,
        )
        assert result[0]["position_qn"] == 2.0
        assert result[0]["velocity"] == 90

    def test_nonzero_timing_variance_can_move_position_off_the_original(self):
        # Not a statistical test - just confirms humanize() actually ran
        # by checking positions are no longer all exactly the seeded value
        # across a batch of identical notes (astronomically unlikely to
        # all land back on 0.0 by chance with variance this large).
        notes = [note("KICK", 0.0) for _ in range(20)]
        result = apply_drummer(
            notes,
            drummer=None,
            intensity=1.0,
            timing_variance=0.5,
            velocity_variance=0.0,
        )
        positions = {n["position_qn"] for n in result}
        assert positions != {0.0}

    def test_nonzero_velocity_variance_can_move_velocity_off_the_original(self):
        notes = [note("KICK", 0.0, velocity=64) for _ in range(20)]
        result = apply_drummer(
            notes,
            drummer=None,
            intensity=1.0,
            timing_variance=0.0,
            velocity_variance=40,
        )
        velocities = {n["velocity"] for n in result}
        assert velocities != {64}

    def test_humanized_velocity_stays_in_midi_range(self):
        notes = [note("KICK", 0.0, velocity=120) for _ in range(20)]
        result = apply_drummer(
            notes,
            drummer=None,
            intensity=1.0,
            timing_variance=0.0,
            velocity_variance=40,
        )
        assert all(1 <= n["velocity"] <= 127 for n in result)


class TestApplyDrummerRealPluginManager:
    """A couple of end-to-end checks against real plugin discovery, so
    the wiring to PluginManager.apply_drummer_style is verified against
    the real thing at least once (not just the fake above)."""

    def test_real_bonham_drummer_runs_without_error(self):
        from midi_drums.generation.engines.drum_generator import DrumGenerator

        pm = DrumGenerator().plugin_manager
        notes = [note("KICK", 0.0), note("SNARE", 1.0)]
        result = apply_drummer(
            notes,
            drummer="bonham",
            intensity=0.8,
            timing_variance=0.0,
            velocity_variance=0.0,
            plugin_manager=pm,
        )
        assert len(result) >= 2

    def test_unknown_real_drummer_falls_back_to_unstyled(self):
        from midi_drums.generation.engines.drum_generator import DrumGenerator

        pm = DrumGenerator().plugin_manager
        notes = [note("KICK", 0.0, velocity=99)]
        result = apply_drummer(
            notes,
            drummer="not-a-real-drummer",
            intensity=1.0,
            timing_variance=0.0,
            velocity_variance=0.0,
            plugin_manager=pm,
        )
        assert result == notes
