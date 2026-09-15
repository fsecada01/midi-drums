"""Tests for the `list kit-map` CLI subtype (ADR 0009 - Step Editor panel
note map, fetched by the REAPER panel instead of a hardcoded Lua table).
"""

import json

import pytest

from midi_drums.api.cli import create_parser, handle_list_command
from midi_drums.core.models.kit import DrumKit
from midi_drums.generation.engines.drum_generator import DrumGenerator


class TestListKitMapArgParsing:
    def test_list_kit_map_parses(self):
        parser = create_parser()
        args = parser.parse_args(["list", "kit-map", "--mapping", "ezdrummer3"])

        assert args.list_type == "kit-map"
        assert args.mapping == "ezdrummer3"

    def test_mapping_is_required(self):
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["list", "kit-map"])


class TestListKitMapCommandBehavior:
    def test_prints_single_line_json_with_expected_keys(self, capsys):
        parser = create_parser()
        args = parser.parse_args(["list", "kit-map", "--mapping", "ezdrummer3"])
        generator = DrumGenerator()

        handle_list_command(args, generator)

        captured = capsys.readouterr()
        json_lines = [
            line for line in captured.out.splitlines() if line.startswith("{")
        ]
        assert len(json_lines) == 1

        payload = json.loads(json_lines[0])
        assert set(payload.keys()) == {"mapping", "notes"}
        assert payload["mapping"] == "ezdrummer3"

    def test_notes_match_drum_kit_kit_map(self, capsys):
        parser = create_parser()
        args = parser.parse_args(["list", "kit-map", "--mapping", "gm_drums"])
        generator = DrumGenerator()

        handle_list_command(args, generator)

        captured = capsys.readouterr()
        json_line = next(
            line for line in captured.out.splitlines() if line.startswith("{")
        )
        payload = json.loads(json_line)

        expected = DrumKit.create_gm_drums_kit().kit_map()
        assert payload["notes"] == expected

    def test_unknown_mapping_exits_with_error(self, capsys):
        parser = create_parser()
        args = parser.parse_args(
            ["list", "kit-map", "--mapping", "not_a_real_mapping"]
        )
        generator = DrumGenerator()

        with pytest.raises(SystemExit):
            handle_list_command(args, generator)

        captured = capsys.readouterr()
        assert "not_a_real_mapping" in captured.err
