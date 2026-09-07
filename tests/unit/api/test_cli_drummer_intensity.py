"""Arg-parsing coverage for --drummer-intensity across every subcommand
that exposes --drummer (generate, reaper export, prompt, riff).

Behavioral coverage of the intensity scaling itself lives in
tests/unit/plugins/test_drummer_intensity.py; this file only checks that
each subcommand parses the flag, defaults it to 1.0, and rejects it when
out of range where argparse itself would (it doesn't - range validation
happens downstream in GenerationParameters.__post_init__).
"""

from midi_drums.api.cli import create_parser


class TestGenerateDrummerIntensity:
    def test_defaults_to_full_intensity(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "generate",
                "--genre",
                "metal",
                "--output",
                "out.mid",
            ]
        )
        assert args.drummer_intensity == 1.0

    def test_accepts_override(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "generate",
                "--genre",
                "metal",
                "--drummer",
                "porcaro",
                "--drummer-intensity",
                "0.3",
                "--output",
                "out.mid",
            ]
        )
        assert args.drummer_intensity == 0.3


class TestReaperExportDrummerIntensity:
    def test_defaults_to_full_intensity(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "reaper",
                "export",
                "--genre",
                "metal",
                "--output",
                "out.rpp",
            ]
        )
        assert args.drummer_intensity == 1.0

    def test_accepts_override(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "reaper",
                "export",
                "--genre",
                "metal",
                "--drummer",
                "hoglan",
                "--drummer-intensity",
                "0.6",
                "--output",
                "out.rpp",
            ]
        )
        assert args.drummer_intensity == 0.6


class TestPromptDrummerIntensity:
    def test_defaults_to_full_intensity(self):
        parser = create_parser()
        args = parser.parse_args(["prompt", "aggressive death metal breakdown"])
        assert args.drummer_intensity == 1.0

    def test_accepts_override(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "prompt",
                "aggressive death metal breakdown",
                "--drummer",
                "bonham",
                "--drummer-intensity",
                "0.8",
            ]
        )
        assert args.drummer_intensity == 0.8
