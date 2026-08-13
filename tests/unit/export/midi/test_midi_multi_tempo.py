"""Tests for MIDIEngine's per-segment tempo/time-signature export.

Covers issue #53 AC Group 2: segmented Sections must actually produce
MIDI tempo/time-signature marker events at segment boundaries, while
non-segmented songs must remain byte-identical to the pre-segment engine.
"""

from pathlib import Path

import pytest

from midi_drums.core.models.pattern import Beat, Pattern
from midi_drums.core.models.song import Section, Song, SongSegment
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.time_signature import TimeSignature
from midi_drums.export.midi.engine import MIDIEngine

FIXTURES_DIR = Path(__file__).parent.parent.parent.parent / "fixtures"


def _fixture_pattern() -> Pattern:
    pattern = Pattern("fixture_pattern")
    pattern.beats = [
        Beat(0.0, DrumInstrument.KICK, 105, 0.1),
        Beat(1.0, DrumInstrument.SNARE, 110, 0.1),
        Beat(0.5, DrumInstrument.CLOSED_HH, 80, 0.1),
        Beat(1.5, DrumInstrument.CLOSED_HH, 80, 0.1),
    ]
    return pattern


def _events_by_name(midi, evtname: str) -> list:
    return [e for e in midi.tracks[0].eventList if e.evtname == evtname]


class TestNonSegmentedSongUnchanged:
    def test_byte_identical_to_pre_segment_baseline(self):
        pattern = _fixture_pattern()
        song = Song(name="fixture_song", tempo=120)
        song.add_section(Section("verse", pattern, bars=2))
        song.add_section(Section("chorus", pattern, bars=2))

        midi = MIDIEngine().song_to_midi(song)
        import io

        buf = io.BytesIO()
        midi.writeFile(buf)

        baseline = (FIXTURES_DIR / "non_segmented_baseline.mid").read_bytes()
        assert buf.getvalue() == baseline

    def test_no_tempo_or_time_signature_events_beyond_the_initial_one(self):
        pattern = _fixture_pattern()
        song = Song(name="s", tempo=120)
        song.add_section(Section("verse", pattern, bars=4))

        midi = MIDIEngine().song_to_midi(song)

        tempos = _events_by_name(midi, "Tempo")
        assert len(tempos) == 1  # only the initial song.tempo event
        assert _events_by_name(midi, "TimeSignature") == []


class TestSegmentedSongEmitsMarkers:
    def test_tempo_change_mid_section_emits_marker(self):
        pattern = _fixture_pattern()
        song = Song(name="s", tempo=120)
        song.add_section(
            Section(
                "verse",
                pattern,
                bars=4,
                segments=[
                    SongSegment(bars=2, tempo=120),
                    SongSegment(bars=2, tempo=160),
                ],
            )
        )

        midi = MIDIEngine().song_to_midi(song)
        tempos = _events_by_name(midi, "Tempo")

        # Initial 120bpm event at t=0, plus a 160bpm event at bar 2's start.
        assert len(tempos) == 2
        bpms = [round(60000000 / t.tempo) for t in tempos]
        assert bpms == [120, 160]
        assert tempos[0].tick == 0
        assert tempos[1].tick == midi.time_to_ticks(
            2 * TimeSignature().beats_per_bar
        )

    def test_meter_change_mid_section_emits_marker_and_reverts(self):
        # Mirrors song_map.json's "Verse 1": 8@4/4 -> 2@7/8 -> 6@4/4
        pattern = _fixture_pattern()
        song = Song(name="s", tempo=144)
        song.add_section(
            Section(
                "verse",
                pattern,
                bars=16,
                segments=[
                    SongSegment(bars=8, tempo=144),
                    SongSegment(
                        bars=2, tempo=144, time_signature=TimeSignature(7, 8)
                    ),
                    SongSegment(bars=6, tempo=144),
                ],
            )
        )

        midi = MIDIEngine().song_to_midi(song)
        sigs = _events_by_name(midi, "TimeSignature")

        # One event entering the 7/8 insert, one event reverting to 4/4.
        assert len(sigs) == 2
        assert (sigs[0].numerator, sigs[0].denominator) == (7, 3)  # 8 = 2**3
        assert (sigs[1].numerator, sigs[1].denominator) == (4, 2)  # 4 = 2**2

    def test_section_without_segments_after_segmented_section_inherits_song_defaults(
        self,
    ):
        pattern = _fixture_pattern()
        song = Song(name="s", tempo=120)
        song.add_section(
            Section(
                "verse",
                pattern,
                bars=2,
                segments=[SongSegment(bars=2, tempo=180)],
            )
        )
        song.add_section(Section("chorus", pattern, bars=2))

        midi = MIDIEngine().song_to_midi(song)
        tempos = _events_by_name(midi, "Tempo")

        # 120 (initial) -> 180 (segment) -> 120 (chorus reverting to song
        # global, since it has no segments of its own).
        bpms = [round(60000000 / t.tempo) for t in tempos]
        assert bpms == [120, 180, 120]


class TestSongDurationMatchesMidiLength:
    def test_get_midi_info_duration_accounts_for_segments(self):
        pattern = _fixture_pattern()
        song = Song(name="s", tempo=120)
        song.add_section(
            Section(
                "verse",
                pattern,
                bars=4,
                segments=[
                    SongSegment(bars=2, tempo=120),
                    SongSegment(bars=2, tempo=240),
                ],
            )
        )

        info = MIDIEngine().get_midi_info(song)
        # 2 bars @120bpm (4s) + 2 bars @240bpm (2s) = 6s
        assert info["duration_seconds"] == pytest.approx(6.0)
