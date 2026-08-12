"""Tests for MIDIEngine's collision dedup (issue #18 review follow-up).

Genre-aware timekeeper promotion can now place a promoted beat at the
same (instrument, position) as an already-placed CrashAccents beat (e.g.
rock's hard/punk styles promoting hi-hat to CRASH, which collides with
CrashAccents' own CRASH placement at the same position). midiutil
silently collapses same-pitch, same-tick NoteOn events, keeping whichever
happens to be added first - _add_section_to_midi already guards against
this for song export; pattern_to_midi (used for single-pattern export)
did not.
"""

from __future__ import annotations

import io

from midi_drums.core.models.pattern import Beat, Pattern
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.export.midi.engine import (
    MIDIEngine,
    _dedupe_by_instrument_position,
)


class TestDedupeByInstrumentPosition:
    def test_keeps_loudest_of_colliding_beats(self):
        quiet = Beat(position=0.0, instrument=DrumInstrument.CRASH, velocity=80)
        loud = Beat(position=0.0, instrument=DrumInstrument.CRASH, velocity=110)

        result = _dedupe_by_instrument_position([quiet, loud])

        assert result == [loud]

    def test_result_independent_of_input_order(self):
        quiet = Beat(position=0.0, instrument=DrumInstrument.CRASH, velocity=80)
        loud = Beat(position=0.0, instrument=DrumInstrument.CRASH, velocity=110)

        assert _dedupe_by_instrument_position(
            [quiet, loud]
        ) == _dedupe_by_instrument_position([loud, quiet])

    def test_different_instruments_at_same_position_both_kept(self):
        crash = Beat(
            position=0.0, instrument=DrumInstrument.CRASH, velocity=110
        )
        kick = Beat(position=0.0, instrument=DrumInstrument.KICK, velocity=100)

        result = _dedupe_by_instrument_position([crash, kick])

        assert len(result) == 2
        assert crash in result
        assert kick in result

    def test_same_instrument_different_positions_both_kept(self):
        first = Beat(
            position=0.0, instrument=DrumInstrument.CRASH, velocity=110
        )
        second = Beat(
            position=1.0, instrument=DrumInstrument.CRASH, velocity=110
        )

        result = _dedupe_by_instrument_position([first, second])

        assert len(result) == 2
        assert first in result
        assert second in result


class TestPatternToMidiDedup:
    def test_colliding_beats_produce_order_independent_output(self):
        quiet = Beat(position=0.0, instrument=DrumInstrument.CRASH, velocity=80)
        loud = Beat(position=0.0, instrument=DrumInstrument.CRASH, velocity=110)
        engine = MIDIEngine()

        buf_quiet_first = io.BytesIO()
        engine.pattern_to_midi(
            Pattern(name="a", beats=[quiet, loud])
        ).writeFile(buf_quiet_first)

        buf_loud_first = io.BytesIO()
        engine.pattern_to_midi(
            Pattern(name="b", beats=[loud, quiet])
        ).writeFile(buf_loud_first)

        assert buf_quiet_first.getvalue() == buf_loud_first.getvalue()

    def test_colliding_beats_keep_the_loudest(self):
        quiet = Beat(position=0.0, instrument=DrumInstrument.CRASH, velocity=80)
        loud = Beat(position=0.0, instrument=DrumInstrument.CRASH, velocity=110)
        engine = MIDIEngine()

        buf_colliding = io.BytesIO()
        engine.pattern_to_midi(
            Pattern(name="colliding", beats=[quiet, loud])
        ).writeFile(buf_colliding)

        buf_loud_only = io.BytesIO()
        engine.pattern_to_midi(
            Pattern(name="loud_only", beats=[loud])
        ).writeFile(buf_loud_only)

        assert buf_colliding.getvalue() == buf_loud_only.getvalue()

    def test_non_colliding_beats_are_both_kept(self):
        crash = Beat(
            position=0.0, instrument=DrumInstrument.CRASH, velocity=110
        )
        kick = Beat(position=0.0, instrument=DrumInstrument.KICK, velocity=100)
        engine = MIDIEngine()

        both = io.BytesIO()
        engine.pattern_to_midi(
            Pattern(name="both", beats=[crash, kick])
        ).writeFile(both)

        crash_only = io.BytesIO()
        engine.pattern_to_midi(
            Pattern(name="crash_only", beats=[crash])
        ).writeFile(crash_only)

        assert both.getvalue() != crash_only.getvalue()
