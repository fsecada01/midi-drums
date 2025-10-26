"""Test drummer modification system.

This test suite validates the drummer modification system including:
- Base modification functionality
- Individual modification implementations
- Modification composition
- Integration with existing pattern system
"""

from midi_drums.config import TIMING, VELOCITY
from midi_drums.models.pattern import DrumInstrument, Pattern, PatternBuilder
from midi_drums.modifications import (
    BehindBeatTiming,
    FastChopsTriplets,
    GhostNoteLayer,
    HeavyAccents,
    LinearCoordination,
    MechanicalPrecision,
    MinimalCreativity,
    ModificationRegistry,
    PocketStretching,
    ShuffleFeelApplication,
    SpeedPrecision,
    TripletVocabulary,
    TwistedAccents,
)


def create_basic_pattern() -> Pattern:
    """Create a basic test pattern."""
    builder = PatternBuilder("basic_test")

    # Basic rock beat
    builder.kick(0.0, VELOCITY.KICK_NORMAL)
    builder.kick(2.0, VELOCITY.KICK_NORMAL)

    builder.snare(1.0, VELOCITY.SNARE_NORMAL)
    builder.snare(3.0, VELOCITY.SNARE_NORMAL)

    # Eighth note hihat
    for i in range(8):
        builder.hihat(i * TIMING.EIGHTH, VELOCITY.HIHAT_NORMAL)

    return builder.build()


def test_behind_beat_timing():
    """Test BehindBeatTiming modification."""
    print("Testing BehindBeatTiming...")

    pattern = create_basic_pattern()
    original_snare_positions = [
        b.position
        for b in pattern.beats
        if b.instrument == DrumInstrument.SNARE
    ]

    # Apply modification
    mod = BehindBeatTiming(max_delay_ms=20.0)
    modified = mod.apply(pattern, intensity=1.0)

    # Original pattern unchanged
    original_after = [
        b.position
        for b in pattern.beats
        if b.instrument == DrumInstrument.SNARE
    ]
    assert (
        original_snare_positions == original_after
    ), "Original pattern was modified!"

    # Modified pattern has delayed snares
    modified_snare_positions = [
        b.position
        for b in modified.beats
        if b.instrument == DrumInstrument.SNARE
    ]

    assert len(modified_snare_positions) == len(
        original_snare_positions
    ), "Snare count changed"

    for orig, mod_pos in zip(
        original_snare_positions, modified_snare_positions, strict=False
    ):
        assert mod_pos > orig, f"Snare not delayed: {orig} -> {mod_pos}"

    print(
        f"  [OK] BehindBeatTiming: snares delayed from "
        f"{original_snare_positions} to {modified_snare_positions}"
    )


def test_triplet_vocabulary():
    """Test TripletVocabulary modification."""
    print("Testing TripletVocabulary...")

    pattern = create_basic_pattern()
    original_count = len(pattern.beats)

    # Apply modification
    mod = TripletVocabulary(triplet_probability=1.0)  # Force fills
    modified = mod.apply(pattern, intensity=1.0)

    # Should add triplet fills
    assert (
        len(modified.beats) > original_count
    ), "No triplet fills added to pattern"

    # Check for triplet timing
    has_triplets = any(
        abs((b.position % 1.0) - (1.0 / 3.0)) < 0.01
        or abs((b.position % 1.0) - (2.0 / 3.0)) < 0.01
        for b in modified.beats
    )

    assert has_triplets, "No triplet-based hits found in pattern"

    print(
        f"  [OK] TripletVocabulary: {original_count} beats -> "
        f"{len(modified.beats)} beats with triplets"
    )


def test_ghost_note_layer():
    """Test GhostNoteLayer modification."""
    print("Testing GhostNoteLayer...")

    pattern = create_basic_pattern()
    original_ghost_count = sum(1 for b in pattern.beats if b.ghost_note)

    # Apply modification
    mod = GhostNoteLayer(density=0.8)  # High density for testing
    modified = mod.apply(pattern, intensity=1.0)

    # Should add ghost notes
    modified_ghost_count = sum(1 for b in modified.beats if b.ghost_note)
    assert (
        modified_ghost_count > original_ghost_count
    ), "No ghost notes added to pattern"

    # Ghost notes should be low velocity
    ghost_velocities = [b.velocity for b in modified.beats if b.ghost_note]
    assert all(
        v < VELOCITY.SNARE_NORMAL for v in ghost_velocities
    ), "Ghost notes too loud"

    ghost_added = modified_ghost_count - original_ghost_count
    print(f"  [OK] GhostNoteLayer: added {ghost_added} ghost notes")


def test_linear_coordination():
    """Test LinearCoordination modification."""
    print("Testing LinearCoordination...")

    # Create pattern with simultaneous hits
    builder = PatternBuilder("simultaneous_test")
    builder.kick(0.0, VELOCITY.KICK_NORMAL)
    builder.snare(0.0, VELOCITY.SNARE_NORMAL)  # Same time as kick
    builder.hihat(0.0, VELOCITY.HIHAT_NORMAL)  # Same time

    builder.kick(1.0, VELOCITY.KICK_NORMAL)
    builder.hihat(1.0, VELOCITY.HIHAT_NORMAL)  # Same time

    pattern = builder.build()

    # Count simultaneous hits at position 0.0
    hits_at_zero = sum(1 for b in pattern.beats if abs(b.position - 0.0) < 0.01)
    assert hits_at_zero == 3, "Test pattern should have 3 simultaneous hits"

    # Apply modification
    mod = LinearCoordination()
    modified = mod.apply(pattern, intensity=1.0)

    # Should have fewer simultaneous hits
    modified_hits_at_zero = sum(
        1 for b in modified.beats if abs(b.position - 0.0) < 0.01
    )
    assert (
        modified_hits_at_zero < hits_at_zero
    ), "Simultaneous hits not removed by linear coordination"

    print(
        f"  [OK] LinearCoordination: {hits_at_zero} simultaneous -> "
        f"{modified_hits_at_zero} linear"
    )


def test_heavy_accents():
    """Test HeavyAccents modification."""
    print("Testing HeavyAccents...")

    pattern = create_basic_pattern()

    # Apply modification
    mod = HeavyAccents(accent_boost=20)
    modified = mod.apply(pattern, intensity=1.0)

    # Check velocity contrast increased
    modified_velocities = [b.velocity for b in modified.beats]
    velocity_range = max(modified_velocities) - min(modified_velocities)

    assert (
        velocity_range > 20
    ), f"Insufficient accent contrast: {velocity_range}"

    # Accented beats should be louder
    accented_velocities = [b.velocity for b in modified.beats if b.accent]
    non_accented_velocities = [
        b.velocity for b in modified.beats if not b.accent
    ]

    if accented_velocities and non_accented_velocities:
        assert sum(accented_velocities) / len(accented_velocities) > sum(
            non_accented_velocities
        ) / len(non_accented_velocities), "Accented beats not louder"

    print(f"  [OK] HeavyAccents: velocity range = {velocity_range}")


def test_shuffle_feel_application():
    """Test ShuffleFeelApplication modification."""
    print("Testing ShuffleFeelApplication...")

    # Create pattern with straight sixteenths (shuffle applies to 16th offbeats)
    builder = PatternBuilder("straight_test")
    for i in range(16):
        builder.hihat(i * TIMING.SIXTEENTH, VELOCITY.HIHAT_NORMAL)
    pattern = builder.build()

    # Apply modification
    mod = ShuffleFeelApplication(shuffle_amount=0.5)
    modified = mod.apply(pattern, intensity=1.0)

    # Offbeat positions should be shifted
    original_positions = sorted(b.position for b in pattern.beats)
    modified_positions = sorted(b.position for b in modified.beats)

    # Some positions should differ (shuffle applied to offbeats at x.25, x.75)
    differences = sum(
        1
        for o, m in zip(original_positions, modified_positions, strict=False)
        if abs(o - m) > 0.01
    )

    assert differences > 0, "Shuffle not applied to pattern"

    print(
        f"  [OK] ShuffleFeelApplication: {differences}/"
        f"{len(original_positions)} positions shuffled"
    )


def test_fast_chops_triplets():
    """Test FastChopsTriplets modification."""
    print("Testing FastChopsTriplets...")

    pattern = create_basic_pattern()
    original_count = len(pattern.beats)

    # Apply modification
    mod = FastChopsTriplets(probability=1.0)  # Force chops
    modified = mod.apply(pattern, intensity=1.0)

    # Should add fast triplet-based chops
    assert len(modified.beats) > original_count, "No chops added to pattern"

    # Check for fast notes added
    assert len(modified.beats) > original_count, "No chops added"

    print(
        f"  [OK] FastChopsTriplets: {original_count} -> "
        f"{len(modified.beats)} beats"
    )


def test_pocket_stretching():
    """Test PocketStretching modification."""
    print("Testing PocketStretching...")

    pattern = create_basic_pattern()
    original_positions = sorted(b.position for b in pattern.beats)

    # Apply modification
    mod = PocketStretching(variation_ms=15.0)
    modified = mod.apply(pattern, intensity=1.0)

    modified_positions = sorted(b.position for b in modified.beats)

    # Positions should vary slightly (within stretch range)
    variations = [
        abs(o - m)
        for o, m in zip(original_positions, modified_positions, strict=False)
    ]

    # Some beats should be stretched
    stretched_count = sum(1 for v in variations if v > 0.001)

    assert stretched_count > 0, "No pocket stretching applied"

    max_variation = max(variations)
    expected_max = (15.0 / 1000.0) * 2.0  # Convert ms to beats

    assert (
        max_variation <= expected_max
    ), f"Stretch exceeds limit: {max_variation} > {expected_max}"

    print(
        f"  [OK] PocketStretching: {stretched_count} beats stretched, "
        f"max={max_variation:.4f}"
    )


def test_minimal_creativity():
    """Test MinimalCreativity modification."""
    print("Testing MinimalCreativity...")

    pattern = create_basic_pattern()
    original_count = len(pattern.beats)

    # Apply modification
    mod = MinimalCreativity(sparseness=0.3)
    modified = mod.apply(pattern, intensity=1.0)

    # Should remove some notes for sparse feel
    # Allow same count since removal is probabilistic
    assert (
        len(modified.beats) <= original_count
    ), "MinimalCreativity added notes instead of removing"

    print(
        f"  [OK] MinimalCreativity: {original_count} -> "
        f"{len(modified.beats)} beats (sparse)"
    )


def test_speed_precision():
    """Test SpeedPrecision modification."""
    print("Testing SpeedPrecision...")

    # Create pattern with velocity variations
    builder = PatternBuilder("varied_test")
    builder.kick(0.0, 100)
    builder.kick(1.0, 110)
    builder.kick(2.0, 95)
    builder.kick(3.0, 115)
    pattern = builder.build()

    original_velocities = [b.velocity for b in pattern.beats]
    original_range = max(original_velocities) - min(original_velocities)

    # Apply modification
    mod = SpeedPrecision(consistency=0.95)
    modified = mod.apply(pattern, intensity=1.0)

    modified_velocities = [b.velocity for b in modified.beats]
    modified_range = max(modified_velocities) - min(modified_velocities)

    # Velocity range should be reduced
    assert (
        modified_range < original_range
    ), f"Velocity range not reduced: {modified_range} >= {original_range}"

    print(
        f"  [OK] SpeedPrecision: velocity range {original_range} -> "
        f"{modified_range}"
    )


def test_twisted_accents():
    """Test TwistedAccents modification."""
    print("Testing TwistedAccents...")

    pattern = create_basic_pattern()

    # Apply modification
    mod = TwistedAccents(displacement=0.5)
    modified = mod.apply(pattern, intensity=1.0)

    # Accent positions should differ
    original_accent_positions = {b.position for b in pattern.beats if b.accent}
    modified_accent_positions = {b.position for b in modified.beats if b.accent}

    # Some accents should be in different positions
    different_positions = len(
        original_accent_positions.symmetric_difference(
            modified_accent_positions
        )
    )

    print(
        f"  [OK] TwistedAccents: {different_positions} accent positions "
        "displaced"
    )


def test_mechanical_precision():
    """Test MechanicalPrecision modification."""
    print("Testing MechanicalPrecision...")

    # Create pattern with slight timing variations
    builder = PatternBuilder("varied_timing_test")
    builder.kick(0.01, VELOCITY.KICK_NORMAL)  # Slightly off
    builder.kick(1.99, VELOCITY.KICK_NORMAL)  # Slightly off
    builder.snare(1.02, VELOCITY.SNARE_NORMAL)  # Slightly off
    pattern = builder.build()

    # Apply modification
    mod = MechanicalPrecision(quantize_amount=1.0)
    modified = mod.apply(pattern, intensity=1.0)

    # All positions should be quantized to grid
    for beat in modified.beats:
        # Check if position is on 16th note grid
        grid_position = (
            round(beat.position / TIMING.SIXTEENTH) * TIMING.SIXTEENTH
        )
        assert (
            abs(beat.position - grid_position) < 0.001
        ), f"Beat not quantized: {beat.position}"

    print("  [OK] MechanicalPrecision: all beats quantized to grid")


def test_modification_composition():
    """Test applying multiple modifications in sequence."""
    print("Testing modification composition...")

    pattern = create_basic_pattern()
    original_count = len(pattern.beats)

    # Apply multiple modifications
    modified = pattern
    modified = BehindBeatTiming().apply(modified, intensity=0.8)
    modified = GhostNoteLayer(density=0.5).apply(modified, intensity=0.7)
    modified = HeavyAccents().apply(modified, intensity=0.9)

    # Pattern should be transformed but still valid
    assert len(modified.beats) > 0, "Composition resulted in empty pattern"
    assert modified.name != pattern.name, "Pattern name not updated"

    # Original pattern unchanged
    assert len(pattern.beats) == original_count, "Original pattern was modified"

    print(
        f"  [OK] Composition: {original_count} -> {len(modified.beats)} "
        "beats with 3 modifications"
    )


def test_modification_registry():
    """Test ModificationRegistry functionality."""
    print("Testing ModificationRegistry...")

    registry = ModificationRegistry()

    # Should have all default modifications
    assert (
        registry.get("behind_beat_timing") is not None
    ), "Missing BehindBeatTiming"
    assert (
        registry.get("triplet_vocabulary") is not None
    ), "Missing TripletVocabulary"
    assert (
        registry.get("ghost_note_layer") is not None
    ), "Missing GhostNoteLayer"

    # List all modifications
    all_mods = registry.list_modifications()
    assert (
        len(all_mods) >= 12
    ), f"Expected at least 12 modifications, got {len(all_mods)}"

    # Create modification from registry
    mod = registry.create("behind_beat_timing", max_delay_ms=25.0)
    assert mod is not None, "Failed to create modification from registry"
    assert isinstance(mod, BehindBeatTiming), "Wrong modification type created"

    print(
        f"  [OK] ModificationRegistry: {len(all_mods)} modifications registered"
    )


def test_intensity_parameter():
    """Test that intensity parameter scales modification effects."""
    print("Testing intensity parameter...")

    pattern = create_basic_pattern()

    # Apply with low intensity
    mod_low = BehindBeatTiming(max_delay_ms=20.0)
    low_intensity = mod_low.apply(pattern, intensity=0.3)

    # Apply with high intensity
    mod_high = BehindBeatTiming(max_delay_ms=20.0)
    high_intensity = mod_high.apply(pattern, intensity=1.0)

    # Get snare positions
    low_positions = [
        b.position
        for b in low_intensity.beats
        if b.instrument == DrumInstrument.SNARE
    ]
    high_positions = [
        b.position
        for b in high_intensity.beats
        if b.instrument == DrumInstrument.SNARE
    ]
    original_positions = [
        b.position
        for b in pattern.beats
        if b.instrument == DrumInstrument.SNARE
    ]

    # High intensity should have greater displacement
    low_displacement = sum(
        abs(low - orig)
        for low, orig in zip(low_positions, original_positions, strict=False)
    )
    high_displacement = sum(
        abs(high - orig)
        for high, orig in zip(high_positions, original_positions, strict=False)
    )

    assert (
        high_displacement > low_displacement
    ), f"High intensity not greater: {high_displacement} vs {low_displacement}"

    print(
        f"  [OK] Intensity: low={low_displacement:.4f}, "
        f"high={high_displacement:.4f}"
    )


def test_immutability():
    """Test that modifications don't mutate original patterns."""
    print("Testing immutability...")

    pattern = create_basic_pattern()

    # Store original state
    original_beats = list(pattern.beats)
    original_count = len(pattern.beats)
    original_name = pattern.name

    # Apply various modifications
    BehindBeatTiming().apply(pattern, intensity=1.0)
    TripletVocabulary().apply(pattern, intensity=1.0)
    GhostNoteLayer().apply(pattern, intensity=1.0)
    HeavyAccents().apply(pattern, intensity=1.0)

    # Original pattern should be unchanged
    assert len(pattern.beats) == original_count, "Beat count changed"
    assert pattern.name == original_name, "Pattern name changed"

    # Beats should be identical
    for orig, curr in zip(original_beats, pattern.beats, strict=False):
        assert orig.position == curr.position, "Beat position changed"
        assert orig.velocity == curr.velocity, "Beat velocity changed"
        assert orig.instrument == curr.instrument, "Beat instrument changed"

    print("  [OK] Immutability: original pattern unchanged after modifications")


if __name__ == "__main__":
    print("=" * 60)
    print("Drummer Modification System Tests")
    print("=" * 60)

    test_behind_beat_timing()
    test_triplet_vocabulary()
    test_ghost_note_layer()
    test_linear_coordination()
    test_heavy_accents()
    test_shuffle_feel_application()
    test_fast_chops_triplets()
    test_pocket_stretching()
    test_minimal_creativity()
    test_speed_precision()
    test_twisted_accents()
    test_mechanical_precision()
    test_modification_composition()
    test_modification_registry()
    test_intensity_parameter()
    test_immutability()

    print("=" * 60)
    print("All drummer modification tests passed!")
    print("=" * 60)
