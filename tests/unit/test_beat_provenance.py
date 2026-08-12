"""Tests for Beat provenance tracking (issue #36 item 1).

Beat.instrument_promoted distinguishes a cymbal beat that started life as a
hi-hat and got switched to ride/crash/china by
GenrePlugin._apply_ride_hihat_logic (issue #18) from a cymbal beat placed
directly by a pattern template/genre style (e.g. CrashAccents). Before this
flag existed, PocketStretching/MinimalCreativity/SpeedPrecision in
midi_drums.modifications.drummer_mods matched "the timekeeping cymbal" by
instrument type alone, so a genuinely-placed accent of the same instrument
as the section's promoted timekeeper was modified exactly like the
timekeeping beat itself - undesired, since a deliberate accent isn't part
of the continuous timekeeping pattern.

These tests cover:
  1. The flag's default and how _apply_ride_hihat_logic sets it.
  2. Propagation through Pattern.copy()/humanize() (any reconstruction that
     drops it silently re-introduces the issue #36 item 1 ambiguity).
  3. PocketStretching/MinimalCreativity/SpeedPrecision now leaving a
     genuinely-placed accent alone while still treating a promoted beat as
     the timekeeper.
"""

from unittest.mock import patch

import pytest

from midi_drums.config import VELOCITY
from midi_drums.core.models.pattern import Beat, Pattern
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.modifications.drummer_mods import (
    MinimalCreativity,
    PocketStretching,
    SpeedPrecision,
)
from midi_drums.plugins.interfaces.genre_plugin import GenrePlugin


class _StubGenrePlugin(GenrePlugin):
    """Minimal concrete GenrePlugin for exercising
    _apply_ride_hihat_logic in isolation, mirroring the stub in
    test_ride_hihat_switching.py.
    """

    @property
    def genre_name(self) -> str:
        return "stub"

    @property
    def supported_styles(self) -> list[str]:
        return ["default"]

    def generate_pattern(self, section, parameters):
        raise NotImplementedError

    def get_common_fills(self):
        return []


class _InvalidTimekeeperPlugin(_StubGenrePlugin):
    """Stub whose override returns an instrument outside the shared
    PROMOTABLE_TIMEKEEPING_CYMBALS registry.
    """

    def _high_energy_timekeeper(self, section, parameters):
        return DrumInstrument.SPLASH


@pytest.mark.unit
class TestBeatInstrumentPromotedFlag:
    def test_default_is_false(self):
        beat = Beat(position=0.0, instrument=DrumInstrument.CRASH)
        assert beat.instrument_promoted is False

    def test_apply_ride_hihat_logic_sets_flag_on_promoted_beats_only(self):
        pattern = Pattern(name="test")
        pattern.add_beat(0.0, DrumInstrument.KICK)
        pattern.add_beat(1.0, DrumInstrument.CLOSED_HH)

        plugin = _StubGenrePlugin()
        params = GenerationParameters(genre="stub")
        result = plugin._apply_ride_hihat_logic(pattern, "chorus", params)

        by_instrument = {
            beat.instrument: beat
            for beat in result.beats
            if beat.instrument != DrumInstrument.PEDAL_HH
        }
        assert by_instrument[DrumInstrument.RIDE].instrument_promoted is True
        assert by_instrument[DrumInstrument.KICK].instrument_promoted is False

    def test_rejects_timekeeper_outside_shared_registry(self):
        pattern = Pattern(name="test")
        pattern.add_beat(0.0, DrumInstrument.CLOSED_HH)

        plugin = _InvalidTimekeeperPlugin()
        params = GenerationParameters(genre="stub")

        with pytest.raises(ValueError, match="PROMOTABLE_TIMEKEEPING_CYMBALS"):
            plugin._apply_ride_hihat_logic(pattern, "chorus", params)


@pytest.mark.unit
class TestInstrumentPromotedPropagation:
    def test_pattern_copy_preserves_flag(self):
        pattern = Pattern(name="test")
        pattern.beats.append(
            Beat(
                position=0.0,
                instrument=DrumInstrument.CRASH,
                instrument_promoted=True,
            )
        )

        copied = pattern.copy()

        assert copied.beats[0].instrument_promoted is True

    def test_pattern_humanize_preserves_flag(self):
        pattern = Pattern(name="test")
        pattern.beats.append(
            Beat(
                position=0.0,
                instrument=DrumInstrument.CRASH,
                instrument_promoted=True,
            )
        )

        humanized = pattern.humanize(timing_variance=0.0, velocity_variance=0)

        assert humanized.beats[0].instrument_promoted is True


def _pattern_with_genuine_and_promoted_crash() -> Pattern:
    """A pattern with two CRASH beats at different positions: one a
    genuinely-placed accent (instrument_promoted=False, as CrashAccents
    would place it), one a promoted former hi-hat beat
    (instrument_promoted=True, as _apply_ride_hihat_logic would leave it).
    """
    pattern = Pattern(name="test")
    pattern.beats.append(
        Beat(
            position=0.0,
            instrument=DrumInstrument.CRASH,
            velocity=VELOCITY.CRASH_ACCENT,
            instrument_promoted=False,
        )
    )
    pattern.beats.append(
        Beat(
            position=2.0,
            instrument=DrumInstrument.CRASH,
            velocity=80,
            instrument_promoted=True,
        )
    )
    return pattern


@pytest.mark.unit
class TestPocketStretchingRespectsProvenance:
    def test_only_promoted_cymbal_beat_shifts_position(self):
        pattern = _pattern_with_genuine_and_promoted_crash()
        genuine_original_position = pattern.beats[0].position
        promoted_original_position = pattern.beats[1].position

        with patch("random.uniform", return_value=0.05):
            result = PocketStretching(variation_ms=5.0).apply(
                pattern, intensity=1.0
            )

        by_promoted = {beat.instrument_promoted: beat for beat in result.beats}
        assert by_promoted[False].position == genuine_original_position
        assert by_promoted[True].position != promoted_original_position
        assert by_promoted[True].position == pytest.approx(
            promoted_original_position + 0.05
        )


@pytest.mark.unit
class TestMinimalCreativityRespectsProvenance:
    def test_only_promoted_cymbal_beat_can_be_thinned(self):
        pattern = _pattern_with_genuine_and_promoted_crash()

        # sparseness * intensity = 1.0 -> random.random() > 1.0 is always
        # False, so any beat that reaches the thinning branch is always
        # dropped. A beat that never reaches that branch is always kept.
        result = MinimalCreativity(sparseness=1.0).apply(pattern, intensity=1.0)

        remaining_promoted_flags = {
            beat.instrument_promoted for beat in result.beats
        }
        assert remaining_promoted_flags == {False}


@pytest.mark.unit
class TestSpeedPrecisionRespectsProvenance:
    def test_only_promoted_cymbal_beat_normalizes_velocity(self):
        pattern = _pattern_with_genuine_and_promoted_crash()
        genuine_original_velocity = pattern.beats[0].velocity
        promoted_original_velocity = pattern.beats[1].velocity

        result = SpeedPrecision(consistency=1.0).apply(pattern, intensity=1.0)

        by_promoted = {beat.instrument_promoted: beat for beat in result.beats}
        assert by_promoted[False].velocity == genuine_original_velocity
        assert by_promoted[True].velocity == VELOCITY.CRASH_NORMAL
        assert by_promoted[True].velocity != promoted_original_velocity
