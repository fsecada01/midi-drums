"""Command-line interface for drum generation."""

import argparse
import sys
from pathlib import Path

from midi_drums.core.engine import DrumGenerator
from midi_drums.models.kit import DrumKit


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate MIDI drum tracks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a metal song
  python -m midi_drums.api.cli generate --genre metal --style death \
      --tempo 180 --output song.mid

  # Generate a single pattern
  python -m midi_drums.api.cli pattern --genre jazz --section verse \
      --output pattern.mid

  # List available options
  python -m midi_drums.api.cli list genres
  python -m midi_drums.api.cli list styles --genre metal
        """,
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands"
    )

    # Generate song command
    gen_parser = subparsers.add_parser(
        "generate", help="Generate a complete song"
    )
    gen_parser.add_argument(
        "--genre", required=True, help="Genre (e.g., metal, rock, jazz)"
    )
    gen_parser.add_argument(
        "--style", default="default", help="Style within genre"
    )
    gen_parser.add_argument(
        "--tempo", type=int, default=120, help="Tempo in BPM"
    )
    gen_parser.add_argument(
        "--output", "-o", required=True, help="Output MIDI file"
    )
    gen_parser.add_argument("--name", help="Song name")
    gen_parser.add_argument(
        "--complexity",
        type=float,
        default=0.5,
        help="Complexity level (0.0-1.0)",
    )
    gen_parser.add_argument(
        "--humanization",
        type=float,
        default=0.3,
        help="Humanization level (0.0-1.0)",
    )
    gen_parser.add_argument("--drummer", help="Drummer style to apply")
    gen_parser.add_argument(
        "--mapping",
        "--vst",
        default="ezdrummer3",
        help=(
            "MIDI mapping preset (ezdrummer3, studio_drummer3, "
            "addictive_drums, bfd3, gm_drums, modo_drums, ml_drums, "
            "metal, jazz)"
        ),
    )

    # Generate pattern command
    pattern_parser = subparsers.add_parser(
        "pattern", help="Generate a single pattern"
    )
    pattern_parser.add_argument("--genre", required=True, help="Genre")
    pattern_parser.add_argument(
        "--section",
        default="verse",
        help="Section type (verse, chorus, bridge, etc.)",
    )
    pattern_parser.add_argument(
        "--style", default="default", help="Style within genre"
    )
    pattern_parser.add_argument(
        "--bars", type=int, default=4, help="Number of bars"
    )
    pattern_parser.add_argument(
        "--tempo", type=int, default=120, help="Tempo in BPM"
    )
    pattern_parser.add_argument(
        "--output", "-o", required=True, help="Output MIDI file"
    )
    pattern_parser.add_argument(
        "--complexity",
        type=float,
        default=0.5,
        help="Complexity level (0.0-1.0)",
    )
    pattern_parser.add_argument(
        "--mapping",
        "--vst",
        default="ezdrummer3",
        help=(
            "MIDI mapping preset (ezdrummer3, studio_drummer3, "
            "addictive_drums, bfd3, gm_drums, modo_drums, ml_drums, "
            "metal, jazz)"
        ),
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List available options")
    list_subparsers = list_parser.add_subparsers(dest="list_type")

    list_subparsers.add_parser("genres", help="List available genres")
    list_subparsers.add_parser("drummers", help="List available drummers")
    list_subparsers.add_parser(
        "mappings", help="List available MIDI mapping presets"
    )

    styles_parser = list_subparsers.add_parser(
        "styles", help="List styles for a genre"
    )
    styles_parser.add_argument("--genre", required=True, help="Genre name")

    # Info command
    subparsers.add_parser("info", help="Get information about the system")

    return parser


def handle_generate_command(args, generator: DrumGenerator) -> None:
    """Handle song generation command."""
    try:
        # Create drum kit from mapping preset
        drum_kit = DrumKit.from_preset(args.mapping)

        song = generator.create_song(
            genre=args.genre,
            style=args.style,
            tempo=args.tempo,
            complexity=args.complexity,
            humanization=args.humanization,
            drummer=args.drummer,
            drum_kit=drum_kit,
        )

        if args.name:
            song.name = args.name

        output_path = Path(args.output)
        generator.export_midi(song, output_path)

        print(f"Generated song: {song.name}")
        print(f"Saved to: {output_path}")
        print(f"Genre: {args.genre} ({args.style})")
        print(f"Tempo: {args.tempo} BPM")

        # Show song info
        info = generator.get_song_info(song)
        print(f"Duration: {info['duration_seconds']:.1f}s")
        print(f"Bars: {info['total_bars']}")
        print(f"Beats: {info['total_beats']}")

    except Exception as e:
        print(f"Error generating song: {e}", file=sys.stderr)
        sys.exit(1)


def handle_pattern_command(args, generator: DrumGenerator) -> None:
    """Handle pattern generation command."""
    try:
        # Create drum kit from mapping preset
        drum_kit = DrumKit.from_preset(args.mapping)

        pattern = generator.generate_pattern(
            genre=args.genre,
            section=args.section,
            style=args.style,
            bars=args.bars,
            complexity=args.complexity,
        )

        if not pattern:
            print(
                f"Failed to generate pattern for {args.genre}/{args.section}",
                file=sys.stderr,
            )
            sys.exit(1)

        output_path = Path(args.output)
        generator.export_pattern_midi(
            pattern, output_path, args.tempo, drum_kit=drum_kit
        )

        print(f"Generated pattern: {pattern.name}")
        print(f"Saved to: {output_path}")
        print(f"Genre: {args.genre} ({args.style})")
        print(f"Section: {args.section}")
        print(f"Bars: {args.bars}")
        print(f"Beats: {len(pattern.beats)}")

    except Exception as e:
        print(f"Error generating pattern: {e}", file=sys.stderr)
        sys.exit(1)


def handle_list_command(args, generator: DrumGenerator) -> None:
    """Handle list command."""
    try:
        if args.list_type == "genres":
            genres = generator.get_available_genres()
            print("Available genres:")
            for genre in sorted(genres):
                print(f"  {genre}")

        elif args.list_type == "drummers":
            drummers = generator.get_available_drummers()
            print("Available drummers:")
            for drummer in sorted(drummers):
                print(f"  {drummer}")

        elif args.list_type == "styles":
            styles = generator.get_styles_for_genre(args.genre)
            print(f"Available styles for '{args.genre}':")
            for style in sorted(styles):
                print(f"  {style}")

        elif args.list_type == "mappings":
            mappings = DrumKit.list_presets()
            print("Available MIDI mapping presets:")
            for preset_name, description in mappings.items():
                print(f"  {preset_name:<18} - {description}")

    except Exception as e:
        print(f"Error listing options: {e}", file=sys.stderr)
        sys.exit(1)


def handle_info_command(args, generator: DrumGenerator) -> None:
    """Handle info command."""
    print("MIDI Drums Generator")
    print("=" * 40)

    try:
        genres = generator.get_available_genres()
        drummers = generator.get_available_drummers()

        print(f"Genres: {len(genres)}")
        print(f"Drummers: {len(drummers)}")
        print("Plugin system: Active")

        print("\nAvailable genres:")
        for genre in sorted(genres):
            styles = generator.get_styles_for_genre(genre)
            print(f"  {genre} ({len(styles)} styles)")

    except Exception as e:
        print(f"Error getting system info: {e}", file=sys.stderr)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize generator
    try:
        generator = DrumGenerator()
    except Exception as e:
        print(f"Failed to initialize drum generator: {e}", file=sys.stderr)
        sys.exit(1)

    # Route to appropriate handler
    if args.command == "generate":
        handle_generate_command(args, generator)
    elif args.command == "pattern":
        handle_pattern_command(args, generator)
    elif args.command == "list":
        handle_list_command(args, generator)
    elif args.command == "info":
        handle_info_command(args, generator)


if __name__ == "__main__":
    main()
