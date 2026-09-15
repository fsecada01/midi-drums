"""Tests for the `adjust-density` CLI subcommand (ADR 0010)."""

import json

from midi_drums.api.cli import create_parser, handle_adjust_density_command


class TestAdjustDensityArgParsing:
    def test_required_args_parse(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "adjust-density",
                "--input",
                "in.json",
                "--output",
                "out.json",
                "--instrument",
                "SNARE",
                "--amount",
                "0.5",
                "--grid",
                "16th",
            ]
        )
        assert args.input == "in.json"
        assert args.output == "out.json"
        assert args.instrument == "SNARE"
        assert args.amount == 0.5
        assert args.grid == "16th"

    def test_defaults(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "adjust-density",
                "--input",
                "in.json",
                "--output",
                "out.json",
                "--instrument",
                "SNARE",
                "--amount",
                "0.5",
                "--grid",
                "16th",
            ]
        )
        assert args.kind == "main"
        assert args.ts_num == 4
        assert args.ts_denom == 4
        assert args.bars == 1
        assert args.genre is None
        assert args.style is None
        assert args.drummer is None
        assert args.complexity is None

    def test_context_and_kind_parse(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "adjust-density",
                "--input",
                "in.json",
                "--output",
                "out.json",
                "--instrument",
                "SNARE",
                "--amount",
                "-0.3",
                "--grid",
                "8th_triplet",
                "--kind",
                "ghost",
                "--bars",
                "2",
                "--genre",
                "metal",
                "--style",
                "death",
                "--drummer",
                "hoglan",
                "--complexity",
                "0.8",
            ]
        )
        assert args.amount == -0.3
        assert args.grid == "8th_triplet"
        assert args.kind == "ghost"
        assert args.bars == 2
        assert args.genre == "metal"
        assert args.style == "death"
        assert args.drummer == "hoglan"
        assert args.complexity == 0.8


class TestAdjustDensityHandler:
    def test_writes_result_json_matching_input_shape(self, tmp_path):
        input_path = tmp_path / "in.json"
        output_path = tmp_path / "out.json"
        input_path.write_text(
            json.dumps(
                [
                    {
                        "bar": 0,
                        "step": 0,
                        "velocity": 100,
                        "off_grid": False,
                        "_idx": 0,
                    }
                ]
            )
        )

        parser = create_parser()
        args = parser.parse_args(
            [
                "adjust-density",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--instrument",
                "SNARE",
                "--amount",
                "1.0",
                "--grid",
                "16th",
                "--bars",
                "1",
            ]
        )
        handle_adjust_density_command(args)

        result = json.loads(output_path.read_text())
        assert isinstance(result, list)
        assert len(result) == 16  # every 16th-note slot in one bar of 4/4

    def test_removal_shrinks_the_note_list(self, tmp_path):
        input_path = tmp_path / "in.json"
        output_path = tmp_path / "out.json"
        input_path.write_text(
            json.dumps(
                [
                    {
                        "bar": 0,
                        "step": s,
                        "velocity": 100,
                        "off_grid": False,
                        "_idx": s,
                    }
                    for s in range(4)
                ]
            )
        )

        parser = create_parser()
        args = parser.parse_args(
            [
                "adjust-density",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--instrument",
                "KICK",
                "--amount",
                "-1.0",
                "--grid",
                "16th",
            ]
        )
        handle_adjust_density_command(args)

        result = json.loads(output_path.read_text())
        assert result == []

    def test_invalid_input_json_exits_nonzero(self, tmp_path, capsys):
        input_path = tmp_path / "in.json"
        output_path = tmp_path / "out.json"
        input_path.write_text("not valid json")

        parser = create_parser()
        args = parser.parse_args(
            [
                "adjust-density",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--instrument",
                "KICK",
                "--amount",
                "0.5",
                "--grid",
                "16th",
            ]
        )
        try:
            handle_adjust_density_command(args)
            raised = False
        except SystemExit as e:
            raised = True
            assert e.code == 1
        assert raised
        assert "Error reading --input" in capsys.readouterr().err

    def test_amount_out_of_range_exits_nonzero(self, tmp_path, capsys):
        input_path = tmp_path / "in.json"
        output_path = tmp_path / "out.json"
        input_path.write_text("[]")

        parser = create_parser()
        args = parser.parse_args(
            [
                "adjust-density",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--instrument",
                "KICK",
                "--amount",
                "5.0",
                "--grid",
                "16th",
            ]
        )
        try:
            handle_adjust_density_command(args)
            raised = False
        except SystemExit as e:
            raised = True
            assert e.code == 1
        assert raised
        assert "Error:" in capsys.readouterr().err
