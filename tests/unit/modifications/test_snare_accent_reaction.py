"""Tests for SnareAccentReaction (riff accents -> snare reinforce/stab)."""

from midi_drums.config import VELOCITY
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.riff_accent import RiffAccentMap
from midi_drums.generation.builders.pattern_builder import PatternBuilder
from midi_drums.modifications.riff_lock import RiffLockTransform
from midi_drums.modifications.snare_accent_reaction import SnareAccentReaction


def basic_pattern():
    builder = PatternBuilder("basic")
    builder.kick(0.0, VELOCITY.KICK_NORMAL)
    builder.kick(2.0, VELOCITY.KICK_NORMAL)
    builder.snare(1.0, VELOCITY.SNARE_NORMAL)
    builder.snare(3.0, VELOCITY.SNARE_NORMAL)
    for i in range(8):
        builder.hihat(i * 0.5, VELOCITY.HIHAT_NORMAL)
    return builder.build()


def snares(pattern):
    return [b for b in pattern.beats if b.instrument == DrumInstrument.SNARE]


def kicks(pattern):
    return [b for b in pattern.beats if b.instrument == DrumInstrument.KICK]


# ── reinforce ────────────────────────────────────────────────────────────


def pattern_with_accent_headroom():
    # Snare at 1.0 sits below the pattern's own accented-snare ceiling
    # (set by the accented hit at 3.0), leaving room for reinforce to
    # boost it.
    builder = PatternBuilder("headroom")
    builder.kick(0.0, VELOCITY.KICK_NORMAL)
    builder.kick(2.0, VELOCITY.KICK_NORMAL)
    builder.snare(1.0, VELOCITY.SNARE_LIGHT)
    builder.pattern.add_beat(
        3.0, DrumInstrument.SNARE, VELOCITY.SNARE_ACCENT, accent=True
    )
    return builder.build()


def test_reinforce_boosts_velocity_in_tolerance():
    pattern = pattern_with_accent_headroom()
    accents = RiffAccentMap.from_positions([(1.0, 1.0)], beats_per_bar=4.0)

    result = SnareAccentReaction(riff_accents=accents, mode="reinforce").apply(
        pattern, intensity=1.0
    )

    boosted = next(s for s in snares(result) if abs(s.position - 1.0) < 1e-6)
    original = next(s for s in snares(pattern) if abs(s.position - 1.0) < 1e-6)
    assert boosted.velocity > original.velocity
    assert boosted.accent is True
    # The unrelated (already-accented) snare at 3.0 is untouched.
    other = next(s for s in snares(result) if abs(s.position - 3.0) < 1e-6)
    assert other.velocity == VELOCITY.SNARE_ACCENT


def test_reinforce_no_op_out_of_tolerance():
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions([(1.5, 1.0)], beats_per_bar=4.0)

    result = SnareAccentReaction(
        riff_accents=accents,
        mode="reinforce",
        reinforce_tolerance_beats=0.125,
    ).apply(pattern, intensity=1.0)

    assert [(s.position, s.velocity) for s in snares(result)] == [
        (s.position, s.velocity) for s in snares(pattern)
    ]


def test_reinforce_excludes_ghost_notes():
    builder = PatternBuilder("ghosts")
    builder.pattern.add_beat(
        1.0, DrumInstrument.SNARE, VELOCITY.SNARE_GHOST, ghost_note=True
    )
    pattern = builder.build()
    accents = RiffAccentMap.from_positions([(1.0, 1.0)], beats_per_bar=4.0)

    result = SnareAccentReaction(riff_accents=accents, mode="reinforce").apply(
        pattern, intensity=1.0
    )

    assert snares(result)[0].velocity == VELOCITY.SNARE_GHOST


def test_reinforce_never_exceeds_pattern_accent_ceiling():
    builder = PatternBuilder("ceiling")
    builder.snare(1.0, VELOCITY.SNARE_LIGHT)
    builder.pattern.add_beat(
        3.0, DrumInstrument.SNARE, VELOCITY.SNARE_ACCENT, accent=True
    )
    pattern = builder.build()
    accents = RiffAccentMap.from_positions([(1.0, 1.0)], beats_per_bar=4.0)

    result = SnareAccentReaction(riff_accents=accents, mode="reinforce").apply(
        pattern, intensity=1.0
    )

    boosted = next(s for s in snares(result) if abs(s.position - 1.0) < 1e-6)
    assert boosted.velocity <= VELOCITY.SNARE_ACCENT


# ── stab ─────────────────────────────────────────────────────────────────


def test_stab_inserts_unison_snare_at_locked_kick():
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions([(1.5, 0.9)], beats_per_bar=4.0)

    locked = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )
    assert any(abs(k.position - 1.5) < 1e-6 for k in kicks(locked))

    result = SnareAccentReaction(
        riff_accents=accents, mode="stab", stab_threshold=0.85
    ).apply(locked, intensity=1.0)

    stabbed = [s for s in snares(result) if abs(s.position - 1.5) < 1e-6]
    assert len(stabbed) == 1
    matched_kick = next(
        k for k in kicks(result) if abs(k.position - 1.5) < 1e-6
    )
    assert stabbed[0].velocity == matched_kick.velocity
    assert stabbed[0].accent is True
    assert stabbed[0].ghost_note is False


def test_stab_skips_when_no_kick_under_accent():
    # A strong-enough-to-stab accent that riff-lock's own budget rejected
    # (min_kick_spacing_beats crowds it out) -> no kick landed there ->
    # stab must not insert a snare hit out of nowhere.
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions(
        [(0.0, 0.95), (0.1, 0.9)], beats_per_bar=4.0
    )

    locked = RiffLockTransform(
        riff_accents=accents, min_kick_spacing_beats=1.0, max_kicks_per_bar=1
    ).apply(pattern, intensity=1.0)
    assert not any(abs(k.position - 0.1) < 1e-6 for k in kicks(locked))

    result = SnareAccentReaction(
        riff_accents=accents,
        mode="stab",
        stab_threshold=0.85,
        min_stab_spacing_beats=0.05,
    ).apply(locked, intensity=1.0)

    assert not any(abs(s.position - 0.1) < 1e-6 for s in snares(result))


def test_stab_collapses_to_reinforce_near_existing_snare():
    pattern = pattern_with_accent_headroom()
    accents = RiffAccentMap.from_positions([(1.0, 0.9)], beats_per_bar=4.0)

    locked = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )

    result = SnareAccentReaction(
        riff_accents=accents,
        mode="stab",
        stab_threshold=0.85,
        stab_collapse_tolerance_beats=0.125,
    ).apply(locked, intensity=1.0)

    matches = [s for s in snares(result) if abs(s.position - 1.0) < 1e-6]
    assert len(matches) == 1
    assert matches[0].velocity > VELOCITY.SNARE_LIGHT


def test_stab_wraparound_at_bar_boundary():
    builder = PatternBuilder("wrap")
    builder.kick(3.9, VELOCITY.KICK_NORMAL)
    pattern = builder.build()
    accents = RiffAccentMap.from_positions([(0.05, 0.95)], beats_per_bar=4.0)

    locked = RiffLockTransform(
        riff_accents=accents, kick_tolerance_beats=0.2
    ).apply(pattern, intensity=1.0)
    assert abs(kicks(locked)[0].position - 0.05) < 1e-6

    result = SnareAccentReaction(
        riff_accents=accents,
        mode="stab",
        stab_threshold=0.85,
        stab_kick_tolerance_beats=0.2,
    ).apply(locked, intensity=1.0)

    assert any(abs(s.position - 0.05) < 1e-6 for s in snares(result))


def test_stab_respects_max_stabs_per_bar_budget():
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions(
        [(i * 0.5, 0.9) for i in range(8)], beats_per_bar=4.0
    )

    locked = RiffLockTransform(
        riff_accents=accents, min_kick_spacing_beats=0.01, max_kicks_per_bar=8
    ).apply(pattern, intensity=1.0)

    result = SnareAccentReaction(
        riff_accents=accents,
        mode="stab",
        stab_threshold=0.85,
        max_stabs_per_bar=2,
        min_stab_spacing_beats=0.01,
    ).apply(locked, intensity=1.0)

    new_stabs = len(snares(result)) - len(snares(locked))
    assert new_stabs <= 2


def test_stab_excludes_ghost_notes_as_collapse_targets():
    builder = PatternBuilder("ghost_collapse")
    builder.kick(1.0, VELOCITY.KICK_NORMAL)
    builder.pattern.add_beat(
        1.0, DrumInstrument.SNARE, VELOCITY.SNARE_GHOST, ghost_note=True
    )
    pattern = builder.build()
    accents = RiffAccentMap.from_positions([(1.0, 0.9)], beats_per_bar=4.0)

    result = SnareAccentReaction(
        riff_accents=accents, mode="stab", stab_threshold=0.85
    ).apply(pattern, intensity=1.0)

    non_ghost_at_1_0 = [
        s
        for s in snares(result)
        if abs(s.position - 1.0) < 1e-6 and not s.ghost_note
    ]
    assert len(non_ghost_at_1_0) == 1


def test_stab_determinism_same_input_twice_gives_identical_output():
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions(
        [(0.1, 0.9), (1.5, 0.95), (2.6, 0.88)], beats_per_bar=4.0
    )
    locked = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )

    transform = SnareAccentReaction(
        riff_accents=accents, mode="stab", stab_threshold=0.85
    )
    result_a = transform.apply(locked, intensity=0.7)
    result_b = transform.apply(locked, intensity=0.7)

    beats_a = [(b.position, b.instrument, b.velocity) for b in result_a.beats]
    beats_b = [(b.position, b.instrument, b.velocity) for b in result_b.beats]
    assert beats_a == beats_b


def test_empty_accent_map_leaves_pattern_unchanged():
    pattern = basic_pattern()
    accents = RiffAccentMap(accents=(), beats_per_bar=4.0)

    for mode in ("reinforce", "stab"):
        result = SnareAccentReaction(riff_accents=accents, mode=mode).apply(
            pattern, intensity=1.0
        )
        assert [(b.position, b.instrument) for b in result.beats] == [
            (b.position, b.instrument) for b in pattern.beats
        ]
        assert result is not pattern


def test_reinforce_does_not_force_accent_flag_when_no_velocity_change():
    # A snare already at the pattern's own ceiling gets no velocity boost
    # from reinforce, so it must not be force-flipped to accent=True just
    # for being the nearest match - that would grant it accent-only
    # humanization treatment it didn't earn.
    builder = PatternBuilder("no_change")
    builder.snare(1.0, VELOCITY.SNARE_ACCENT)
    builder.pattern.add_beat(
        3.0, DrumInstrument.SNARE, VELOCITY.SNARE_ACCENT, accent=True
    )
    pattern = builder.build()
    accents = RiffAccentMap.from_positions([(1.0, 1.0)], beats_per_bar=4.0)

    result = SnareAccentReaction(riff_accents=accents, mode="reinforce").apply(
        pattern, intensity=1.0
    )

    touched = next(s for s in snares(result) if abs(s.position - 1.0) < 1e-6)
    assert touched.velocity == VELOCITY.SNARE_ACCENT
    assert touched.accent is False


def test_stab_does_not_duplicate_snare_when_two_accents_share_a_kick():
    # Two stab accents close enough together to both fall within
    # stab_kick_tolerance_beats of the SAME locked kick must not both
    # insert a snare hit there - the second must find no unclaimed kick
    # and skip, rather than stacking a duplicate on top of the first.
    pattern = basic_pattern()
    accents = RiffAccentMap.from_positions(
        [(1.5, 0.95), (1.55, 0.9)], beats_per_bar=4.0
    )
    locked = RiffLockTransform(
        riff_accents=accents, min_kick_spacing_beats=0.01, max_kicks_per_bar=1
    ).apply(pattern, intensity=1.0)
    assert len(kicks(locked)) == len(kicks(pattern)) + 1
    new_kick = next(k for k in kicks(locked) if abs(k.position - 1.5) < 1e-6)

    result = SnareAccentReaction(
        riff_accents=accents,
        mode="stab",
        stab_threshold=0.85,
        min_stab_spacing_beats=0.02,
        stab_kick_tolerance_beats=0.2,
    ).apply(locked, intensity=1.0)

    stabbed_at_kick = [
        s for s in snares(result) if abs(s.position - new_kick.position) < 1e-6
    ]
    assert len(stabbed_at_kick) == 1


def test_stab_collapse_keeps_strongest_accents_boost_not_last_writer():
    # Accents arrive strength-descending (select_accents); when two both
    # collapse onto the same existing snare, the first (strongest) boost
    # must win, not be silently overwritten by a later, weaker one.
    pattern = pattern_with_accent_headroom()
    accents = RiffAccentMap.from_positions(
        [(1.0, 0.95), (1.02, 0.5)], beats_per_bar=4.0
    )
    locked = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )

    result = SnareAccentReaction(
        riff_accents=accents,
        mode="stab",
        stab_threshold=0.4,
        min_stab_spacing_beats=0.01,
        stab_collapse_tolerance_beats=0.125,
    ).apply(locked, intensity=1.0)

    boosted = next(s for s in snares(result) if abs(s.position - 1.0) < 1e-6)
    ceiling = VELOCITY.SNARE_ACCENT
    current = VELOCITY.SNARE_LIGHT
    strongest_expected = min(
        127, max(current, current + round((ceiling - current) * 0.95))
    )
    assert boosted.velocity == strongest_expected


def test_generation_parameters_rejects_invalid_snare_mode():
    from midi_drums.core.value_objects.generation_parameters import (
        GenerationParameters,
    )

    try:
        GenerationParameters(genre="metal", riff_snare_mode="bogus")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for riff_snare_mode='bogus'")


def test_invalid_mode_raises():
    accents = RiffAccentMap.from_positions([(0.0, 0.9)], beats_per_bar=4.0)
    try:
        SnareAccentReaction(riff_accents=accents, mode="off")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for mode='off'")
