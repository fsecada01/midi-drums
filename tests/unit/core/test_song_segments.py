"""Tests for SongSegment / Section per-segment tempo and meter overrides.

Covers issue #53 AC Group 1: a Section can be split into segments, each
optionally overriding the song's global tempo and/or time signature,
mirroring the song_creator REAPER tool's region-segment shape.
"""

import pytest

from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Section, Song, SongSegment
from midi_drums.core.value_objects.time_signature import TimeSignature


def _pattern(name: str = "p") -> Pattern:
    return Pattern(name)


class TestSongSegmentDefaults:
    def test_segment_defaults_to_inheriting_tempo_and_meter(self):
        segment = SongSegment(bars=4)
        assert segment.tempo is None
        assert segment.time_signature is None
        assert segment.bars == 4


class TestSectionSegmentsValidation:
    def test_section_with_no_segments_is_unaffected(self):
        section = Section("verse", _pattern(), bars=8)
        assert section.segments == []

    def test_segment_bars_must_sum_to_section_bars(self):
        with pytest.raises(ValueError, match="segments sum to"):
            Section(
                "verse",
                _pattern(),
                bars=8,
                segments=[SongSegment(bars=4), SongSegment(bars=2)],
            )

    def test_segment_bars_matching_section_bars_is_valid(self):
        section = Section(
            "verse",
            _pattern(),
            bars=8,
            segments=[SongSegment(bars=4), SongSegment(bars=4)],
        )
        assert len(section.segments) == 2


class TestSegmentForBar:
    def test_no_segments_returns_none(self):
        section = Section("verse", _pattern(), bars=4)
        assert section.segment_for_bar(0) is None
        assert section.segment_for_bar(3) is None

    def test_finds_segment_covering_local_bar_number(self):
        # Mirrors song_map.json's "Verse 1": 8@4/4 -> 2@7/8 -> 6@4/4
        seg_a = SongSegment(bars=8, tempo=144)
        seg_b = SongSegment(
            bars=2, tempo=144, time_signature=TimeSignature(7, 8)
        )
        seg_c = SongSegment(bars=6, tempo=144)
        section = Section(
            "verse", _pattern(), bars=16, segments=[seg_a, seg_b, seg_c]
        )

        assert section.segment_for_bar(0) is seg_a
        assert section.segment_for_bar(7) is seg_a
        assert section.segment_for_bar(8) is seg_b
        assert section.segment_for_bar(9) is seg_b
        assert section.segment_for_bar(10) is seg_c
        assert section.segment_for_bar(15) is seg_c

    def test_bar_number_past_end_returns_none(self):
        section = Section(
            "verse", _pattern(), bars=4, segments=[SongSegment(bars=4)]
        )
        assert section.segment_for_bar(4) is None


class TestEffectiveTempoAndTimeSignature:
    def test_no_segments_falls_back_to_song_global(self):
        section = Section("verse", _pattern(), bars=4)
        assert section.effective_tempo(0, song_tempo=120) == 120
        default_sig = TimeSignature()
        assert section.effective_time_signature(0, default_sig) == default_sig

    def test_segment_without_override_falls_back_to_song_global(self):
        section = Section(
            "verse", _pattern(), bars=4, segments=[SongSegment(bars=4)]
        )
        assert section.effective_tempo(0, song_tempo=120) == 120
        default_sig = TimeSignature()
        assert section.effective_time_signature(0, default_sig) == default_sig

    def test_segment_override_takes_precedence(self):
        odd_meter = TimeSignature(7, 8)
        section = Section(
            "verse",
            _pattern(),
            bars=10,
            segments=[
                SongSegment(bars=8, tempo=144),
                SongSegment(bars=2, tempo=160, time_signature=odd_meter),
            ],
        )
        # Tempo-only override within the 4/4 segment
        assert section.effective_tempo(0, song_tempo=120) == 144
        assert (
            section.effective_time_signature(0, TimeSignature())
            == TimeSignature()
        )
        # Tempo + meter override within the 7/8 segment
        assert section.effective_tempo(8, song_tempo=120) == 160
        assert section.effective_time_signature(8, TimeSignature()) == odd_meter


class TestTotalDurationSecondsWithSegments:
    def test_non_segmented_song_duration_unchanged(self):
        song = Song(name="s", tempo=120)
        song.add_section(Section("verse", _pattern(), bars=8))
        song.add_section(Section("chorus", _pattern(), bars=8))
        # 16 bars * 4 beats/bar / (120/60 beats-per-second) = 32 seconds
        assert song.total_duration_seconds() == pytest.approx(32.0)

    def test_segmented_section_uses_per_segment_tempo_and_meter(self):
        # song_map.json's "Verse 1" shape: 8@144bpm 4/4 -> 2@144bpm 7/8
        # -> 6@144bpm 4/4, all inside one 16-bar section.
        song = Song(name="s", tempo=120)
        song.add_section(
            Section(
                "verse",
                _pattern(),
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

        expected = (
            8 * 4.0 / (144 / 60.0)
            + 2 * (7 * 4.0 / 8) / (144 / 60.0)
            + 6 * 4.0 / (144 / 60.0)
        )
        assert song.total_duration_seconds() == pytest.approx(expected)
