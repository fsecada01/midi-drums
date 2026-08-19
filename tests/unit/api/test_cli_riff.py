"""Tests for the `riff` CLI subcommand (audio riff -> kick-locked pattern).

Arg-parsing only - no librosa required. Behavioral coverage of
analyze_riff() itself lives in tests/unit/analysis/test_audio_analysis.py
(requires_audio-marked); RiffLockTransform behavior lives in
tests/unit/modifications/test_riff_lock.py.
"""

import pytest

from midi_drums.api.cli import create_parser, handle_riff_command


class TestRiffArgParsing:
    def test_riff_requires_audio_genre_tempo_output(self):
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["riff"])

    def test_riff_parses_required_args(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "riff",
                "--audio",
                "riff.wav",
                "--genre",
                "metal",
                "--tempo",
                "180",
                "--output",
                "out.mid",
            ]
        )
        assert args.audio == "riff.wav"
        assert args.genre == "metal"
        assert args.tempo == 180.0
        assert args.output == "out.mid"

    def test_riff_defaults(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "riff",
                "--audio",
                "riff.wav",
                "--genre",
                "metal",
                "--tempo",
                "180",
                "--output",
                "out.mid",
            ]
        )
        assert args.style == "default"
        assert args.section == "verse"
        assert args.time_signature == "4/4"
        assert args.bars == 4
        assert args.grid == "16th"
        assert args.lock_strength == 1.0
        assert args.offset_beats == 0.0
        assert args.audio_offset is None
        assert args.audio_duration is None
        assert args.humanization == 0.0
        assert args.mapping == "ezdrummer3"
        assert args.write_sidecar is None

    def test_riff_grid_rejects_unknown_value(self):
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(
                [
                    "riff",
                    "--audio",
                    "riff.wav",
                    "--genre",
                    "metal",
                    "--tempo",
                    "180",
                    "--output",
                    "out.mid",
                    "--grid",
                    "5th",
                ]
            )

    def test_riff_accepts_overrides(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "riff",
                "--audio",
                "riff.wav",
                "--genre",
                "metal",
                "--style",
                "death",
                "--drummer",
                "hoglan",
                "--tempo",
                "180",
                "--output",
                "out.mid",
                "--time-signature",
                "7/8",
                "--bars",
                "8",
                "--grid",
                "8th_triplet",
                "--lock-strength",
                "0.5",
                "--offset-beats",
                "0.25",
                "--audio-offset",
                "1.5",
                "--audio-duration",
                "2.0",
                "--write-sidecar",
                "sidecar.json",
            ]
        )
        assert args.style == "death"
        assert args.drummer == "hoglan"
        assert args.time_signature == "7/8"
        assert args.bars == 8
        assert args.grid == "8th_triplet"
        assert args.lock_strength == 0.5
        assert args.offset_beats == 0.25
        assert args.audio_offset == 1.5
        assert args.audio_duration == 2.0
        assert args.write_sidecar == "sidecar.json"


class TestRiffCommandBehavior:
    def test_riff_command_guards_missing_audio_dependency(
        self, monkeypatch, capsys
    ):
        # Simulate the `audio` extras group not being installed by making
        # the analyze_riff import fail, mirroring handle_prompt_command's
        # own ImportError-guard test shape.
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "midi_drums.analysis.audio_analysis":
                raise ImportError("no librosa")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        parser = create_parser()
        args = parser.parse_args(
            [
                "riff",
                "--audio",
                "riff.wav",
                "--genre",
                "metal",
                "--tempo",
                "180",
                "--output",
                "out.mid",
            ]
        )

        with pytest.raises(SystemExit) as exc_info:
            handle_riff_command(args)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "uv sync --group audio" in captured.err

    def test_riff_command_rejects_invalid_time_signature(
        self, monkeypatch, capsys
    ):
        pytest.importorskip("librosa")

        parser = create_parser()
        args = parser.parse_args(
            [
                "riff",
                "--audio",
                "riff.wav",
                "--genre",
                "metal",
                "--tempo",
                "180",
                "--output",
                "out.mid",
                "--time-signature",
                "not-a-time-sig",
            ]
        )

        with pytest.raises(SystemExit) as exc_info:
            handle_riff_command(args)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid time signature" in captured.err
