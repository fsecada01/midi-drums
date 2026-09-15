"""Tests for MIDIEngine.bars_to_midi (additive-rhythm-grouping spike).

See claudedocs/design_additive_rhythm_grouping.md for why this is a
separate, non-scaling export path rather than Song/Section reuse.
"""

from midi_drums.export.midi.engine import MIDIEngine
from midi_drums.generation.builders.additive_rhythm_builder import (
    build_additive_rhythm_bars,
)


def _events_by_name(midi, evtname: str) -> list:
    return [e for e in midi.tracks[0].eventList if e.evtname == evtname]


class TestBarsToMidi:
    def test_emits_one_time_signature_event_per_meter_change(self):
        patterns = build_additive_rhythm_bars(
            "3-3-3-3-2-2", grid_denominator=16
        )

        midi = MIDIEngine().bars_to_midi(patterns, tempo=120)

        sigs = _events_by_name(midi, "TimeSignature")
        assert len(sigs) == 2  # initial 6/8, then the change to 2/8

    def test_second_bar_time_signature_marker_at_first_bars_beats_per_bar(self):
        patterns = build_additive_rhythm_bars(
            "3-3-3-3-2-2", grid_denominator=16
        )
        assert patterns[0].time_signature.beats_per_bar == 3.0

        midi = MIDIEngine().bars_to_midi(patterns, tempo=120)

        sigs = sorted(
            _events_by_name(midi, "TimeSignature"), key=lambda e: e.tick
        )
        # 3.0 beats * 960 ticks/quarter (MIDIFile(1) default TPQ) == 2880 -
        # the marker isn't squashed/stretched against some other meter.
        assert sigs[1].tick == 2880

    def test_single_meter_emits_one_time_signature_event(self):
        patterns = build_additive_rhythm_bars("4-4-4-4", grid_denominator=16)

        midi = MIDIEngine().bars_to_midi(patterns, tempo=120)

        sigs = _events_by_name(midi, "TimeSignature")
        assert len(sigs) == 1
