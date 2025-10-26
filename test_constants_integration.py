"""Test constants module integration.

This test verifies that the new constants module works correctly
and can be used to replace magic numbers throughout the codebase.
"""

from midi_drums.config import DEFAULTS, TIMING, VELOCITY, VelocityPresets
from midi_drums.models.pattern import Beat, DrumInstrument, PatternBuilder


def test_velocity_constants():
    """Test that velocity constants work in Beat creation."""
    print("Testing velocity constants...")

    # Create beats using constants
    kick = Beat(
        position=0.0,
        instrument=DrumInstrument.KICK,
        velocity=VELOCITY.KICK_NORMAL,
        duration=TIMING.QUARTER,
    )

    snare = Beat(
        position=1.0,
        instrument=DrumInstrument.SNARE,
        velocity=VELOCITY.SNARE_HEAVY,
        duration=TIMING.QUARTER,
    )

    hihat = Beat(
        position=0.0,
        instrument=DrumInstrument.CLOSED_HH,
        velocity=VELOCITY.HIHAT_NORMAL,
        duration=TIMING.EIGHTH,
    )

    assert kick.velocity == 110, f"Expected 110, got {kick.velocity}"
    assert snare.velocity == 127, f"Expected 127, got {snare.velocity}"
    assert hihat.velocity == 80, f"Expected 80, got {hihat.velocity}"

    print("  [OK] Velocity constants work correctly")


def test_timing_constants():
    """Test that timing constants work for positioning."""
    print("Testing timing constants...")

    # Test quarter note positions
    assert TIMING.QUARTER == 1.0
    assert TIMING.HALF == 2.0
    assert TIMING.WHOLE == 4.0

    # Test subdivisions
    assert TIMING.EIGHTH == 0.5
    assert TIMING.SIXTEENTH == 0.25

    # Test triplets
    assert abs(TIMING.EIGHTH_TRIPLET - (1.0 / 3.0)) < 0.0001

    print("  [OK] Timing constants are accurate")


def test_pattern_builder_integration():
    """Test PatternBuilder with constants."""
    print("Testing PatternBuilder integration...")

    builder = PatternBuilder("test_pattern")

    # Build pattern using constants
    for i in range(4):
        builder.kick(i * TIMING.QUARTER, VELOCITY.KICK_NORMAL)

    for i in [1, 3]:  # Snare on 2 and 4
        builder.snare(i * TIMING.QUARTER, VELOCITY.SNARE_NORMAL)

    for i in range(8):
        builder.hihat(i * TIMING.EIGHTH, VELOCITY.HIHAT_NORMAL)

    pattern = builder.build()

    # 4 kicks + 2 snares + 8 hihats = 14 beats total
    assert (
        len(pattern.beats) == 14
    ), f"Expected 14 beats, got {len(pattern.beats)}"
    print(
        f"  [OK] Built pattern with {len(pattern.beats)} beats using constants"
    )


def test_velocity_presets():
    """Test velocity preset ranges."""
    print("Testing velocity presets...")

    # Metal presets should be high
    metal_kick_min, metal_kick_max = VelocityPresets.METAL_KICK
    assert metal_kick_min >= 120, "Metal kick should be loud"

    # Jazz presets should be lower
    jazz_kick_min, jazz_kick_max = VelocityPresets.JAZZ_KICK
    assert jazz_kick_max <= 95, "Jazz kick should be subtle"

    print("  [OK] Velocity presets configured correctly")


def test_defaults():
    """Test generation defaults."""
    print("Testing generation defaults...")

    assert DEFAULTS.TEMPO_DEFAULT == 120
    assert DEFAULTS.COMPLEXITY_DEFAULT == 0.5
    assert DEFAULTS.HUMANIZATION_DEFAULT == 0.3
    assert DEFAULTS.BARS_VERSE == 8
    assert DEFAULTS.BARS_CHORUS == 8

    print("  [OK] Generation defaults loaded")


def test_constant_immutability():
    """Test that constants are truly immutable (frozen)."""
    print("Testing constant immutability...")

    try:
        VELOCITY.KICK_NORMAL = 999  # Should fail
        raise AssertionError("Should not be able to modify frozen constant")
    except AttributeError:
        print("  [OK] Constants are immutable (frozen dataclass)")


if __name__ == "__main__":
    print("=" * 60)
    print("Constants Module Integration Tests")
    print("=" * 60)

    test_velocity_constants()
    test_timing_constants()
    test_pattern_builder_integration()
    test_velocity_presets()
    test_defaults()
    test_constant_immutability()

    print("=" * 60)
    print("All tests passed! Constants module ready for use.")
    print("=" * 60)
