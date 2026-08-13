"""Tests for the song_creator song-map bridge (issue #53 AC Group 3).

song_creator (a separate REAPER Lua arrangement tool) models a song as
regions containing segments, each with its own bars/bpm/num/denom. These
tests cover DrumGeneratorAPI.create_song_from_song_map (ingestion) and
export_song_map_json (the reverse direction), including a round trip
against song_creator's own committed song_map.json fixture.
"""

import json
from pathlib import Path

import pytest

from midi_drums.api.python_api import DrumGeneratorAPI
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Section, Song, SongSegment
from midi_drums.core.value_objects.time_signature import TimeSignature

FIXTURE = (
    Path(__file__).parent.parent.parent
    / "fixtures"
    / "song_creator_song_map.json"
)

SIMPLE_MAP = {
    "title": "Simple Map",
    "color_groups": {"groove": [200, 120, 40]},
    "regions": [
        {
            "name": "Intro",
            "color_group": "groove",
            "segments": [{"bars": 4, "bpm": 100, "num": 4, "denom": 4}],
        },
        {
            "name": "Verse",
            "color_group": "groove",
            "segments": [
                {"bars": 8, "bpm": 140, "num": 4, "denom": 4},
                {"bars": 2, "bpm": 140, "num": 7, "denom": 8},
            ],
        },
        {
            "name": "Chorus",
            "color_group": "groove",
            "segments": [{"bars": 8, "bpm": 120, "num": 4, "denom": 4}],
        },
    ],
}


class TestCreateSongFromSongMap:
    def test_no_regions_raises(self):
        api = DrumGeneratorAPI()
        with pytest.raises(ValueError, match="No regions"):
            api.create_song_from_song_map(
                {"regions": []}, genre="metal", style="heavy"
            )

    def test_missing_file_raises(self):
        api = DrumGeneratorAPI()
        with pytest.raises(FileNotFoundError):
            api.create_song_from_song_map(
                "does-not-exist.json", genre="metal", style="heavy"
            )

    def test_accepts_dict_input(self):
        api = DrumGeneratorAPI()
        song = api.create_song_from_song_map(
            SIMPLE_MAP, genre="metal", style="heavy"
        )
        assert len(song.sections) == 3
        assert [s.bars for s in song.sections] == [4, 10, 8]

    def test_accepts_json_string_input(self):
        api = DrumGeneratorAPI()
        song = api.create_song_from_song_map(
            json.dumps(SIMPLE_MAP), genre="metal", style="heavy"
        )
        assert len(song.sections) == 3

    def test_accepts_file_path_input(self, tmp_path):
        path = tmp_path / "map.json"
        path.write_text(json.dumps(SIMPLE_MAP))
        api = DrumGeneratorAPI()
        song = api.create_song_from_song_map(path, genre="metal", style="heavy")
        assert len(song.sections) == 3

    def test_segments_attached_to_sections(self):
        api = DrumGeneratorAPI()
        song = api.create_song_from_song_map(
            SIMPLE_MAP, genre="metal", style="heavy"
        )
        verse = song.sections[1]
        assert len(verse.segments) == 2
        assert verse.segments[0].tempo == 140
        assert verse.segments[1].time_signature == TimeSignature(7, 8)

    def test_tempo_defaults_to_first_segment_bpm_when_not_specified(self):
        api = DrumGeneratorAPI()
        song = api.create_song_from_song_map(
            SIMPLE_MAP, genre="metal", style="heavy"
        )
        assert song.tempo == 100  # first region's first segment's bpm

    def test_explicit_tempo_overrides_song_map_default(self):
        api = DrumGeneratorAPI()
        song = api.create_song_from_song_map(
            SIMPLE_MAP, genre="metal", style="heavy", tempo=90
        )
        assert song.tempo == 90

    def test_metadata_carries_title_and_color_groups(self):
        api = DrumGeneratorAPI()
        song = api.create_song_from_song_map(
            SIMPLE_MAP, genre="metal", style="heavy"
        )
        assert song.metadata["song_map_title"] == "Simple Map"
        assert song.metadata["color_groups"] == {"groove": [200, 120, 40]}

    def test_unrecognized_genre_raises_clear_error(self):
        api = DrumGeneratorAPI()
        with pytest.raises(ValueError, match="Could not generate"):
            api.create_song_from_song_map(
                SIMPLE_MAP, genre="not-a-real-genre", style="heavy"
            )

    def test_real_song_creator_fixture_generates_successfully(self):
        # metal's genre plugin defaults unrecognized section names (e.g.
        # "Pre-Chorus", "Guitar Solo") to a verse pattern rather than
        # failing, so song_creator's full 10-region map should still
        # produce one Section per region.
        api = DrumGeneratorAPI()
        song = api.create_song_from_song_map(
            FIXTURE, genre="metal", style="heavy"
        )
        fixture_data = json.loads(FIXTURE.read_text())
        assert len(song.sections) == len(fixture_data["regions"])
        assert song.metadata["song_map_title"] == (
            "Groove/Technical Metal Song Map"
        )


class TestExportSongMapJson:
    def test_non_segmented_section_exports_single_implicit_segment(
        self, tmp_path
    ):
        song = Song(name="s", tempo=120)
        song.add_section(Section("verse", Pattern("p"), bars=4))

        api = DrumGeneratorAPI()
        out = tmp_path / "out.json"
        api.export_song_map_json(song, out)

        data = json.loads(out.read_text())
        assert len(data["regions"]) == 1
        region = data["regions"][0]
        assert region["segments"] == [
            {"bars": 4, "bpm": 120, "num": 4, "denom": 4}
        ]

    def test_segmented_section_exports_each_segment(self, tmp_path):
        song = Song(name="s", tempo=120)
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
        out = tmp_path / "out.json"
        api.export_song_map_json(song, out)

        data = json.loads(out.read_text())
        segments = data["regions"][0]["segments"]
        assert segments == [
            {"bars": 8, "bpm": 140, "num": 4, "denom": 4},
            {"bars": 2, "bpm": 140, "num": 7, "denom": 8},
        ]


class TestRoundTripAgainstRealFixture:
    def test_export_reproduces_original_regions_and_segments(self, tmp_path):
        """Build a Song matching song_creator's own song_map.json exactly
        (bypassing genre pattern generation, which is orthogonal to the
        region/segment bridge itself) and confirm export_song_map_json
        reproduces the same regions/segments/color-groups."""
        original = json.loads(FIXTURE.read_text())

        song = Song(
            name="roundtrip",
            tempo=original["regions"][0]["segments"][0]["bpm"],
        )
        song.metadata["song_map_title"] = original["title"]
        song.metadata["color_groups"] = original["color_groups"]

        for region in original["regions"]:
            segments = [
                SongSegment(
                    bars=seg["bars"],
                    tempo=seg["bpm"],
                    time_signature=TimeSignature(seg["num"], seg["denom"]),
                )
                for seg in region["segments"]
            ]
            total_bars = sum(s.bars for s in segments)
            section = Section(
                region["name"].lower(),
                Pattern("p"),
                total_bars,
                segments=segments,
            )
            section.section_parameters["color_group"] = region["color_group"]
            section.section_parameters["display_name"] = region["name"]
            song.add_section(section)

        api = DrumGeneratorAPI()
        out = tmp_path / "roundtrip.json"
        api.export_song_map_json(song, out)
        reexported = json.loads(out.read_text())

        assert reexported["title"] == original["title"]
        assert reexported["color_groups"] == original["color_groups"]
        assert len(reexported["regions"]) == len(original["regions"])
        for original_region, reexported_region in zip(
            original["regions"], reexported["regions"], strict=True
        ):
            assert reexported_region["name"] == original_region["name"]
            assert (
                reexported_region["color_group"]
                == original_region["color_group"]
            )
            assert reexported_region["segments"] == original_region["segments"]


class TestFlatSidecarPathUnchanged:
    def test_export_sections_json_still_works(self, tmp_path):
        song = Song(name="s", tempo=120)
        song.add_section(Section("verse", Pattern("p"), bars=4))

        api = DrumGeneratorAPI()
        out = tmp_path / "sidecar.json"
        api.export_sections_json(song, out)

        data = json.loads(out.read_text())
        assert data["source"] == "python"
        assert data["tempo"] == 120
        assert data["sections"] == [
            {"name": "Verse", "bars": 4, "color": data["sections"][0]["color"]}
        ]
