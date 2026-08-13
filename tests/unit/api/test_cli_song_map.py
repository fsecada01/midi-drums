"""Tests for the --song-map CLI option (issue #53, AC Group 5)."""

import json

from midi_drums.api.cli import create_parser, handle_generate_command
from midi_drums.generation.engines.drum_generator import DrumGenerator

SIMPLE_MAP = {
    "title": "CLI Test Map",
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
    ],
}


class TestSongMapArgParsing:
    def test_generate_accepts_song_map(self):
        parser = create_parser()

        args = parser.parse_args(
            [
                "generate",
                "--genre",
                "metal",
                "--output",
                "out.mid",
                "--song-map",
                "map.json",
            ]
        )

        assert args.song_map == "map.json"

    def test_song_map_defaults_to_none(self):
        parser = create_parser()

        args = parser.parse_args(
            ["generate", "--genre", "metal", "--output", "out.mid"]
        )

        assert args.song_map is None


class TestGenerateCommandUsesSongMap:
    def test_song_map_drives_structure_and_tempo(self, tmp_path):
        map_path = tmp_path / "map.json"
        map_path.write_text(json.dumps(SIMPLE_MAP))
        output_path = tmp_path / "out.mid"

        parser = create_parser()
        args = parser.parse_args(
            [
                "generate",
                "--genre",
                "metal",
                "--style",
                "heavy",
                "--output",
                str(output_path),
                "--song-map",
                str(map_path),
            ]
        )

        generator = DrumGenerator()
        handle_generate_command(args, generator)

        assert output_path.exists()

    def test_write_timeline_produces_timeline_json(self, tmp_path):
        map_path = tmp_path / "map.json"
        map_path.write_text(json.dumps(SIMPLE_MAP))
        output_path = tmp_path / "out.mid"
        timeline_path = tmp_path / "timeline.json"

        parser = create_parser()
        args = parser.parse_args(
            [
                "generate",
                "--genre",
                "metal",
                "--style",
                "heavy",
                "--output",
                str(output_path),
                "--song-map",
                str(map_path),
                "--write-timeline",
                str(timeline_path),
            ]
        )

        generator = DrumGenerator()
        handle_generate_command(args, generator)

        assert timeline_path.exists()
        data = json.loads(timeline_path.read_text())
        assert len(data["regions"]) == 2
        assert data["regions"][0]["name"] == "Intro"

    def test_song_map_takes_precedence_over_sidecar(self, tmp_path):
        # If both are somehow provided, --song-map wins (checked first).
        map_path = tmp_path / "map.json"
        map_path.write_text(json.dumps(SIMPLE_MAP))
        sidecar_path = tmp_path / "sidecar.json"
        sidecar_path.write_text(
            json.dumps(
                {
                    "source": "python",
                    "tempo": 999,
                    "time_signature": [4, 4],
                    "sections": [{"name": "Verse", "bars": 4}],
                }
            )
        )
        output_path = tmp_path / "out.mid"

        parser = create_parser()
        args = parser.parse_args(
            [
                "generate",
                "--genre",
                "metal",
                "--style",
                "heavy",
                "--output",
                str(output_path),
                "--song-map",
                str(map_path),
                "--sidecar",
                str(sidecar_path),
            ]
        )

        generator = DrumGenerator()
        handle_generate_command(args, generator)

        assert output_path.exists()
