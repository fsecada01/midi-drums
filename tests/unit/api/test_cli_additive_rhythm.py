"""Tests for the `additive-rhythm` CLI subcommand (see
claudedocs/design_additive_rhythm_grouping.md).
"""

from midi_drums.api.cli import create_parser, handle_additive_rhythm_command


class TestAdditiveRhythmArgParsing:
    def test_defaults(self):
        parser = create_parser()
        args = parser.parse_args(
            ["additive-rhythm", "3-3-3-3-2-2", "--output", "out.mid"]
        )
        assert args.grouping == "3-3-3-3-2-2"
        assert args.grid == 16
        assert args.tempo == 120
        assert args.drummer is None
        assert args.drummer_intensity == 1.0
        assert args.output == "out.mid"

    def test_drummer_and_intensity_parse(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "additive-rhythm",
                "3-3-3-3-2-2",
                "--drummer",
                "bonham",
                "--drummer-intensity",
                "0.5",
                "--output",
                "out.mid",
            ]
        )
        assert args.drummer == "bonham"
        assert args.drummer_intensity == 0.5


class TestAdditiveRhythmDrummerStyling:
    def test_drummer_flag_produces_output_file(self, tmp_path):
        output_path = tmp_path / "styled.mid"
        parser = create_parser()
        args = parser.parse_args(
            [
                "additive-rhythm",
                "3-3-3-3-2-2",
                "--drummer",
                "bonham",
                "--output",
                str(output_path),
            ]
        )

        handle_additive_rhythm_command(args)

        assert output_path.exists()

    def test_unknown_drummer_falls_back_to_unstyled_pattern(self, tmp_path):
        """Matches the rest of the CLI's convention (e.g. `generate`,
        `riff`): an unrecognized --drummer logs an error via
        PluginManager but does not abort generation."""
        output_path = tmp_path / "fallback.mid"
        parser = create_parser()
        args = parser.parse_args(
            [
                "additive-rhythm",
                "3-3-3-3-2-2",
                "--drummer",
                "not-a-real-drummer",
                "--output",
                str(output_path),
            ]
        )

        handle_additive_rhythm_command(args)

        assert output_path.exists()

    def test_no_drummer_flag_still_works(self, tmp_path):
        output_path = tmp_path / "plain.mid"
        parser = create_parser()
        args = parser.parse_args(
            [
                "additive-rhythm",
                "3-3-3-3-2-2",
                "--output",
                str(output_path),
            ]
        )

        handle_additive_rhythm_command(args)

        assert output_path.exists()
