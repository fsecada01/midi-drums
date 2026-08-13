"""Tests for DrumGeneratorAPI.export_song_timeline_json (issue #53 AC
Group 4). This produces a flat, resolved tempo/region timeline consumed
by reaper/create_song_sections.lua's song-map mode - flat so Lua's
regex-based parser can read it without a full JSON parser.
"""

import json

from midi_drums.api.python_api import DrumGeneratorAPI
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Section, Song, SongSegment
from midi_drums.core.value_objects.time_signature import TimeSignature


class TestExportSongTimelineJson:
    def test_non_segmented_song_produces_single_tempo_point(self, tmp_path):
        song = Song(name="s", tempo=120)
        song.add_section(Section("verse", Pattern("p"), bars=4))
        song.add_section(Section("chorus", Pattern("p"), bars=4))

        api = DrumGeneratorAPI()
        out = tmp_path / "timeline.json"
        api.export_song_timeline_json(song, out)

        data = json.loads(out.read_text())
        assert data["tempo_points"] == [
            {"time": 0.0, "bpm": 120, "num": 4, "denom": 4}
        ]
        assert len(data["regions"]) == 2
        assert data["regions"][0]["start_time"] == 0.0
        assert data["regions"][0]["end_time"] == 8.0
        assert data["regions"][1]["start_time"] == 8.0
        assert data["regions"][1]["end_time"] == 16.0
        assert data["total_time"] == 16.0

    def test_segmented_section_emits_tempo_point_per_change(self, tmp_path):
        song = Song(name="s", tempo=140)
        song.add_section(
            Section(
                "verse",
                Pattern("p"),
                bars=10,
                segments=[
                    SongSegment(bars=8, tempo=140),
                    SongSegment(
                        bars=2, tempo=140, time_signature=TimeSignature(7, 8)
                    ),
                ],
            )
        )

        api = DrumGeneratorAPI()
        out = tmp_path / "timeline.json"
        api.export_song_timeline_json(song, out)

        data = json.loads(out.read_text())
        # 8 bars @ 4/4, 140bpm: 8 * 4 beats / (140/60 beats/sec) = 96/7s.
        assert data["tempo_points"] == [
            {"time": 0.0, "bpm": 140, "num": 4, "denom": 4},
            {"time": 96 / 7, "bpm": 140, "num": 7, "denom": 8},
        ]

    def test_region_names_and_color_groups_from_section_parameters(
        self, tmp_path
    ):
        song = Song(name="s", tempo=100)
        section = Section("verse", Pattern("p"), bars=4)
        section.section_parameters["display_name"] = "Verse 1"
        section.section_parameters["color_group"] = "groove"
        song.add_section(section)

        api = DrumGeneratorAPI()
        out = tmp_path / "timeline.json"
        api.export_song_timeline_json(song, out)

        data = json.loads(out.read_text())
        assert data["regions"][0]["name"] == "Verse 1"
        assert data["regions"][0]["color_group"] == "groove"

    def test_color_groups_carried_from_song_metadata(self, tmp_path):
        song = Song(name="s", tempo=100)
        song.metadata["color_groups"] = {"groove": [200, 120, 40]}
        song.add_section(Section("verse", Pattern("p"), bars=4))

        api = DrumGeneratorAPI()
        out = tmp_path / "timeline.json"
        api.export_song_timeline_json(song, out)

        data = json.loads(out.read_text())
        assert data["color_groups"] == [
            {"name": "groove", "r": 200, "g": 120, "b": 40}
        ]

    def test_no_color_groups_metadata_yields_empty_list(self, tmp_path):
        song = Song(name="s", tempo=100)
        song.add_section(Section("verse", Pattern("p"), bars=4))

        api = DrumGeneratorAPI()
        out = tmp_path / "timeline.json"
        api.export_song_timeline_json(song, out)

        data = json.loads(out.read_text())
        assert data["color_groups"] == []
