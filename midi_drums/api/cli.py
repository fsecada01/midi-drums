"""Command-line interface for drum generation."""

import argparse
import sys
from pathlib import Path

from midi_drums.core.engine import DrumGenerator
from midi_drums.exporters.reaper_exporter import ReaperExporter
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

  # Reaper integration
  python -m midi_drums.api.cli reaper export --genre metal --style doom \
      --tempo 120 --output doom.rpp
  python -m midi_drums.api.cli reaper add-markers --song doom.mid \
      --output project.rpp
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

    # Reaper command
    reaper_parser = subparsers.add_parser(
        "reaper", help="Reaper DAW integration"
    )
    reaper_subparsers = reaper_parser.add_subparsers(dest="reaper_command")

    # Reaper export command
    reaper_export = reaper_subparsers.add_parser(
        "export", help="Generate drums and create Reaper project with markers"
    )
    reaper_export.add_argument(
        "--genre", required=True, help="Genre (e.g., metal, rock, jazz)"
    )
    reaper_export.add_argument(
        "--style", default="default", help="Style within genre"
    )
    reaper_export.add_argument(
        "--tempo", type=int, default=120, help="Tempo in BPM"
    )
    reaper_export.add_argument(
        "--output", "-o", required=True, help="Output Reaper project (.rpp)"
    )
    reaper_export.add_argument("--name", help="Song name")
    reaper_export.add_argument(
        "--complexity",
        type=float,
        default=0.5,
        help="Complexity level (0.0-1.0)",
    )
    reaper_export.add_argument(
        "--humanization",
        type=float,
        default=0.3,
        help="Humanization level (0.0-1.0)",
    )
    reaper_export.add_argument("--drummer", help="Drummer style to apply")
    reaper_export.add_argument(
        "--template", help="Input Reaper template (.rpp) to use as base"
    )
    reaper_export.add_argument(
        "--midi",
        nargs="?",
        const="",
        help=(
            "Also export MIDI file (auto-generates filename based on .rpp "
            "name, or specify custom filename)"
        ),
    )
    reaper_export.add_argument(
        "--marker-color",
        default="#FF5733",
        help="Hex color for markers (default: #FF5733)",
    )

    # Reaper add-markers command
    reaper_markers = reaper_subparsers.add_parser(
        "add-markers",
        help="Add markers to Reaper project based on song structure",
    )
    reaper_markers.add_argument(
        "--song",
        help=(
            "Input MIDI file (optional). If metadata.json exists in the same "
            "directory, it will be used automatically."
        ),
    )
    reaper_markers.add_argument(
        "--output", "-o", required=True, help="Output Reaper project (.rpp)"
    )
    reaper_markers.add_argument(
        "--metadata",
        help=(
            "Path to metadata.json file (contains structure, tempo, "
            "time signature)"
        ),
    )
    reaper_markers.add_argument(
        "--structure",
        help=(
            'Song structure as "section:bars,section:bars". '
            'Example: "intro:4,verse:8,chorus:8,verse:8,outro:4". '
            "Required if --metadata not provided."
        ),
    )
    reaper_markers.add_argument(
        "--tempo",
        type=int,
        help="Tempo in BPM (default: 120, or from metadata)",
    )
    reaper_markers.add_argument(
        "--template", help="Input Reaper template (.rpp) to use as base"
    )
    reaper_markers.add_argument(
        "--marker-color",
        default="#FF5733",
        help="Hex color for markers (default: #FF5733)",
    )
    reaper_markers.add_argument(
        "--time-signature",
        help="Time signature (default: 4/4, or from metadata)",
    )

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


def handle_reaper_export_command(args, generator: DrumGenerator) -> None:
    """Handle Reaper export command."""
    try:
        # Create drum kit
        drum_kit = DrumKit.from_preset("ezdrummer3")

        # Generate song
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

        # Export to Reaper
        exporter = ReaperExporter()
        output_path = Path(args.output)

        exporter.export_with_markers(
            song=song,
            output_rpp=str(output_path),
            input_rpp=args.template,
            marker_color=args.marker_color,
        )

        print(f"Generated song: {song.name}")
        print(f"Reaper project saved to: {output_path}")
        print(f"Genre: {args.genre} ({args.style})")
        print(f"Tempo: {args.tempo} BPM")

        # Show song info
        info = generator.get_song_info(song)
        print(f"Duration: {info['duration_seconds']:.1f}s")
        print(f"Sections: {len(song.sections)}")
        print(f"Markers added: {len(song.sections)}")

        # Export MIDI if requested
        if args.midi is not None:
            midi_path = (
                Path(args.midi)
                if args.midi
                else output_path.with_suffix(".mid")
            )
            generator.export_midi(song, midi_path)
            print(f"MIDI file saved to: {midi_path}")

    except Exception as e:
        print(f"Error exporting to Reaper: {e}", file=sys.stderr)
        sys.exit(1)


def handle_reaper_add_markers_command(args, generator: DrumGenerator) -> None:
    """Handle Reaper add-markers command."""
    try:
        import json

        from midi_drums.models.song import Section, Song, TimeSignature

        # Auto-detect metadata from song directory if not explicitly provided
        metadata_file = args.metadata
        if not metadata_file and args.song:
            song_path = Path(args.song)
            potential_metadata = song_path.parent / "metadata.json"
            if potential_metadata.exists():
                metadata_file = str(potential_metadata)
                print(
                    f"Auto-detected metadata file: {potential_metadata.name}",
                    file=sys.stderr,
                )

        # Determine data source: metadata file or manual arguments
        if metadata_file:
            # Read from metadata file
            try:
                metadata_path = Path(metadata_file)
                if not metadata_path.exists():
                    print(
                        f"Error: Metadata file not found: {metadata_file}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                with open(metadata_path) as f:
                    metadata = json.load(f)

                # Extract song information
                song_info = metadata.get("song", {})
                tempo = (
                    args.tempo if args.tempo else song_info.get("tempo", 120)
                )
                time_sig_str = (
                    args.time_signature
                    if args.time_signature
                    else song_info.get("time_signature", "4/4")
                )
                song_name = song_info.get("name", "markers")

                # Extract structure
                structure_data = metadata.get("structure", [])
                if not structure_data:
                    print(
                        "Error: No structure found in metadata file",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                sections = []
                for section_data in structure_data:
                    sections.append(
                        Section(
                            name=section_data["name"],
                            bars=section_data["bars"],
                            pattern=None,  # No pattern needed for markers only
                        )
                    )

                print(f"Loaded structure from metadata: {metadata_file}")

            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error reading metadata file: {e}", file=sys.stderr)
                sys.exit(1)

        else:
            # Parse manual structure specification
            if not args.structure:
                print(
                    "Error: Either --metadata or --structure must be provided",
                    file=sys.stderr,
                )
                sys.exit(1)

            try:
                sections = []
                for part in args.structure.split(","):
                    section_name, bars = part.strip().split(":")
                    sections.append(
                        Section(
                            name=section_name.strip(),
                            bars=int(bars),
                            pattern=None,  # No pattern needed for markers only
                        )
                    )
                tempo = args.tempo if args.tempo else 120
                time_sig_str = (
                    args.time_signature if args.time_signature else "4/4"
                )
                song_name = "markers"

            except (ValueError, AttributeError) as e:
                print(f"Error parsing structure: {e}", file=sys.stderr)
                print(
                    'Expected format: "section:bars,section:bars"',
                    file=sys.stderr,
                )
                print('Example: "intro:4,verse:8,chorus:8"', file=sys.stderr)
                sys.exit(1)

        # Parse time signature
        try:
            numerator, denominator = map(int, time_sig_str.split("/"))
            time_sig = TimeSignature(numerator, denominator)
        except (ValueError, AttributeError):
            print(f"Invalid time signature: {time_sig_str}", file=sys.stderr)
            print('Expected format: "4/4" or "3/4"', file=sys.stderr)
            sys.exit(1)

        # Create song structure for marker calculation
        song = Song(
            name=song_name,
            tempo=tempo,
            time_signature=time_sig,
            sections=sections,
        )

        # Export to Reaper
        exporter = ReaperExporter()
        exporter.export_with_markers(
            song=song,
            output_rpp=args.output,
            input_rpp=args.template,
            marker_color=args.marker_color,
        )

        print(f"Created Reaper project: {args.output}")
        print(f"Song: {song_name}")
        print(f"Tempo: {tempo} BPM")
        print(f"Time signature: {time_sig_str}")
        print(f"Sections: {len(sections)}")
        print(f"Markers added: {len(sections)}")

        if args.song:
            print(f"\nNote: MIDI file '{args.song}' provided for reference")
            print("Import it manually in Reaper or copy to project directory")

    except Exception as e:
        print(f"Error adding markers: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


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
    elif args.command == "reaper":
        if args.reaper_command == "export":
            handle_reaper_export_command(args, generator)
        elif args.reaper_command == "add-markers":
            handle_reaper_add_markers_command(args, generator)
        else:
            print(
                "Error: Please specify a reaper subcommand (export or "
                "add-markers)",
                file=sys.stderr,
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
