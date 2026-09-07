"""Tests for CymbalAccentReaction (riff accents -> hihat/crash/ride
reinforce/stab), mirroring test_snare_accent_reaction.py's coverage shape
across the three supported kit pieces."""

import pytest

from midi_drums.config import VELOCITY
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.riff_accent import RiffAccentMap
from midi_drums.generation.builders.pattern_builder import PatternBuilder
from midi_drums.modifications.cymbal_accent_reaction import CymbalAccentReaction
from midi_drums.modifications.riff_lock import RiffLockTransform

KIT_PIECES = ["hihat", "crash", "ride", "china"]

# Each kit piece's canonical instrument (what PatternBuilder's convenience
# method places, and what CymbalAccentReaction inserts on a stab) plus the
# normal/light/accent velocities used to build fixtures.
_INSTRUMENT = {
    "hihat": DrumInstrument.CLOSED_HH,
    "crash": DrumInstrument.CRASH,
    "ride": DrumInstrument.RIDE,
    "china": DrumInstrument.CHINA,
}
_NORMAL_VELOCITY = {
    "hihat": VELOCITY.HIHAT_NORMAL,
    "crash": VELOCITY.CRASH_NORMAL,
    "ride": VELOCITY.RIDE_NORMAL,
    "china": VELOCITY.CHINA_NORMAL,
}
_LIGHT_VELOCITY = {
    "hihat": VELOCITY.HIHAT_LIGHT,
    "crash": VELOCITY.CRASH_LIGHT,
    "ride": VELOCITY.RIDE_LIGHT,
    "china": VELOCITY.CHINA_LIGHT,
}
_ACCENT_VELOCITY = {
    "hihat": VELOCITY.HIHAT_ACCENT,
    "crash": VELOCITY.CRASH_ACCENT,
    "ride": VELOCITY.RIDE_ACCENT,
    "china": VELOCITY.CHINA_ACCENT,
}


def _place(builder, kit_piece, position, velocity):
    if kit_piece == "hihat":
        builder.hihat(position, velocity)
    elif kit_piece == "crash":
        builder.crash(position, velocity)
    elif kit_piece == "china":
        builder.pattern.add_beat(position, DrumInstrument.CHINA, velocity)
    else:
        builder.ride(position, velocity)


def basic_pattern(kit_piece):
    builder = PatternBuilder("basic")
    builder.kick(0.0, VELOCITY.KICK_NORMAL)
    builder.kick(2.0, VELOCITY.KICK_NORMAL)
    _place(builder, kit_piece, 1.0, _NORMAL_VELOCITY[kit_piece])
    _place(builder, kit_piece, 3.0, _NORMAL_VELOCITY[kit_piece])
    return builder.build()


def matches(pattern, kit_piece):
    return [b for b in pattern.beats if b.instrument == _INSTRUMENT[kit_piece]]


def kicks(pattern):
    return [b for b in pattern.beats if b.instrument == DrumInstrument.KICK]


def pattern_with_accent_headroom(kit_piece):
    # The hit at 1.0 sits below the pattern's own accented ceiling (set
    # by the accented hit at 3.0), leaving room for reinforce to boost it.
    builder = PatternBuilder("headroom")
    builder.kick(0.0, VELOCITY.KICK_NORMAL)
    builder.kick(2.0, VELOCITY.KICK_NORMAL)
    _place(builder, kit_piece, 1.0, _LIGHT_VELOCITY[kit_piece])
    builder.pattern.add_beat(
        3.0, _INSTRUMENT[kit_piece], _ACCENT_VELOCITY[kit_piece], accent=True
    )
    return builder.build()


# ── reinforce ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_reinforce_boosts_velocity_in_tolerance(kit_piece):
    pattern = pattern_with_accent_headroom(kit_piece)
    accents = RiffAccentMap.from_positions([(1.0, 1.0)], beats_per_bar=4.0)

    result = CymbalAccentReaction(
        riff_accents=accents, kit_piece=kit_piece, mode="reinforce"
    ).apply(pattern, intensity=1.0)

    boosted = next(
        b for b in matches(result, kit_piece) if abs(b.position - 1.0) < 1e-6
    )
    original = next(
        b for b in matches(pattern, kit_piece) if abs(b.position - 1.0) < 1e-6
    )
    assert boosted.velocity > original.velocity
    assert boosted.accent is True
    other = next(
        b for b in matches(result, kit_piece) if abs(b.position - 3.0) < 1e-6
    )
    assert other.velocity == _ACCENT_VELOCITY[kit_piece]


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_reinforce_no_op_out_of_tolerance(kit_piece):
    pattern = basic_pattern(kit_piece)
    accents = RiffAccentMap.from_positions([(1.5, 1.0)], beats_per_bar=4.0)

    result = CymbalAccentReaction(
        riff_accents=accents,
        kit_piece=kit_piece,
        mode="reinforce",
        reinforce_tolerance_beats=0.125,
    ).apply(pattern, intensity=1.0)

    assert [(b.position, b.velocity) for b in matches(result, kit_piece)] == [
        (b.position, b.velocity) for b in matches(pattern, kit_piece)
    ]


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_reinforce_excludes_ghost_notes(kit_piece):
    builder = PatternBuilder("ghosts")
    builder.pattern.add_beat(
        1.0,
        _INSTRUMENT[kit_piece],
        VELOCITY.HIHAT_WHISPER,
        ghost_note=True,
    )
    pattern = builder.build()
    accents = RiffAccentMap.from_positions([(1.0, 1.0)], beats_per_bar=4.0)

    result = CymbalAccentReaction(
        riff_accents=accents, kit_piece=kit_piece, mode="reinforce"
    ).apply(pattern, intensity=1.0)

    assert matches(result, kit_piece)[0].velocity == VELOCITY.HIHAT_WHISPER


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_reinforce_never_exceeds_pattern_accent_ceiling(kit_piece):
    builder = PatternBuilder("ceiling")
    _place(builder, kit_piece, 1.0, _LIGHT_VELOCITY[kit_piece])
    builder.pattern.add_beat(
        3.0, _INSTRUMENT[kit_piece], _ACCENT_VELOCITY[kit_piece], accent=True
    )
    pattern = builder.build()
    accents = RiffAccentMap.from_positions([(1.0, 1.0)], beats_per_bar=4.0)

    result = CymbalAccentReaction(
        riff_accents=accents, kit_piece=kit_piece, mode="reinforce"
    ).apply(pattern, intensity=1.0)

    boosted = next(
        b for b in matches(result, kit_piece) if abs(b.position - 1.0) < 1e-6
    )
    assert boosted.velocity <= _ACCENT_VELOCITY[kit_piece]


# ── stab ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_stab_inserts_unison_hit_at_locked_kick(kit_piece):
    pattern = basic_pattern(kit_piece)
    accents = RiffAccentMap.from_positions([(1.5, 0.9)], beats_per_bar=4.0)

    locked = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )
    assert any(abs(k.position - 1.5) < 1e-6 for k in kicks(locked))

    result = CymbalAccentReaction(
        riff_accents=accents,
        kit_piece=kit_piece,
        mode="stab",
        stab_threshold=0.85,
    ).apply(locked, intensity=1.0)

    stabbed = [
        b for b in matches(result, kit_piece) if abs(b.position - 1.5) < 1e-6
    ]
    assert len(stabbed) == 1
    matched_kick = next(
        k for k in kicks(result) if abs(k.position - 1.5) < 1e-6
    )
    assert stabbed[0].velocity == matched_kick.velocity
    assert stabbed[0].accent is True
    assert stabbed[0].ghost_note is False


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_stab_skips_when_no_kick_under_accent(kit_piece):
    pattern = basic_pattern(kit_piece)
    accents = RiffAccentMap.from_positions(
        [(0.0, 0.95), (0.1, 0.9)], beats_per_bar=4.0
    )

    locked = RiffLockTransform(
        riff_accents=accents, min_kick_spacing_beats=1.0, max_kicks_per_bar=1
    ).apply(pattern, intensity=1.0)
    assert not any(abs(k.position - 0.1) < 1e-6 for k in kicks(locked))

    result = CymbalAccentReaction(
        riff_accents=accents,
        kit_piece=kit_piece,
        mode="stab",
        stab_threshold=0.85,
        min_stab_spacing_beats=0.05,
    ).apply(locked, intensity=1.0)

    assert not any(
        abs(b.position - 0.1) < 1e-6 for b in matches(result, kit_piece)
    )


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_stab_collapses_to_reinforce_near_existing_hit(kit_piece):
    pattern = pattern_with_accent_headroom(kit_piece)
    accents = RiffAccentMap.from_positions([(1.0, 0.9)], beats_per_bar=4.0)

    locked = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )

    result = CymbalAccentReaction(
        riff_accents=accents,
        kit_piece=kit_piece,
        mode="stab",
        stab_threshold=0.85,
        stab_collapse_tolerance_beats=0.125,
    ).apply(locked, intensity=1.0)

    matched = [
        b for b in matches(result, kit_piece) if abs(b.position - 1.0) < 1e-6
    ]
    assert len(matched) == 1
    assert matched[0].velocity > _LIGHT_VELOCITY[kit_piece]


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_stab_wraparound_at_bar_boundary(kit_piece):
    builder = PatternBuilder("wrap")
    builder.kick(3.9, VELOCITY.KICK_NORMAL)
    pattern = builder.build()
    accents = RiffAccentMap.from_positions([(0.05, 0.95)], beats_per_bar=4.0)

    locked = RiffLockTransform(
        riff_accents=accents, kick_tolerance_beats=0.2
    ).apply(pattern, intensity=1.0)
    assert abs(kicks(locked)[0].position - 0.05) < 1e-6

    result = CymbalAccentReaction(
        riff_accents=accents,
        kit_piece=kit_piece,
        mode="stab",
        stab_threshold=0.85,
        stab_kick_tolerance_beats=0.2,
    ).apply(locked, intensity=1.0)

    assert any(
        abs(b.position - 0.05) < 1e-6 for b in matches(result, kit_piece)
    )


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_stab_respects_max_stabs_per_bar_budget(kit_piece):
    pattern = basic_pattern(kit_piece)
    accents = RiffAccentMap.from_positions(
        [(i * 0.5, 0.9) for i in range(8)], beats_per_bar=4.0
    )

    locked = RiffLockTransform(
        riff_accents=accents, min_kick_spacing_beats=0.01, max_kicks_per_bar=8
    ).apply(pattern, intensity=1.0)

    result = CymbalAccentReaction(
        riff_accents=accents,
        kit_piece=kit_piece,
        mode="stab",
        stab_threshold=0.85,
        max_stabs_per_bar=2,
        min_stab_spacing_beats=0.01,
    ).apply(locked, intensity=1.0)

    new_stabs = len(matches(result, kit_piece)) - len(
        matches(locked, kit_piece)
    )
    assert new_stabs <= 2


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_stab_excludes_ghost_notes_as_collapse_targets(kit_piece):
    builder = PatternBuilder("ghost_collapse")
    builder.kick(1.0, VELOCITY.KICK_NORMAL)
    builder.pattern.add_beat(
        1.0, _INSTRUMENT[kit_piece], VELOCITY.HIHAT_WHISPER, ghost_note=True
    )
    pattern = builder.build()
    accents = RiffAccentMap.from_positions([(1.0, 0.9)], beats_per_bar=4.0)

    result = CymbalAccentReaction(
        riff_accents=accents,
        kit_piece=kit_piece,
        mode="stab",
        stab_threshold=0.85,
    ).apply(pattern, intensity=1.0)

    non_ghost_at_1_0 = [
        b
        for b in matches(result, kit_piece)
        if abs(b.position - 1.0) < 1e-6 and not b.ghost_note
    ]
    assert len(non_ghost_at_1_0) == 1


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_stab_determinism_same_input_twice_gives_identical_output(kit_piece):
    pattern = basic_pattern(kit_piece)
    accents = RiffAccentMap.from_positions(
        [(0.1, 0.9), (1.5, 0.95), (2.6, 0.88)], beats_per_bar=4.0
    )
    locked = RiffLockTransform(riff_accents=accents).apply(
        pattern, intensity=1.0
    )

    transform = CymbalAccentReaction(
        riff_accents=accents,
        kit_piece=kit_piece,
        mode="stab",
        stab_threshold=0.85,
    )
    result_a = transform.apply(locked, intensity=0.7)
    result_b = transform.apply(locked, intensity=0.7)

    beats_a = [(b.position, b.instrument, b.velocity) for b in result_a.beats]
    beats_b = [(b.position, b.instrument, b.velocity) for b in result_b.beats]
    assert beats_a == beats_b


@pytest.mark.parametrize("kit_piece", KIT_PIECES)
def test_empty_accent_map_leaves_pattern_unchanged(kit_piece):
    pattern = basic_pattern(kit_piece)
    accents = RiffAccentMap(accents=(), beats_per_bar=4.0)

    for mode in ("reinforce", "stab"):
        result = CymbalAccentReaction(
            riff_accents=accents, kit_piece=kit_piece, mode=mode
        ).apply(pattern, intensity=1.0)
        assert [(b.position, b.instrument) for b in result.beats] == [
            (b.position, b.instrument) for b in pattern.beats
        ]
        assert result is not pattern


def test_invalid_mode_raises():
    accents = RiffAccentMap.from_positions([(0.0, 0.9)], beats_per_bar=4.0)
    try:
        CymbalAccentReaction(
            riff_accents=accents, kit_piece="hihat", mode="off"
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for mode='off'")


def test_invalid_kit_piece_raises():
    accents = RiffAccentMap.from_positions([(0.0, 0.9)], beats_per_bar=4.0)
    try:
        CymbalAccentReaction(
            riff_accents=accents, kit_piece="splash", mode="reinforce"
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for kit_piece='splash'")
