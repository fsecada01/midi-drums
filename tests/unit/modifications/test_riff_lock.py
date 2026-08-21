"""Tests for RiffLockTransform (audio riff -> kick-locked drum pattern)."""

from midi_drums.config import VELOCITY
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.riff_accent import RiffAccentMap
from midi_drums.generation.builders.pattern_builder import PatternBuilder
from midi_drums.modifications.riff_lock import (
    RiffLockTransform,
    _circular_distance,
)


def basic_pattern():
    builder = PatternBuilder("basic")
    builder.kick(0.0, VELOCITY.KICK_NORMAL)
    builder.kick(2.0, VELOCITY.KICK_NORMAL)
    builder.snare(1.0, VELOCITY.SNARE_NORMAL)
    builder.snare(3.0, VELOCITY.SNARE_NORMAL)
    for i in range(8):
        builder.hihat(i * 0.5, VELOCITY.HIHAT_NORMAL)
    return builder.build()


def kicks(pattern):
    return [b for b in pattern.beats if b.instrument == DrumInstrument.KICK]


def non_kicks(pattern):
    return [b for b in pattern.beats if b.instrument != DrumInstrument.KICK]


def test_circular_distance_wraps_at_bar_boundary():
    assert abs(_circular_distance(3.875, 0.0, 4.0) - 0.125) < 1e-9
    assert abs(_circular_distance(0.0, 3.875, 4.0) - 0.125) < 1e-9
    assert _circular_distance(1.0, 3.0, 4.0) == 2.0


def test_snap_within_tolerance_moves_existing_kick():
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions([(0.1, 0.9)], beats_per_bar=4.0)

    result = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )

    result_kicks = kicks(result)
    assert len(result_kicks) == len(kicks(pattern))
    assert any(abs(k.position - 0.1) < 1e-6 for k in result_kicks)
    # The other original kick (at 2.0) is untouched.
    assert any(abs(k.position - 2.0) < 1e-6 for k in result_kicks)


def test_insert_when_no_kick_nearby():
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions([(1.5, 0.9)], beats_per_bar=4.0)

    result = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )

    result_kicks = kicks(result)
    assert len(result_kicks) == len(kicks(pattern)) + 1
    assert any(abs(k.position - 1.5) < 1e-6 for k in result_kicks)


def test_wraparound_accent_snaps_kick_across_bar_boundary():
    builder = PatternBuilder("wrap")
    builder.kick(3.9, VELOCITY.KICK_NORMAL)
    pattern = builder.build()

    accents = RiffAccentMap.from_positions([(0.05, 0.9)], beats_per_bar=4.0)
    result = RiffLockTransform(
        riff_accents=accents, kick_tolerance_beats=0.2
    ).apply(pattern, intensity=1.0)

    result_kicks = kicks(result)
    assert len(result_kicks) == 1
    # 3.9 should snap to 0.05 (wrapping), not stay far away or double up.
    assert abs(result_kicks[0].position - 0.05) < 1e-6


def test_max_kicks_per_bar_budget_is_respected():
    # removal_strength=1.0/max_removal_fraction=1.0/preserve_downbeat=False
    # strips every unmatched original kick, isolating the resulting kick
    # count to exactly the number of riff-locked accents so the
    # max_kicks_per_bar budget can be checked directly against it.
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions(
        [(i * 0.5, 0.9) for i in range(8)], beats_per_bar=4.0
    )

    result = RiffLockTransform(
        riff_accents=accents,
        max_kicks_per_bar=3,
        min_kick_spacing_beats=0.01,
        removal_strength=1.0,
        max_removal_fraction=1.0,
        preserve_downbeat=False,
    ).apply(pattern, intensity=1.0)

    assert len(kicks(result)) == 3


def test_min_kick_spacing_filters_close_accents():
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions(
        [(1.5, 0.9), (1.55, 0.8)], beats_per_bar=4.0
    )

    result = RiffLockTransform(
        riff_accents=accents, min_kick_spacing_beats=0.25
    ).apply(pattern, intensity=1.0)

    # Only the stronger of the two close accents should be selected.
    inserted_near_1_5 = [k for k in kicks(result) if 1.4 < k.position < 1.7]
    assert len(inserted_near_1_5) == 1


def test_empty_accent_map_leaves_pattern_unchanged():
    pattern = basic_pattern()
    accents = RiffAccentMap(accents=(), beats_per_bar=4.0)

    result = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )

    assert [(b.position, b.instrument) for b in result.beats] == [
        (b.position, b.instrument) for b in pattern.beats
    ]
    assert result is not pattern


def test_kickless_pattern_inserts_from_accents():
    builder = PatternBuilder("no_kicks")
    builder.snare(1.0, VELOCITY.SNARE_NORMAL)
    pattern = builder.build()

    accents = RiffAccentMap.from_positions([(0.0, 1.0)], beats_per_bar=4.0)
    result = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )

    assert len(kicks(result)) == 1
    assert kicks(result)[0].velocity > 0


def test_non_kick_instruments_are_untouched():
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions([(0.0, 0.9)], beats_per_bar=4.0)

    result = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )

    original_non_kicks = sorted(
        (b.position, b.instrument.value, b.velocity) for b in non_kicks(pattern)
    )
    result_non_kicks = sorted(
        (b.position, b.instrument.value, b.velocity) for b in non_kicks(result)
    )
    assert original_non_kicks == result_non_kicks


def test_determinism_same_input_twice_gives_identical_output():
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions(
        [(0.1, 0.9), (1.5, 0.7), (2.6, 0.8)], beats_per_bar=4.0
    )

    transform = RiffLockTransform(riff_accents=accents, removal_strength=0.5)
    result_a = transform.apply(pattern, intensity=0.7)
    result_b = transform.apply(pattern, intensity=0.7)

    beats_a = [(b.position, b.instrument, b.velocity) for b in result_a.beats]
    beats_b = [(b.position, b.instrument, b.velocity) for b in result_b.beats]
    assert beats_a == beats_b


def test_intensity_blending_partial_snap():
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions([(0.4, 0.9)], beats_per_bar=4.0)

    result = RiffLockTransform(
        riff_accents=accents, kick_tolerance_beats=0.5
    ).apply(pattern, intensity=0.5)

    snapped = [k for k in kicks(result) if 0.0 < k.position < 0.4]
    assert len(snapped) == 1
    # Halfway between 0.0 and 0.4 at intensity=0.5.
    assert abs(snapped[0].position - 0.2) < 1e-6


def test_removal_strength_zero_keeps_unmatched_kicks_by_default():
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions([(1.5, 0.9)], beats_per_bar=4.0)

    result = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )

    # Original kicks at 0.0 and 2.0 remain untouched, plus the new one.
    assert len(kicks(result)) == 3


def test_removal_strength_preserves_downbeat():
    builder = PatternBuilder("downbeat")
    builder.kick(0.0, VELOCITY.KICK_LIGHT)
    builder.kick(2.0, VELOCITY.KICK_LIGHT)
    pattern = builder.build()

    accents = RiffAccentMap.from_positions([(1.0, 0.9)], beats_per_bar=4.0)
    result = RiffLockTransform(
        riff_accents=accents,
        removal_strength=1.0,
        max_removal_fraction=1.0,
        preserve_downbeat=True,
    ).apply(pattern, intensity=1.0)

    result_positions = [k.position for k in kicks(result)]
    assert 0.0 in result_positions
