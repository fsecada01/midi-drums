"""Tests for the `list options` CLI subtype (single-line JSON for tooling,
e.g. the REAPER panel's dropdowns - see the "options" subtype's help text
in create_parser()).

Behavioral coverage prints real JSON via the real plugin system (genres/
drummers/mappings are plugin-discovered, not a fixed compile-time set - see
CLAUDE.md's "REAPER Lua Script Integration" section), so these assert on
shape/keys rather than a hardcoded genre/drummer list that would go stale
the moment a new plugin is added.
"""

import json

from midi_drums.api.cli import create_parser, handle_list_command
from midi_drums.generation.engines.drum_generator import DrumGenerator


class TestListOptionsArgParsing:
    def test_list_options_parses(self):
        parser = create_parser()
        args = parser.parse_args(["list", "options"])
        assert args.list_type == "options"


class TestListOptionsCommandBehavior:
    def test_list_options_prints_single_line_json_with_expected_keys(
        self, capsys
    ):
        parser = create_parser()
        args = parser.parse_args(["list", "options"])
        generator = DrumGenerator()

        handle_list_command(args, generator)

        captured = capsys.readouterr()
        json_lines = [
            line for line in captured.out.splitlines() if line.startswith("{")
        ]
        assert len(json_lines) == 1

        payload = json.loads(json_lines[0])
        assert set(payload.keys()) == {
            "genres",
            "drummers",
            "mappings",
            "genre_styles",
        }

    def test_list_options_genres_include_all_discovered_genres(self, capsys):
        parser = create_parser()
        args = parser.parse_args(["list", "options"])
        generator = DrumGenerator()

        handle_list_command(args, generator)

        captured = capsys.readouterr()
        json_line = next(
            line for line in captured.out.splitlines() if line.startswith("{")
        )
        payload = json.loads(json_line)

        assert set(payload["genres"]) == set(generator.get_available_genres())
        assert set(payload["drummers"]) == set(
            generator.get_available_drummers()
        )

    def test_list_options_genre_styles_are_flat_genre_style_pairs(self, capsys):
        # Flat {genre, style} pairs, not a nested genre -> [styles] map -
        # see the comment in handle_list_command's "options" branch.
        parser = create_parser()
        args = parser.parse_args(["list", "options"])
        generator = DrumGenerator()

        handle_list_command(args, generator)

        captured = capsys.readouterr()
        json_line = next(
            line for line in captured.out.splitlines() if line.startswith("{")
        )
        payload = json.loads(json_line)

        assert len(payload["genre_styles"]) > 0
        for entry in payload["genre_styles"]:
            assert set(entry.keys()) == {"genre", "style"}
            assert entry["genre"] in payload["genres"]
            assert entry["style"] in generator.get_styles_for_genre(
                entry["genre"]
            )

    def test_list_options_mappings_match_drum_kit_presets(self, capsys):
        from midi_drums.core.models.kit import DrumKit

        parser = create_parser()
        args = parser.parse_args(["list", "options"])
        generator = DrumGenerator()

        handle_list_command(args, generator)

        captured = capsys.readouterr()
        json_line = next(
            line for line in captured.out.splitlines() if line.startswith("{")
        )
        payload = json.loads(json_line)

        assert set(payload["mappings"]) == set(DrumKit.list_presets().keys())
