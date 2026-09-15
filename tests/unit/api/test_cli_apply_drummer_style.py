"""Tests for the `apply-drummer-style` CLI subcommand (ADR 0011)."""

import json

from midi_drums.api.cli import create_parser, handle_apply_drummer_style_command


class TestApplyDrummerStyleArgParsing:
    def test_required_args_parse(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "apply-drummer-style",
                "--input",
                "in.json",
                "--output",
                "out.json",
            ]
        )
        assert args.input == "in.json"
        assert args.output == "out.json"

    def test_defaults(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "apply-drummer-style",
                "--input",
                "in.json",
                "--output",
                "out.json",
            ]
        )
        assert args.drummer is None
        assert args.drummer_intensity == 1.0
        assert args.timing_variance == 0.0
        assert args.velocity_variance == 0.0
        assert args.ts_num == 4
        assert args.ts_denom == 4

    def test_all_options_parse(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "apply-drummer-style",
                "--input",
                "in.json",
                "--output",
                "out.json",
                "--drummer",
                "bonham",
                "--drummer-intensity",
                "0.6",
                "--timing-variance",
                "0.03",
                "--velocity-variance",
                "12",
                "--ts-num",
                "3",
                "--ts-denom",
                "4",
            ]
        )
        assert args.drummer == "bonham"
        assert args.drummer_intensity == 0.6
        assert args.timing_variance == 0.03
        assert args.velocity_variance == 12.0
        assert args.ts_num == 3
        assert args.ts_denom == 4


class TestApplyDrummerStyleHandler:
    def test_writes_result_json_matching_input_shape(self, tmp_path):
        input_path = tmp_path / "in.json"
        output_path = tmp_path / "out.json"
        input_path.write_text(
            json.dumps(
                [
                    {
                        "instrument": "KICK",
                        "position_qn": 0.0,
                        "velocity": 105,
                        "ghost_note": False,
                        "accent": False,
                    },
                    {
                        "instrument": "SNARE",
                        "position_qn": 1.0,
                        "velocity": 100,
                        "ghost_note": False,
                        "accent": False,
                    },
                ]
            )
        )

        parser = create_parser()
        args = parser.parse_args(
            [
                "apply-drummer-style",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--drummer",
                "bonham",
            ]
        )
        handle_apply_drummer_style_command(args)

        result = json.loads(output_path.read_text())
        assert isinstance(result, list)
        assert len(result) >= 2
        assert all("instrument" in n and "position_qn" in n for n in result)

    def test_no_drummer_no_variance_round_trips_unchanged(self, tmp_path):
        input_path = tmp_path / "in.json"
        output_path = tmp_path / "out.json"
        original = [
            {
                "instrument": "KICK",
                "position_qn": 0.0,
                "velocity": 105,
                "ghost_note": False,
                "accent": False,
            }
        ]
        input_path.write_text(json.dumps(original))

        parser = create_parser()
        args = parser.parse_args(
            [
                "apply-drummer-style",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
            ]
        )
        handle_apply_drummer_style_command(args)

        result = json.loads(output_path.read_text())
        assert result == original

    def test_unmapped_instrument_passes_through(self, tmp_path):
        input_path = tmp_path / "in.json"
        output_path = tmp_path / "out.json"
        input_path.write_text(
            json.dumps(
                [
                    {
                        "instrument": "unmapped_50",
                        "position_qn": 0.5,
                        "velocity": 90,
                        "ghost_note": False,
                        "accent": False,
                    }
                ]
            )
        )

        parser = create_parser()
        args = parser.parse_args(
            [
                "apply-drummer-style",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--drummer",
                "bonham",
            ]
        )
        handle_apply_drummer_style_command(args)

        result = json.loads(output_path.read_text())
        assert any(n["instrument"] == "unmapped_50" for n in result)

    def test_invalid_input_json_exits_nonzero(self, tmp_path, capsys):
        input_path = tmp_path / "in.json"
        output_path = tmp_path / "out.json"
        input_path.write_text("not valid json")

        parser = create_parser()
        args = parser.parse_args(
            [
                "apply-drummer-style",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
            ]
        )
        try:
            handle_apply_drummer_style_command(args)
            raised = False
        except SystemExit as e:
            raised = True
            assert e.code == 1
        assert raised
        assert "Error reading --input" in capsys.readouterr().err

    def test_intensity_out_of_range_exits_nonzero(self, tmp_path, capsys):
        input_path = tmp_path / "in.json"
        output_path = tmp_path / "out.json"
        input_path.write_text("[]")

        parser = create_parser()
        args = parser.parse_args(
            [
                "apply-drummer-style",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--drummer",
                "bonham",
                "--drummer-intensity",
                "5.0",
            ]
        )
        try:
            handle_apply_drummer_style_command(args)
            raised = False
        except SystemExit as e:
            raised = True
            assert e.code == 1
        assert raised
        assert "Error:" in capsys.readouterr().err
