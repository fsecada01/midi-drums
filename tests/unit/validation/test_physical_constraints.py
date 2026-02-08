"""Tests for physical feasibility validation."""

import pytest

from midi_drums.models.pattern import DrumInstrument, Pattern
from midi_drums.validation.physical_constraints import (
    Conflict,
    LimbAssignment,
    PhysicalValidator,
)


class TestPhysicalValidator:
    """Test suite for PhysicalValidator."""

    def test_validator_initialization(self):
        """Test validator can be initialized with custom tolerance."""
        validator = PhysicalValidator(timing_tolerance=0.02)
        assert validator.timing_tolerance == 0.02

    def test_valid_basic_pattern(self):
        """Test that a basic valid pattern passes validation."""
        pattern = Pattern("basic_beat")

        # Basic rock beat: kick + hi-hat, snare + hi-hat (2 simultaneous max)
        pattern.add_beat(0.0, DrumInstrument.KICK, 105)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)
        pattern.add_beat(1.0, DrumInstrument.SNARE, 110)
        pattern.add_beat(1.0, DrumInstrument.CLOSED_HH, 80)
        pattern.add_beat(2.0, DrumInstrument.KICK, 105)
        pattern.add_beat(2.0, DrumInstrument.CLOSED_HH, 80)
        pattern.add_beat(3.0, DrumInstrument.SNARE, 110)
        pattern.add_beat(3.0, DrumInstrument.CLOSED_HH, 80)

        validator = PhysicalValidator()
        conflicts = validator.validate_pattern(pattern)

        assert len(conflicts) == 0, "Basic beat should be valid"
        assert validator.is_valid(pattern)

    def test_ride_hihat_conflict(self):
        """Test that ride + hi-hat (hand) is detected as conflict."""
        pattern = Pattern("ride_hihat_conflict")

        # Simultaneous ride and hi-hat hand - INVALID
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        validator = PhysicalValidator()
        conflicts = validator.validate_pattern(pattern)

        assert len(conflicts) == 1, "Should detect ride + hi-hat conflict"
        assert "ride" in conflicts[0].reason.lower()
        assert "hi-hat" in conflicts[0].reason.lower()
        assert not validator.is_valid(pattern)

    def test_ride_hihat_foot_valid(self):
        """Test that ride + hi-hat foot pedal is VALID."""
        pattern = Pattern("ride_with_pedal")

        # Ride (hand) + hi-hat foot pedal - VALID
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.PEDAL_HH, 65)
        pattern.add_beat(0.5, DrumInstrument.RIDE, 95)
        pattern.add_beat(1.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(1.0, DrumInstrument.PEDAL_HH, 65)

        validator = PhysicalValidator()
        conflicts = validator.validate_pattern(pattern)

        assert len(conflicts) == 0, "Ride + foot pedal should be valid"
        assert validator.is_valid(pattern)

    def test_three_hands_required(self):
        """Test that 3 simultaneous hand instruments is detected."""
        pattern = Pattern("three_hands")

        # Snare + crash + ride at same time - INVALID (needs 3 hands)
        pattern.add_beat(0.0, DrumInstrument.SNARE, 110)
        pattern.add_beat(0.0, DrumInstrument.CRASH, 115)
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)

        validator = PhysicalValidator()
        conflicts = validator.validate_pattern(pattern)

        assert len(conflicts) >= 1, "Should detect 3 simultaneous hands"
        hand_conflicts = [c for c in conflicts if "hands" in c.reason.lower()]
        assert len(hand_conflicts) >= 1

    def test_timing_tolerance(self):
        """Test that timing tolerance groups nearby beats."""
        pattern = Pattern("timing_test")

        # Beats very close together (within tolerance)
        pattern.add_beat(0.00, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.005, DrumInstrument.CLOSED_HH, 80)  # Within 0.01 tolerance

        validator = PhysicalValidator(timing_tolerance=0.01)
        conflicts = validator.validate_pattern(pattern)

        assert len(conflicts) == 1, "Should group beats within tolerance"

    def test_timing_tolerance_separate(self):
        """Test that beats outside tolerance are not grouped."""
        pattern = Pattern("timing_separate")

        # Beats far apart (outside tolerance)
        pattern.add_beat(0.00, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.02, DrumInstrument.CLOSED_HH, 80)  # Outside 0.01 tolerance

        validator = PhysicalValidator(timing_tolerance=0.01)
        conflicts = validator.validate_pattern(pattern)

        assert len(conflicts) == 0, "Should not group beats outside tolerance"

    def test_all_hihat_variants_conflict_with_ride(self):
        """Test that all hi-hat hand variants conflict with ride."""
        hihat_variants = [
            DrumInstrument.CLOSED_HH,
            DrumInstrument.CLOSED_HH_EDGE,
            DrumInstrument.CLOSED_HH_TIP,
            DrumInstrument.TIGHT_HH_EDGE,
            DrumInstrument.TIGHT_HH_TIP,
            DrumInstrument.OPEN_HH,
            DrumInstrument.OPEN_HH_1,
            DrumInstrument.OPEN_HH_2,
            DrumInstrument.OPEN_HH_3,
            DrumInstrument.OPEN_HH_MAX,
        ]

        validator = PhysicalValidator()

        for hihat_variant in hihat_variants:
            pattern = Pattern(f"ride_vs_{hihat_variant.name}")
            pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
            pattern.add_beat(0.0, hihat_variant, 80)

            conflicts = validator.validate_pattern(pattern)

            assert (
                len(conflicts) >= 1
            ), f"{hihat_variant.name} should conflict with ride"

    def test_ride_bell_also_conflicts(self):
        """Test that ride bell also conflicts with hi-hat hand."""
        pattern = Pattern("ride_bell_conflict")

        pattern.add_beat(0.0, DrumInstrument.RIDE_BELL, 100)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        validator = PhysicalValidator()
        conflicts = validator.validate_pattern(pattern)

        assert len(conflicts) == 1, "Ride bell should conflict with hi-hat"

    def test_complex_valid_pattern(self):
        """Test a complex but valid pattern."""
        pattern = Pattern("complex_valid")

        # Bar 1: Kick + hi-hat, snare + hi-hat
        for i in range(8):
            pattern.add_beat(i * 0.5, DrumInstrument.CLOSED_HH, 80)

        pattern.add_beat(0.0, DrumInstrument.KICK, 105)
        pattern.add_beat(1.0, DrumInstrument.SNARE, 110)
        pattern.add_beat(2.0, DrumInstrument.KICK, 105)
        pattern.add_beat(3.0, DrumInstrument.SNARE, 110)

        # Crash on downbeat
        pattern.add_beat(0.0, DrumInstrument.CRASH, 115)

        validator = PhysicalValidator()
        conflicts = validator.validate_pattern(pattern)

        assert len(conflicts) == 0, "Complex valid pattern should pass"

    def test_get_statistics(self):
        """Test statistics generation."""
        pattern = Pattern("stats_test")

        # Add valid beats
        pattern.add_beat(0.0, DrumInstrument.KICK, 105)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        # Add invalid beats
        pattern.add_beat(1.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(1.0, DrumInstrument.CLOSED_HH, 80)

        validator = PhysicalValidator()
        stats = validator.get_statistics(pattern)

        assert stats["total_beats"] == 4
        assert stats["total_conflicts"] == 1
        assert not stats["is_valid"]
        assert stats["error_conflicts"] == 1
        assert stats["conflict_types"]["ride_hihat"] == 1

    def test_empty_pattern(self):
        """Test that empty pattern is valid."""
        pattern = Pattern("empty")

        validator = PhysicalValidator()
        conflicts = validator.validate_pattern(pattern)

        assert len(conflicts) == 0
        assert validator.is_valid(pattern)

    def test_kick_with_everything(self):
        """Test that kick (foot) can be played with 2 hand instruments."""
        pattern = Pattern("kick_plus_hands")

        # Kick + snare + hi-hat - VALID (1 foot + 2 hands)
        pattern.add_beat(0.0, DrumInstrument.KICK, 105)
        pattern.add_beat(0.0, DrumInstrument.SNARE, 110)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)

        validator = PhysicalValidator()
        conflicts = validator.validate_pattern(pattern)

        assert len(conflicts) == 0, "Kick + 2 hands should be valid"

    def test_kick_plus_pedal_hihat_plus_two_hands(self):
        """Test maximum limb usage: all 4 limbs at once."""
        pattern = Pattern("four_limbs")

        # Kick + pedal hi-hat + snare + ride - VALID (all 4 limbs)
        pattern.add_beat(0.0, DrumInstrument.KICK, 105)  # Right foot
        pattern.add_beat(0.0, DrumInstrument.PEDAL_HH, 65)  # Left foot
        pattern.add_beat(0.0, DrumInstrument.SNARE, 110)  # Left hand
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)  # Right hand

        validator = PhysicalValidator()
        conflicts = validator.validate_pattern(pattern)

        assert len(conflicts) == 0, "All 4 limbs simultaneously should be valid"

    def test_conflict_string_representation(self):
        """Test Conflict __str__ method."""
        conflict = Conflict(
            time=1.5,
            instruments=[DrumInstrument.RIDE, DrumInstrument.CLOSED_HH],
            reason="Test conflict",
            severity="error",
        )

        conflict_str = str(conflict)

        assert "1.50" in conflict_str
        assert "ERROR" in conflict_str
        assert "Test conflict" in conflict_str
        assert "RIDE" in conflict_str
        assert "CLOSED_HH" in conflict_str


class TestLimbAssignment:
    """Test LimbAssignment enum."""

    def test_limb_assignment_values(self):
        """Test that all limb assignments are defined."""
        assert LimbAssignment.RIGHT_HAND.value == "right_hand"
        assert LimbAssignment.LEFT_HAND.value == "left_hand"
        assert LimbAssignment.RIGHT_FOOT.value == "right_foot"
        assert LimbAssignment.LEFT_FOOT.value == "left_foot"


class TestInstrumentClassifications:
    """Test instrument classification constants."""

    def test_hand_instruments_complete(self):
        """Test that hand instruments set includes all hand-played drums."""
        validator = PhysicalValidator()

        # Should include all cymbals and drums played by hand
        assert DrumInstrument.RIDE in validator.HAND_INSTRUMENTS
        assert DrumInstrument.SNARE in validator.HAND_INSTRUMENTS
        assert DrumInstrument.CRASH in validator.HAND_INSTRUMENTS
        assert DrumInstrument.CLOSED_HH in validator.HAND_INSTRUMENTS

        # Should NOT include foot-operated instruments
        assert DrumInstrument.KICK not in validator.HAND_INSTRUMENTS
        assert DrumInstrument.PEDAL_HH not in validator.HAND_INSTRUMENTS

    def test_foot_instruments_complete(self):
        """Test that foot instruments set is correct."""
        validator = PhysicalValidator()

        assert DrumInstrument.KICK in validator.FOOT_INSTRUMENTS
        assert DrumInstrument.PEDAL_HH in validator.FOOT_INSTRUMENTS
        assert len(validator.FOOT_INSTRUMENTS) == 2

    def test_ride_hihat_sets_disjoint(self):
        """Test that ride and hi-hat hand sets are properly separate."""
        validator = PhysicalValidator()

        # Ride and hi-hat hand should be disjoint
        assert len(validator.RIDE_INSTRUMENTS & validator.HIHAT_HAND_INSTRUMENTS) == 0

        # Hi-hat hand and foot should be disjoint
        assert len(validator.HIHAT_HAND_INSTRUMENTS & validator.HIHAT_FOOT) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
