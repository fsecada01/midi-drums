"""Tests for pattern conflict resolution utilities."""

import pytest

from midi_drums.models.pattern import DrumInstrument, Pattern
from midi_drums.utils.pattern_fixer import (
    PatternFixer,
    remove_ride_hihat_conflicts,
)


class TestPatternFixer:
    """Test suite for PatternFixer class."""

    def test_fixer_initialization(self):
        """Test fixer can be initialized with custom tolerance."""
        fixer = PatternFixer(timing_tolerance=0.02)
        assert fixer.timing_tolerance == 0.02
        assert fixer.fixes_applied == []

    def test_no_conflicts_pattern_unchanged(self):
        """Test that valid patterns are not modified."""
        pattern = Pattern("valid_pattern")
        pattern.add_beat(0.0, DrumInstrument.KICK, 105)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)
        pattern.add_beat(1.0, DrumInstrument.SNARE, 110)
        pattern.add_beat(1.0, DrumInstrument.CLOSED_HH, 80)

        fixer = PatternFixer()
        fixed_pattern = fixer.fix_pattern(pattern)

        assert len(fixed_pattern.beats) == 4
        assert len(fixer.fixes_applied) == 0

    def test_ride_hihat_conflict_removed(self):
        """Test that ride + hi-hat conflicts are resolved."""
        pattern = Pattern("ride_hihat_conflict")
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        fixer = PatternFixer()
        fixed_pattern = fixer.remove_ride_hihat_conflicts(pattern)

        # Hi-hat hand should be removed
        instruments = [b.instrument for b in fixed_pattern.beats]
        assert DrumInstrument.RIDE in instruments
        assert DrumInstrument.CLOSED_HH not in instruments

        # Foot pedal should be added
        assert DrumInstrument.PEDAL_HH in instruments

    def test_foot_pedal_velocity_softer(self):
        """Test that foot pedal velocity is softer than hand."""
        pattern = Pattern("velocity_test")
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        fixer = PatternFixer()
        fixed_pattern = fixer.remove_ride_hihat_conflicts(pattern)

        # Find foot pedal beat
        foot_beats = [
            b
            for b in fixed_pattern.beats
            if b.instrument == DrumInstrument.PEDAL_HH
        ]

        assert len(foot_beats) == 1
        # Should be softer than original hi-hat (80 - 20 = 60)
        assert foot_beats[0].velocity == 60

    def test_multiple_hihat_variants_removed(self):
        """Test that all hi-hat hand variants are removed when ride present."""
        pattern = Pattern("multiple_hihats")
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)
        pattern.add_beat(0.0, DrumInstrument.OPEN_HH, 85)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH_TIP, 75)

        fixer = PatternFixer()
        fixed_pattern = fixer.remove_ride_hihat_conflicts(pattern)

        # All hi-hat hands should be removed
        instruments = [b.instrument for b in fixed_pattern.beats]
        assert DrumInstrument.CLOSED_HH not in instruments
        assert DrumInstrument.OPEN_HH not in instruments
        assert DrumInstrument.CLOSED_HH_TIP not in instruments

        # Ride and foot pedal should remain/be added
        assert DrumInstrument.RIDE in instruments
        assert DrumInstrument.PEDAL_HH in instruments

    def test_ride_bell_also_triggers_fix(self):
        """Test that ride bell also triggers conflict resolution."""
        pattern = Pattern("ride_bell_conflict")
        pattern.add_beat(0.0, DrumInstrument.RIDE_BELL, 100)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        fixer = PatternFixer()
        fixed_pattern = fixer.remove_ride_hihat_conflicts(pattern)

        instruments = [b.instrument for b in fixed_pattern.beats]
        assert DrumInstrument.RIDE_BELL in instruments
        assert DrumInstrument.CLOSED_HH not in instruments
        assert DrumInstrument.PEDAL_HH in instruments

    def test_multiple_conflicts_in_pattern(self):
        """Test fixing multiple conflicts at different times."""
        pattern = Pattern("multiple_conflicts")

        # Conflict at beat 0
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        # Valid beat at 1
        pattern.add_beat(1.0, DrumInstrument.SNARE, 110)

        # Conflict at beat 2
        pattern.add_beat(2.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(2.0, DrumInstrument.OPEN_HH, 85)

        fixer = PatternFixer()
        fixed_pattern = fixer.remove_ride_hihat_conflicts(pattern)

        # Should have 5 beats: 2 ride, 1 snare, 2 foot pedals
        assert len(fixed_pattern.beats) == 5

        # Check instruments
        instruments = [b.instrument for b in fixed_pattern.beats]
        assert instruments.count(DrumInstrument.RIDE) == 2
        assert instruments.count(DrumInstrument.SNARE) == 1
        assert instruments.count(DrumInstrument.PEDAL_HH) == 2
        assert DrumInstrument.CLOSED_HH not in instruments
        assert DrumInstrument.OPEN_HH not in instruments

    def test_timing_tolerance_groups_beats(self):
        """Test that beats within tolerance are grouped together."""
        pattern = Pattern("timing_test")
        pattern.add_beat(0.00, DrumInstrument.RIDE, 95)
        pattern.add_beat(
            0.005, DrumInstrument.CLOSED_HH, 80
        )  # Within tolerance

        fixer = PatternFixer(timing_tolerance=0.01)
        fixed_pattern = fixer.remove_ride_hihat_conflicts(pattern)

        # Hi-hat should be removed, foot pedal added
        instruments = [b.instrument for b in fixed_pattern.beats]
        assert DrumInstrument.CLOSED_HH not in instruments
        assert DrumInstrument.PEDAL_HH in instruments

    def test_beats_outside_tolerance_not_affected(self):
        """Test that beats outside tolerance are not grouped."""
        pattern = Pattern("timing_separate")
        pattern.add_beat(0.00, DrumInstrument.RIDE, 95)
        pattern.add_beat(
            0.02, DrumInstrument.CLOSED_HH, 80
        )  # Outside tolerance

        fixer = PatternFixer(timing_tolerance=0.01)
        fixed_pattern = fixer.remove_ride_hihat_conflicts(pattern)

        # Both should remain (no conflict)
        assert len(fixed_pattern.beats) == 2
        instruments = [b.instrument for b in fixed_pattern.beats]
        assert DrumInstrument.RIDE in instruments
        assert DrumInstrument.CLOSED_HH in instruments

    def test_foot_pedal_timing_preserved(self):
        """Test that foot pedal uses correct timing from hi-hat."""
        pattern = Pattern("timing_preservation")
        pattern.add_beat(1.5, DrumInstrument.RIDE, 95)
        pattern.add_beat(1.5, DrumInstrument.CLOSED_HH, 80)

        fixer = PatternFixer()
        fixed_pattern = fixer.remove_ride_hihat_conflicts(pattern)

        # Find foot pedal
        foot_beats = [
            b
            for b in fixed_pattern.beats
            if b.instrument == DrumInstrument.PEDAL_HH
        ]

        assert len(foot_beats) == 1
        assert foot_beats[0].position == 1.5

    def test_average_velocity_multiple_hihats(self):
        """Test average velocity calculation from multiple hi-hats."""
        pattern = Pattern("avg_velocity")
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)
        pattern.add_beat(0.0, DrumInstrument.OPEN_HH, 90)

        fixer = PatternFixer()
        fixed_pattern = fixer.remove_ride_hihat_conflicts(pattern)

        # Average: (80 + 90) / 2 = 85, minus 20 = 65
        foot_beats = [
            b
            for b in fixed_pattern.beats
            if b.instrument == DrumInstrument.PEDAL_HH
        ]

        assert len(foot_beats) == 1
        assert foot_beats[0].velocity == 65

    def test_minimum_foot_velocity(self):
        """Test that foot velocity has a minimum floor."""
        pattern = Pattern("min_velocity")
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 60)  # Very soft

        fixer = PatternFixer()
        fixed_pattern = fixer.remove_ride_hihat_conflicts(pattern)

        # 60 - 20 = 40, but should be clamped to min 50
        foot_beats = [
            b
            for b in fixed_pattern.beats
            if b.instrument == DrumInstrument.PEDAL_HH
        ]

        assert len(foot_beats) == 1
        assert foot_beats[0].velocity >= 50

    def test_fixes_applied_logging(self):
        """Test that fixes are logged in fixes_applied."""
        pattern = Pattern("logging_test")
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        fixer = PatternFixer()
        fixer.remove_ride_hihat_conflicts(pattern)

        assert len(fixer.fixes_applied) == 1
        assert "beat 0.00" in fixer.fixes_applied[0]
        assert "CLOSED_HH" in fixer.fixes_applied[0]
        assert "PEDAL_HH" in fixer.fixes_applied[0]

    def test_fix_pattern_comprehensive(self):
        """Test fix_pattern applies all fixes."""
        pattern = Pattern("comprehensive")
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        fixer = PatternFixer()
        fixed_pattern = fixer.fix_pattern(pattern)

        # Should have applied ride/hihat fix
        instruments = [b.instrument for b in fixed_pattern.beats]
        assert DrumInstrument.CLOSED_HH not in instruments
        assert DrumInstrument.PEDAL_HH in instruments
        assert len(fixer.fixes_applied) == 1

    def test_pattern_copy_not_modified(self):
        """Test that original pattern is not modified."""
        pattern = Pattern("original")
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        original_beat_count = len(pattern.beats)

        fixer = PatternFixer()
        fixed_pattern = fixer.remove_ride_hihat_conflicts(pattern)

        # Original should be unchanged
        assert len(pattern.beats) == original_beat_count
        assert any(
            b.instrument == DrumInstrument.CLOSED_HH for b in pattern.beats
        )

        # Fixed should have different instruments (PEDAL_HH instead of CLOSED_HH)
        assert not any(
            b.instrument == DrumInstrument.CLOSED_HH
            for b in fixed_pattern.beats
        )
        assert any(
            b.instrument == DrumInstrument.PEDAL_HH for b in fixed_pattern.beats
        )


class TestConvenienceFunction:
    """Test convenience function."""

    def test_remove_ride_hihat_conflicts_function(self):
        """Test convenience function works correctly."""
        pattern = Pattern("convenience_test")
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        fixed_pattern = remove_ride_hihat_conflicts(pattern)

        instruments = [b.instrument for b in fixed_pattern.beats]
        assert DrumInstrument.RIDE in instruments
        assert DrumInstrument.CLOSED_HH not in instruments
        assert DrumInstrument.PEDAL_HH in instruments

    def test_convenience_function_preserves_original(self):
        """Test convenience function doesn't modify original."""
        pattern = Pattern("preservation_test")
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        original_count = len(pattern.beats)

        fixed_pattern = remove_ride_hihat_conflicts(pattern)

        # Original should still have CLOSED_HH
        assert len(pattern.beats) == original_count
        assert any(
            b.instrument == DrumInstrument.CLOSED_HH for b in pattern.beats
        )

        # Fixed should have PEDAL_HH instead
        assert not any(
            b.instrument == DrumInstrument.CLOSED_HH
            for b in fixed_pattern.beats
        )
        assert any(
            b.instrument == DrumInstrument.PEDAL_HH for b in fixed_pattern.beats
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
