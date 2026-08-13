"""Tests for the --mapping-file CLI option (issue #47, AC Group 1)."""

import json

from midi_drums.api.cli import create_parser, handle_generate_command
from midi_drums.generation.engines.drum_generator import DrumGenerator


class TestMappingFileArgParsing:
    """--mapping-file is accepted by both generate and pattern subcommands."""

    def test_generate_accepts_mapping_file(self):
        parser = create_parser()

        args = parser.parse_args(
            [
                "generate",
                "--genre",
                "metal",
                "--output",
                "out.mid",
                "--mapping-file",
                "custom.json",
            ]
        )

        assert args.mapping_file == "custom.json"

    def test_pattern_accepts_mapping_file(self):
        parser = create_parser()

        args = parser.parse_args(
            [
                "pattern",
                "--genre",
                "metal",
                "--output",
                "out.mid",
                "--mapping-file",
                "custom.json",
            ]
        )

        assert args.mapping_file == "custom.json"

    def test_mapping_file_defaults_to_none(self):
        parser = create_parser()

        args = parser.parse_args(
            ["generate", "--genre", "metal", "--output", "out.mid"]
        )

        assert args.mapping_file is None


class TestGenerateCommandUsesMappingFile:
    """handle_generate_command() builds the drum_kit from --mapping-file
    when supplied, taking precedence over --mapping."""

    def test_mapping_file_takes_precedence_over_mapping(self, tmp_path):
        mapping_path = tmp_path / "custom_kit.json"
        mapping_path.write_text(
            json.dumps({"name": "File Kit", "mappings": {"KICK": 30}}),
            encoding="utf-8",
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
                "--mapping",
                "ezdrummer3",
                "--mapping-file",
                str(mapping_path),
            ]
        )

        generator = DrumGenerator()
        handle_generate_command(args, generator)

        assert generator.drum_kit.name == "File Kit"
        assert output_path.exists()
