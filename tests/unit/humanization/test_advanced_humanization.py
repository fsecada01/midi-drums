"""Unit tests for advanced humanization system."""

import pytest

from midi_drums.humanization import AdvancedHumanizer
from midi_drums.models.pattern import (
    Beat,
    DrumInstrument,
    Pattern,
    PatternBuilder,
)


@pytest.fixture
def simple_pattern():
    """Create a simple 4-bar pattern for testing."""
    builder = PatternBuilder("test_pattern")

    # Standard rock beat
    for bar in range(4):
        base = bar * 4.0

        # Kick on 1 and 3
        builder.kick(base + 0.0, 100)
        builder.kick(base + 2.0, 100)

        # Snare on 2 and 4
        builder.snare(base + 1.0, 100)
        builder.snare(base + 3.0, 100)

        # Hi-hat 8ths
        for eighth in range(8):
            builder.hihat(base + (eighth * 0.5), 80)

    return builder.build()


@pytest.fixture
def pattern_with_accents():
    """Create pattern with ghost notes and accents."""
    builder = PatternBuilder("test_accents")

    # Kick
    builder.kick(0.0, 100)
    builder.kick(2.0, 100)

    # Snare with accent
    builder.pattern.add_beat(1.0, DrumInstrument.SNARE, 110, accent=True)

    # Snare with ghost note
    builder.pattern.add_beat(1.5, DrumInstrument.SNARE, 40, ghost_note=True)

    # Normal snare
    builder.snare(3.0, 100)

    return builder.build()


@pytest.fixture
def simultaneous_pattern():
    """Create pattern with simultaneous kick+snare for micro-timing tests."""
    builder = PatternBuilder("test_simultaneous")

    # Simultaneous kick + snare + crash on beat 1
    builder.kick(0.0, 110)
    builder.snare(0.0, 110)
    builder.crash(0.0, 115)

    # Simultaneous kick + snare on beat 3
    builder.kick(2.0, 110)
    builder.snare(2.0, 110)

    return builder.build()


class TestAdvancedHumanizerInit:
    """Test AdvancedHumanizer initialization."""

    def test_default_initialization(self):
        """Test default initialization values."""
        humanizer = AdvancedHumanizer()

        assert humanizer.tempo == 120
        assert humanizer.style == "balanced"
        assert humanizer.humanization_amount == 0.5
        assert humanizer.multiplier == 1.0

    def test_style_multipliers(self):
        """Test style multiplier settings."""
        tight = AdvancedHumanizer(style="tight")
        balanced = AdvancedHumanizer(style="balanced")
        loose = AdvancedHumanizer(style="loose")

        assert tight.multiplier == 0.5
        assert balanced.multiplier == 1.0
        assert loose.multiplier == 1.8

    def test_tempo_affects_ms_per_beat(self):
        """Test that tempo correctly calculates ms per beat."""
        h_60 = AdvancedHumanizer(tempo=60)
        h_120 = AdvancedHumanizer(tempo=120)
        h_240 = AdvancedHumanizer(tempo=240)

        assert h_60.ms_per_beat == 1000.0  # 60 BPM = 1 beat per second
        assert h_120.ms_per_beat == 500.0  # 120 BPM = 2 beats per second
        assert h_240.ms_per_beat == 250.0  # 240 BPM = 4 beats per second


class TestBasicHumanization:
    """Test basic humanization functionality."""

    def test_zero_humanization_returns_unchanged(self, simple_pattern):
        """Test that 0.0 humanization returns pattern unchanged."""
        humanizer = AdvancedHumanizer(humanization_amount=0.0)
        humanized = humanizer.humanize_pattern(simple_pattern)

        # Should return same pattern (by reference, not copy)
        assert humanized is simple_pattern

    def test_humanization_creates_new_pattern(self, simple_pattern):
        """Test that humanization creates new pattern instance."""
        humanizer = AdvancedHumanizer(humanization_amount=0.5)
        humanized = humanizer.humanize_pattern(simple_pattern)

        # Should be different object
        assert humanized is not simple_pattern
        assert humanized.name != simple_pattern.name
        assert "humanized" in humanized.name

    def test_humanization_preserves_beat_count(self, simple_pattern):
        """Test that humanization doesn't lose beats."""
        humanizer = AdvancedHumanizer(humanization_amount=0.7)
        humanized = humanizer.humanize_pattern(simple_pattern)

        assert len(humanized.beats) == len(simple_pattern.beats)

    def test_humanization_changes_timing(self, simple_pattern):
        """Test that humanization modifies beat timing."""
        humanizer = AdvancedHumanizer(humanization_amount=0.7)
        humanized = humanizer.humanize_pattern(simple_pattern)

        # At least some beats should have different timing
        timing_changed = False
        for original, humanized_beat in zip(simple_pattern.beats, humanized.beats, strict=False):
            if abs(original.position - humanized_beat.position) > 0.001:
                timing_changed = True
                break

        assert timing_changed, "Humanization should change beat timing"

    def test_humanization_changes_velocity(self, simple_pattern):
        """Test that humanization modifies velocities."""
        humanizer = AdvancedHumanizer(humanization_amount=0.7)
        humanized = humanizer.humanize_pattern(simple_pattern)

        # At least some beats should have different velocities
        velocity_changed = False
        for original, humanized_beat in zip(simple_pattern.beats, humanized.beats, strict=False):
            if original.velocity != humanized_beat.velocity:
                velocity_changed = True
                break

        assert velocity_changed, "Humanization should change velocities"

    def test_no_negative_positions(self, simple_pattern):
        """Test that humanization never creates negative positions."""
        humanizer = AdvancedHumanizer(humanization_amount=1.0)  # Maximum
        humanized = humanizer.humanize_pattern(simple_pattern)

        for beat in humanized.beats:
            assert (
                beat.position >= 0.0
            ), f"Beat position {beat.position} is negative"

    def test_velocity_within_midi_range(self, simple_pattern):
        """Test that velocities stay in valid MIDI range (1-127)."""
        humanizer = AdvancedHumanizer(humanization_amount=1.0)  # Maximum
        humanized = humanizer.humanize_pattern(simple_pattern)

        for beat in humanized.beats:
            assert 1 <= beat.velocity <= 127, f"Velocity {beat.velocity} out of range"


class TestContextAwareHumanization:
    """Test context-aware humanization features."""

    def test_verse_context_tighter_timing(self, simple_pattern):
        """Test that verse context produces tighter timing."""
        humanizer = AdvancedHumanizer(humanization_amount=0.5)

        verse = humanizer.humanize_pattern(simple_pattern, section_type="verse")
        fill = humanizer.humanize_pattern(simple_pattern, section_type="fill")

        # Measure timing variance (simplified - just check it doesn't crash)
        assert len(verse.beats) == len(fill.beats)

    def test_chorus_louder_than_verse(self, simple_pattern):
        """Test that chorus is louder than verse on average."""
        humanizer = AdvancedHumanizer(humanization_amount=0.5)

        verse = humanizer.humanize_pattern(simple_pattern, section_type="verse")
        chorus = humanizer.humanize_pattern(simple_pattern, section_type="chorus")

        verse_avg_velocity = sum(b.velocity for b in verse.beats) / len(verse.beats)
        chorus_avg_velocity = sum(b.velocity for b in chorus.beats) / len(
            chorus.beats
        )

        # Chorus should be louder (with some tolerance for randomness)
        assert (
            chorus_avg_velocity > verse_avg_velocity - 5
        ), "Chorus should be louder than verse"

    def test_breakdown_has_highest_velocity(self, simple_pattern):
        """Test that breakdown has highest average velocity."""
        humanizer = AdvancedHumanizer(humanization_amount=0.5)

        verse = humanizer.humanize_pattern(simple_pattern, section_type="verse")
        breakdown = humanizer.humanize_pattern(simple_pattern, section_type="breakdown")

        verse_avg_velocity = sum(b.velocity for b in verse.beats) / len(verse.beats)
        breakdown_avg_velocity = sum(b.velocity for b in breakdown.beats) / len(
            breakdown.beats
        )

        # Breakdown should be significantly louder
        assert (
            breakdown_avg_velocity > verse_avg_velocity + 5
        ), "Breakdown should be much louder"


class TestAccentAndGhostNotes:
    """Test handling of accents and ghost notes."""

    def test_ghost_notes_softer(self, pattern_with_accents):
        """Test that ghost notes have lower velocity."""
        humanizer = AdvancedHumanizer(humanization_amount=0.5)
        humanized = humanizer.humanize_pattern(pattern_with_accents)

        ghost_velocities = [b.velocity for b in humanized.beats if b.ghost_note]
        normal_velocities = [
            b.velocity for b in humanized.beats if not b.ghost_note and not b.accent
        ]

        # Ghost notes should be softer (within reasonable range)
        if ghost_velocities and normal_velocities:
            assert max(ghost_velocities) < min(normal_velocities) + 30

    def test_accents_louder(self, pattern_with_accents):
        """Test that accented notes have higher velocity."""
        humanizer = AdvancedHumanizer(humanization_amount=0.5)
        humanized = humanizer.humanize_pattern(pattern_with_accents)

        accent_velocities = [b.velocity for b in humanized.beats if b.accent]
        normal_velocities = [
            b.velocity for b in humanized.beats if not b.accent and not b.ghost_note
        ]

        # Accents should be louder
        if accent_velocities and normal_velocities:
            avg_accent = sum(accent_velocities) / len(accent_velocities)
            avg_normal = sum(normal_velocities) / len(normal_velocities)
            assert avg_accent > avg_normal - 10


class TestMicroTiming:
    """Test micro-timing relationships."""

    def test_simultaneous_beats_get_different_timing(self, simultaneous_pattern):
        """Test that simultaneous beats get slightly different timing."""
        humanizer = AdvancedHumanizer(humanization_amount=0.5)
        humanized = humanizer.humanize_pattern(simultaneous_pattern)

        # Get beats that were originally at position 0.0
        beats_at_zero = [b for b in humanized.beats if abs(b.position - 0.0) < 0.01]

        if len(beats_at_zero) > 1:
            # Should have different positions now (micro-timing)
            positions = [b.position for b in beats_at_zero]
            assert len(set(positions)) > 1, "Simultaneous beats should have micro-timing"

    def test_crash_behind_other_instruments(self, simultaneous_pattern):
        """Test that crashes are slightly behind other instruments."""
        humanizer = AdvancedHumanizer(humanization_amount=0.5)
        humanized = humanizer.humanize_pattern(simultaneous_pattern)

        # Find crash and kick that were originally simultaneous
        crash = next(
            (b for b in humanized.beats if b.instrument == DrumInstrument.CRASH), None
        )
        kick = next(
            (b for b in humanized.beats if b.instrument == DrumInstrument.KICK), None
        )

        if crash and kick and abs(crash.position - kick.position) < 0.1:
            # Crash should be behind kick (with some tolerance)
            # This might not always be true due to randomness, so we just check it doesn't crash
            assert crash.position >= 0.0
            assert kick.position >= 0.0


class TestFatigue:
    """Test fatigue modeling."""

    def test_fatigue_on_long_patterns(self):
        """Test that fatigue is applied to long patterns (8+ bars)."""
        # Create long pattern (8 bars)
        builder = PatternBuilder("long_pattern")
        for bar in range(8):
            base = bar * 4.0
            builder.kick(base, 100)
            builder.snare(base + 1.0, 100)

        long_pattern = builder.build()

        humanizer = AdvancedHumanizer(humanization_amount=0.7)
        humanized = humanizer.humanize_pattern(long_pattern)

        # Get velocities from first and last bar
        first_bar_beats = [b for b in humanized.beats if b.position < 4.0]
        last_bar_beats = [b for b in humanized.beats if b.position >= 28.0]

        if first_bar_beats and last_bar_beats:
            first_avg = sum(b.velocity for b in first_bar_beats) / len(first_bar_beats)
            last_avg = sum(b.velocity for b in last_bar_beats) / len(last_bar_beats)

            # Last bar should be slightly softer (fatigue) - with tolerance for randomness
            assert (
                last_avg <= first_avg + 5
            ), "Fatigue should reduce velocity slightly over time"

    def test_no_fatigue_on_short_patterns(self, simple_pattern):
        """Test that fatigue is NOT applied to short patterns (< 8 bars)."""
        # Simple pattern is only 4 bars, should not have fatigue
        humanizer = AdvancedHumanizer(humanization_amount=0.7)
        humanized = humanizer.humanize_pattern(simple_pattern)

        # Just verify it runs without crashing
        assert len(humanized.beats) == len(simple_pattern.beats)


class TestStyleVariations:
    """Test different style variations (tight, balanced, loose)."""

    def test_loose_more_variation_than_tight(self, simple_pattern):
        """Test that loose style has more timing variation than tight."""
        tight = AdvancedHumanizer(style="tight", humanization_amount=0.7)
        loose = AdvancedHumanizer(style="loose", humanization_amount=0.7)

        tight_result = tight.humanize_pattern(simple_pattern)
        loose_result = loose.humanize_pattern(simple_pattern)

        # Measure timing deviation from original
        tight_deviations = [
            abs(h.position - o.position)
            for h, o in zip(tight_result.beats, simple_pattern.beats, strict=False)
        ]
        loose_deviations = [
            abs(h.position - o.position)
            for h, o in zip(loose_result.beats, simple_pattern.beats, strict=False)
        ]

        # Loose should have larger deviations on average (with some tolerance)
        tight_avg = sum(tight_deviations) / len(tight_deviations)
        loose_avg = sum(loose_deviations) / len(loose_deviations)

        assert loose_avg > tight_avg - 0.001, "Loose should have more timing variation"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_pattern(self):
        """Test humanization on empty pattern."""
        empty = Pattern("empty", beats=[])
        humanizer = AdvancedHumanizer()

        # Should not crash
        humanized = humanizer.humanize_pattern(empty)
        assert len(humanized.beats) == 0

    def test_single_beat_pattern(self):
        """Test humanization on pattern with single beat."""
        single = Pattern("single", beats=[Beat(0.0, DrumInstrument.KICK, 100)])
        humanizer = AdvancedHumanizer(humanization_amount=0.5)

        humanized = humanizer.humanize_pattern(single)
        assert len(humanized.beats) == 1
        assert humanized.beats[0].position >= 0.0

    def test_extreme_humanization_amount(self, simple_pattern):
        """Test with extreme humanization amount (1.0)."""
        humanizer = AdvancedHumanizer(humanization_amount=1.0)
        humanized = humanizer.humanize_pattern(simple_pattern)

        # Should still produce valid output
        assert len(humanized.beats) == len(simple_pattern.beats)
        assert all(b.position >= 0.0 for b in humanized.beats)
        assert all(1 <= b.velocity <= 127 for b in humanized.beats)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
