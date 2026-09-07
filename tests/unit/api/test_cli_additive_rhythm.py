"""Tests for the `additive-rhythm` CLI subcommand (see
claudedocs/design_additive_rhythm_grouping.md).
"""

import json

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

    def test_write_timeline_defaults_to_none(self):
        parser = create_parser()
        args = parser.parse_args(
            ["additive-rhythm", "3-3-3-3-2-2", "--output", "out.mid"]
        )
        assert args.write_timeline is None


class TestAdditiveRhythmTimeline:
    def test_writes_expected_bar_start_times_and_meters(self, tmp_path):
        """See CLAUDE.md's REAPER panel section: the REAPER panel's
        Additive Rhythm tab parses this JSON to place per-bar tempo/
        time-signature markers before importing the MIDI."""
        output_path = tmp_path / "out.mid"
        timeline_path = tmp_path / "timeline.json"
        parser = create_parser()
        args = parser.parse_args(
            [
                "additive-rhythm",
                "3-3-3-3-2-2",
                "--tempo",
                "120",
                "--output",
                str(output_path),
                "--write-timeline",
                str(timeline_path),
            ]
        )

        handle_additive_rhythm_command(args)

        timeline = json.loads(timeline_path.read_text())
        assert timeline["tempo"] == 120.0
        assert len(timeline["bars"]) == 2

        # Bar 1: 6/8 -> 3.0 beats at 120bpm (0.5s/beat) starting at t=0.
        assert timeline["bars"][0] == {
            "start_time": 0.0,
            "num": 6,
            "denom": 8,
        }
        # Bar 2: 2/8, starts after bar 1's 3.0 beats * 0.5s/beat = 1.5s.
        assert timeline["bars"][1] == {
            "start_time": 1.5,
            "num": 2,
            "denom": 8,
        }

    def test_no_write_timeline_flag_writes_no_file(self, tmp_path):
        output_path = tmp_path / "out.mid"
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

        assert list(tmp_path.iterdir()) == [output_path]


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
