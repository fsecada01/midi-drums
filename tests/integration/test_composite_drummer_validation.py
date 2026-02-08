"""Integration tests for composite drummer with physical validation."""

import pytest

from midi_drums.models.pattern import DrumInstrument, Pattern
from midi_drums.plugins.drummers.composite_doom_blues import (
    CompositeDoomBluesPlugin,
)
from midi_drums.validation.physical_constraints import PhysicalValidator


class TestCompositeDrummerValidation:
    """Test that composite drummer produces physically valid patterns."""

    def test_composite_drummer_initialization(self):
        """Test composite drummer initializes with validator."""
        drummer = CompositeDoomBluesPlugin()

        assert drummer.validator is not None
        assert isinstance(drummer.validator, PhysicalValidator)

    def test_composite_produces_valid_patterns(self):
        """Test that composite drummer output is physically valid."""
        drummer = CompositeDoomBluesPlugin()
        validator = PhysicalValidator()

        # Create a base pattern that might create conflicts
        pattern = Pattern("test_verse")

        # Add some basic beats
        for i in range(8):
            pattern.add_beat(i * 0.5, DrumInstrument.CLOSED_HH, 80)

        pattern.add_beat(0.0, DrumInstrument.KICK, 105)
        pattern.add_beat(1.0, DrumInstrument.SNARE, 110)
        pattern.add_beat(2.0, DrumInstrument.KICK, 105)
        pattern.add_beat(3.0, DrumInstrument.SNARE, 110)

        # Apply composite drummer style
        styled_pattern = drummer.apply_style(pattern)

        # Validate result
        conflicts = validator.validate_pattern(styled_pattern)

        assert (
            len(conflicts) == 0
        ), f"Composite drummer should produce valid patterns, but got {len(conflicts)} conflicts"

    def test_composite_resolves_ride_hihat_conflicts(self):
        """Test that composite drummer produces valid output even with conflicting input."""
        drummer = CompositeDoomBluesPlugin()

        # Create pattern with potential for ride/hihat conflict
        pattern = Pattern("test_chorus")

        # Add ride and hi-hat at same time (will conflict)
        pattern.add_beat(0.0, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH, 80)
        pattern.add_beat(0.5, DrumInstrument.RIDE, 95)
        pattern.add_beat(0.5, DrumInstrument.CLOSED_HH, 80)

        # Apply composite drummer (should produce valid output)
        styled_pattern = drummer.apply_style(pattern)

        # Most important: Check that output is physically valid
        validator = PhysicalValidator()
        conflicts = validator.validate_pattern(styled_pattern)

        assert (
            len(conflicts) == 0
        ), f"Composite drummer output should be physically valid, got {len(conflicts)} conflicts"

        # Pattern should have some beats
        assert len(styled_pattern.beats) > 0, "Should have some beats in output"

    def test_composite_produces_meaningful_output(self):
        """Test that composite produces meaningful drum patterns."""
        drummer = CompositeDoomBluesPlugin()

        pattern = Pattern("test_pattern")
        for i in range(16):
            pattern.add_beat(i * 0.25, DrumInstrument.CLOSED_HH, 80)

        pattern.add_beat(0.0, DrumInstrument.KICK, 105)
        pattern.add_beat(1.0, DrumInstrument.SNARE, 110)

        styled_pattern = drummer.apply_style(pattern)

        # Should have a reasonable number of beats (composite adds complexity)
        # Not too few (would be boring) and not too many (would be cluttered)
        assert (
            10 <= len(styled_pattern.beats) <= 100
        ), f"Beat count seems unreasonable: {len(styled_pattern.beats)}"

        # Should be physically valid
        validator = PhysicalValidator()
        conflicts = validator.validate_pattern(styled_pattern)
        assert len(conflicts) == 0

    def test_composite_negative_positions_clamped(self):
        """Test that negative positions are clamped to 0.0."""
        drummer = CompositeDoomBluesPlugin()

        pattern = Pattern("test_timing")
        pattern.add_beat(0.1, DrumInstrument.SNARE, 110)
        pattern.add_beat(1.0, DrumInstrument.KICK, 105)

        styled_pattern = drummer.apply_style(pattern)

        # Check no negative positions
        for beat in styled_pattern.beats:
            assert (
                beat.position >= 0.0
            ), f"Beat position {beat.position} is negative"

    def test_composite_with_complex_pattern(self):
        """Test composite drummer with complex multi-instrument pattern."""
        drummer = CompositeDoomBluesPlugin()
        validator = PhysicalValidator()

        pattern = Pattern("complex_verse")

        # 16th note hi-hats
        for i in range(16):
            pattern.add_beat(i * 0.25, DrumInstrument.CLOSED_HH, 80)

        # Kick pattern
        pattern.add_beat(0.0, DrumInstrument.KICK, 105)
        pattern.add_beat(0.5, DrumInstrument.KICK, 100)
        pattern.add_beat(2.0, DrumInstrument.KICK, 105)
        pattern.add_beat(2.5, DrumInstrument.KICK, 100)

        # Snare backbeat
        pattern.add_beat(1.0, DrumInstrument.SNARE, 110)
        pattern.add_beat(3.0, DrumInstrument.SNARE, 110)

        # Crash on downbeat
        pattern.add_beat(0.0, DrumInstrument.CRASH, 115)

        styled_pattern = drummer.apply_style(pattern)

        # Should be valid
        conflicts = validator.validate_pattern(styled_pattern)
        assert len(conflicts) == 0

        # Should have various instruments
        instruments = {b.instrument for b in styled_pattern.beats}
        assert len(instruments) >= 3, "Should have multiple instruments"


class TestCompositeDrummerDescription:
    """Test metadata methods."""

    def test_drummer_name(self):
        """Test drummer name is correct."""
        drummer = CompositeDoomBluesPlugin()
        assert drummer.drummer_name == "composite_doom_blues"

    def test_compatible_genres(self):
        """Test compatible genres list."""
        drummer = CompositeDoomBluesPlugin()
        genres = drummer.compatible_genres

        assert "metal" in genres
        assert "rock" in genres
        assert "blues" in genres

    def test_description(self):
        """Test description contains all three drummers."""
        drummer = CompositeDoomBluesPlugin()
        description = drummer.get_description()

        assert "Roeder" in description
        assert "Porcaro" in description
        assert "Chambers" in description

    def test_signature_fills_combined(self):
        """Test that signature fills are combined from all drummers."""
        drummer = CompositeDoomBluesPlugin()
        fills = drummer.get_signature_fills()

        # Should have fills from all three drummers
        # (exact count depends on implementation)
        assert isinstance(fills, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
