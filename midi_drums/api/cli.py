"""Command-line interface for drum generation."""

from __future__ import annotations

import argparse
import os
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
  python -m midi_drums.api.cli generate --genre metal --style death \\
      --tempo 180 --output song.mid

  # Generate a single pattern
  python -m midi_drums.api.cli pattern --genre jazz --section verse \\
      --output pattern.mid

  # List available options
  python -m midi_drums.api.cli list genres
  python -m midi_drums.api.cli list styles --genre metal

  # Reaper integration — full export with MIDI
  python -m midi_drums.api.cli reaper export --genre metal --style doom \\
      --tempo 120 --output doom.rpp --midi

  # Reaper integration — markers only, no MIDI (preset-only mode)
  python -m midi_drums.api.cli reaper export --genre jazz --style swing \\
      --tempo 160 --output jazz.rpp --preset-only

  # List available genre structure presets
  python -m midi_drums.api.cli reaper presets
  python -m midi_drums.api.cli reaper presets --genre metal

  # Add markers from existing metadata
  python -m midi_drums.api.cli reaper add-markers --song doom.mid \\
      --output project.rpp

  # Generate a pattern from a natural language prompt
  python -m midi_drums prompt "funky groove with ghost notes and syncopation"
  python -m midi_drums prompt "aggressive death metal breakdown" --tempo 180 -o breakdown.mid
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
        "--tempo", type=int, default=None, help="Tempo in BPM"
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
            "name, or specify custom filename). Ignored when --preset-only."
        ),
    )
    reaper_export.add_argument(
        "--marker-color",
        default="#FF5733",
        help=(
            "Hex color for markers (default: #FF5733). "
            "Ignored when --preset-only (preset colors used instead)."
        ),
    )
    reaper_export.add_argument(
        "--preset-only",
        action="store_true",
        default=False,
        help=(
            "Create the Reaper project with genre-smart structure markers "
            "without generating any MIDI audio. Much faster and does not "
            "require the drum plugin system."
        ),
    )
    reaper_export.add_argument(
        "--list-presets",
        action="store_true",
        default=False,
        help="List available genre structure presets and exit.",
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

    # Reaper presets command
    reaper_presets = reaper_subparsers.add_parser(
        "presets",
        help="List available genre structure presets",
    )
    reaper_presets.add_argument(
        "--genre",
        default=None,
        help="Filter presets to a specific genre (e.g. metal, jazz)",
    )

    # AI prompt command
    prompt_parser = subparsers.add_parser(
        "prompt",
        help="Generate a drum pattern from a natural language description",
    )
    prompt_parser.add_argument(
        "text",
        help='Natural language description in quotes, e.g. "funky groove with ghost notes"',
    )
    prompt_parser.add_argument(
        "--output", "-o", help="Output MIDI file (auto-named if omitted)"
    )
    prompt_parser.add_argument(
        "--tempo", type=int, default=120, help="Tempo in BPM (default: 120)"
    )
    prompt_parser.add_argument(
        "--section", default="verse", help="Song section (verse, chorus, …)"
    )
    prompt_parser.add_argument(
        "--bars", type=int, default=4, help="Number of bars (default: 4)"
    )
    prompt_parser.add_argument(
        "--complexity",
        type=float,
        default=0.5,
        help="Complexity 0.0–1.0 (default: 0.5)",
    )
    prompt_parser.add_argument(
        "--drummer", help="Drummer style (bonham, weckl, …)"
    )
    prompt_parser.add_argument(
        "--song",
        action="store_true",
        help=(
            "Compose a full multi-section song via the AI agent "
            "(default: single pattern)"
        ),
    )
    prompt_parser.add_argument(
        "--rpp",
        metavar="FILE.rpp",
        help="Also create a Reaper project with tempo, meter, and section markers",
    )
    prompt_parser.add_argument(
        "--save-metadata",
        action="store_true",
        help="Save a JSON metadata file alongside the MIDI (e.g. output.json)",
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
    """Handle Reaper export command.

    Supports two modes:

    * ``--preset-only``: create the ``.rpp`` with genre-smart markers from the
      preset registry, without generating any MIDI audio.
    * Normal mode: generate a full song with audio patterns, then export to
      Reaper with optional MIDI output.
    """
    # Fast path: show presets and exit
    if getattr(args, "list_presets", False):
        _print_genre_presets(genre_filter=None)
        return

    try:
        output_path = Path(args.output)

        if args.preset_only:
            # ----------------------------------------------------------------
            # Preset-only mode: no MIDI generation
            # ----------------------------------------------------------------
            from midi_drums.models.reaper_models import get_genre_preset

            exporter = ReaperExporter()
            preset = exporter.export_with_genre_preset(
                genre=args.genre,
                style=args.style,
                output_rpp=str(output_path),
                tempo=args.tempo,
                input_rpp=args.template,
                name=args.name,
            )

            resolved_tempo = (
                args.tempo if args.tempo is not None else preset.default_tempo
            )
            print(f"Reaper project saved to: {output_path}")
            print("Mode: preset-only (no MIDI generated)")
            print(f"Genre: {args.genre} ({args.style})")
            print(f"Preset matched: {preset.genre}/{preset.style}")
            print(f"Tempo: {resolved_tempo} BPM")
            print(f"Sections: {len(preset.sections)}")
            print(f"Markers added: {len(preset.sections)}")

        else:
            # ----------------------------------------------------------------
            # Full generation mode
            # ----------------------------------------------------------------
            # Create drum kit
            drum_kit = DrumKit.from_preset("ezdrummer3")

            # Resolve tempo — use preset default when not supplied
            from midi_drums.models.reaper_models import get_genre_preset

            preset = get_genre_preset(args.genre, args.style)
            resolved_tempo = (
                args.tempo if args.tempo is not None else preset.default_tempo
            )

            # Generate song
            song = generator.create_song(
                genre=args.genre,
                style=args.style,
                tempo=resolved_tempo,
                complexity=args.complexity,
                humanization=args.humanization,
                drummer=args.drummer,
                drum_kit=drum_kit,
            )

            if args.name:
                song.name = args.name

            # Attach genre metadata so the exporter picks section colors
            song.metadata["genre"] = args.genre
            song.metadata["style"] = args.style

            exporter = ReaperExporter()
            exporter.export_with_markers(
                song=song,
                output_rpp=str(output_path),
                input_rpp=args.template,
                marker_color=args.marker_color,
            )

            print(f"Generated song: {song.name}")
            print(f"Reaper project saved to: {output_path}")
            print(f"Genre: {args.genre} ({args.style})")
            print(f"Tempo: {resolved_tempo} BPM")

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


def _print_genre_presets(genre_filter: str | None = None) -> None:
    """Print genre structure presets to stdout.

    Args:
        genre_filter: When provided, only presets for this genre are shown.
    """
    from midi_drums.models.reaper_models import (
        GENRE_STRUCTURE_PRESETS,
        list_genre_presets,
    )

    all_presets = list_genre_presets()

    if genre_filter:
        g = genre_filter.lower()
        if g not in all_presets:
            print(
                f"No presets found for genre '{genre_filter}'.",
                file=sys.stderr,
            )
            print(
                f"Available genres: {', '.join(sorted(all_presets))}",
                file=sys.stderr,
            )
            sys.exit(1)
        genres_to_show = {g: all_presets[g]}
    else:
        genres_to_show = all_presets

    print("Available genre structure presets")
    print("=" * 48)
    for genre, styles in sorted(genres_to_show.items()):
        print(f"\n{genre.upper()}")
        for style in styles:
            preset = GENRE_STRUCTURE_PRESETS.get((genre, style))
            if preset is None:
                continue
            lo, hi = preset.tempo_range
            num, den = preset.time_signature
            section_names = ", ".join(s.name for s in preset.sections)
            print(f"  {style:<16}  {lo}-{hi} BPM  {num}/{den}")
            print(f"    Sections: {section_names}")


def handle_reaper_presets_command(args) -> None:
    """Handle 'reaper presets' command.

    Args:
        args: Parsed CLI arguments (expects ``args.genre``).
    """
    _print_genre_presets(genre_filter=getattr(args, "genre", None))


def _print_ai_setup_help(provider: str | None = None) -> None:
    """Print AI setup instructions and exit."""
    active = provider or os.getenv("AI_PROVIDER", "anthropic")
    key_var = f"{active.upper()}_API_KEY"
    print(
        f"\nLooks like you haven't set up your AI provider yet, my dudes.\n"
        f"\nCurrently configured provider: {active!r}\n"
        f"Missing API key: {key_var}\n"
        f"\nHere's what you need:\n"
        f"\n  Provider (optional, default: anthropic)"
        f"\n    AI_PROVIDER=anthropic | openai | groq | cohere"
        f"\n"
        f"\n  API key for your provider:"
        f"\n    ANTHROPIC_API_KEY=sk-ant-...    → Anthropic (Claude)"
        f"\n    OPENAI_API_KEY=sk-proj-...      → OpenAI (GPT-4o)"
        f"\n    GROQ_API_KEY=gsk_...            → Groq (Llama)"
        f"\n    COHERE_API_KEY=...              → Cohere"
        f"\n"
        f"\n  Optional tuning:"
        f"\n    AI_MODEL=claude-sonnet-4-20250514"
        f"\n    AI_TEMPERATURE=0.7"
        f"\n    AI_MAX_TOKENS=4096"
        f"\n"
        f"\nDrop these in a .env file at the project root and they'll be"
        f"\npicked up automatically.\n",
        file=sys.stderr,
    )
    sys.exit(1)


def handle_prompt_command(args) -> None:
    """Handle the 'prompt' command — AI-powered natural language generation."""
    # ── guard: AI extras installed? ──────────────────────────────────────────
    try:
        from midi_drums.ai.ai_api import DrumGeneratorAI  # noqa: PLC0415
        from midi_drums.ai.backends import AIBackendConfig  # noqa: PLC0415
    except ImportError:
        print(
            "\nAI dependencies are not installed, my dudes.\n"
            "Install them with:\n"
            "  uv sync --group ai\n"
            "  # or: pip install 'midi-drums[ai]'\n",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── guard: env vars configured? ───────────────────────────────────────────
    config = AIBackendConfig.from_env()
    if not config.api_key:
        _print_ai_setup_help(config.provider.value)

    # ── resolve output paths ─────────────────────────────────────────────────
    description = args.text
    save_metadata = getattr(args, "save_metadata", False)
    rpp_path = getattr(args, "rpp", None)

    # Derive a filesystem-safe slug from --output stem or the first 4 prompt words
    if args.output:
        slug = Path(args.output).stem
    else:
        slug = "_".join(description.lower().split()[:4])
        slug = "".join(c if c.isalnum() or c == "_" else "" for c in slug)
        slug = slug or "ai_pattern"

    if save_metadata:
        # Organised layout:  output/<slug>/
        #                    output/<slug>/<slug>.mid
        #                    output/<slug>/metadata.json
        #                    output/<slug>/parts/<N>_<section>.mid   (--song only)
        out_dir = Path("output") / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(out_dir / f"{slug}.mid")
        meta_path: Path | None = out_dir / "metadata.json"
        parts_dir: Path | None = out_dir / "parts"
    else:
        output_path = args.output or f"{slug}.mid"
        meta_path = None
        parts_dir = None

    print(f"Generating from prompt: {description!r}")
    print(f"Provider : {config.provider.value}/{config.model}")
    if save_metadata:
        print(f"Output dir: output/{slug}/")

    ai = DrumGeneratorAI(backend_config=config)

    try:
        if getattr(args, "song", False):
            # ── --song path: Langchain agent composes a multi-section song ──
            print("Composing song via agent…")
            result = ai.compose_with_agent(description)
            print(result.get("output", ""))

            song_cache = result.get("song_cache", {})
            pattern_cache = result.get("pattern_cache", {})

            if song_cache:
                last_id = song_cache[-1]
                success = ai.export_song(last_id, output_path)
                song_obj = ai.get_song_from_agent(last_id)
            elif pattern_cache:
                last_id = pattern_cache[-1]
                success = ai.export_pattern(
                    last_id, output_path, tempo=args.tempo
                )
                song_obj = None
            else:
                print(
                    "Agent didn't create any patterns or songs.",
                    file=sys.stderr,
                )
                sys.exit(1)

            if not success:
                print("MIDI export returned failure.", file=sys.stderr)
                sys.exit(1)

            # ── export per-section parts ─────────────────────────────────────
            if parts_dir is not None and song_obj:
                from midi_drums.engines.midi_engine import MIDIEngine

                parts_dir.mkdir(exist_ok=True)
                engine = MIDIEngine()
                for i, section in enumerate(song_obj.sections):
                    part_file = parts_dir / f"{i:02d}_{section.name}.mid"
                    engine.save_pattern_midi(
                        section.pattern, part_file, tempo=song_obj.tempo
                    )
                print(
                    f"  Parts      : {parts_dir}/"
                    f" ({len(song_obj.sections)} files)"
                )

            # ── optional Reaper project ──────────────────────────────────────
            if rpp_path and song_obj:
                from midi_drums.exporters.reaper_exporter import ReaperExporter

                Path(rpp_path).parent.mkdir(parents=True, exist_ok=True)
                ReaperExporter().export_complete(
                    song_obj, rpp_path, output_path
                )
                print(f"  Reaper     : {rpp_path}")

            # ── optional metadata JSON ───────────────────────────────────────
            if save_metadata:
                import json
                from datetime import datetime

                meta = {
                    "generator": "midi-drums",
                    "created_at": datetime.now().isoformat(),
                    "prompt": description,
                    "provider": f"{config.provider.value}/{config.model}",
                    "song": {
                        "name": song_obj.name if song_obj else None,
                        "tempo": song_obj.tempo if song_obj else args.tempo,
                        "time_signature": (
                            f"{song_obj.time_signature.numerator}/"
                            f"{song_obj.time_signature.denominator}"
                            if song_obj
                            else "4/4"
                        ),
                        "total_bars": (
                            song_obj.total_bars() if song_obj else None
                        ),
                    },
                    "structure": (
                        [
                            {"name": s.name, "bars": s.bars}
                            for s in song_obj.sections
                        ]
                        if song_obj
                        else []
                    ),
                    "agent": {
                        "patterns_generated": result.get("pattern_cache", []),
                        "songs_generated": result.get("song_cache", []),
                        "composition_notes": result.get("output", ""),
                    },
                }
                meta_path.write_text(json.dumps(meta, indent=2))
                print(f"  Metadata   : {meta_path}")

            print(f"\nDone!\n  Output : {output_path}")

        else:
            # ── default path: Pydantic AI → single pattern ───────────────────
            pattern, info = ai.generate_pattern_from_text_sync(
                description=description,
                section=args.section,
                tempo=args.tempo,
                bars=args.bars,
                complexity=args.complexity,
                drummer_style=args.drummer,
            )

            success = ai.export_pattern(pattern, output_path, tempo=args.tempo)
            if not success:
                print("MIDI export returned failure.", file=sys.stderr)
                sys.exit(1)

            chars = info.characteristics

            # ── optional Reaper project ──────────────────────────────────────
            if rpp_path:
                from midi_drums.exporters.reaper_exporter import ReaperExporter
                from midi_drums.models.song import Section, Song, TimeSignature

                Path(rpp_path).parent.mkdir(parents=True, exist_ok=True)
                song_obj = Song(
                    name=slug,
                    tempo=args.tempo,
                    time_signature=TimeSignature(4, 4),
                    sections=[
                        Section(
                            name=args.section, pattern=pattern, bars=args.bars
                        )
                    ],
                    metadata={"genre": chars.genre, "style": chars.style},
                )
                ReaperExporter().export_complete(
                    song_obj, rpp_path, output_path
                )
                print(f"  Reaper     : {rpp_path}")

            # ── optional metadata JSON ───────────────────────────────────────
            if save_metadata:
                import json
                from datetime import datetime

                meta = {
                    "generator": "midi-drums",
                    "created_at": datetime.now().isoformat(),
                    "prompt": description,
                    "provider": f"{config.provider.value}/{config.model}",
                    "song": {
                        "tempo": args.tempo,
                        "time_signature": "4/4",
                        "total_bars": args.bars,
                    },
                    "structure": [{"name": args.section, "bars": args.bars}],
                    "generation": {
                        "genre": chars.genre,
                        "style": chars.style,
                        "complexity": args.complexity,
                        "drummer": args.drummer,
                        "confidence": round(info.confidence, 3),
                    },
                }
                if info.suggestions:
                    meta["generation"]["suggestions"] = info.suggestions
                meta_path.write_text(json.dumps(meta, indent=2))
                print(f"  Metadata   : {meta_path}")

            print("\nDone!")
            print(f"  Output     : {output_path}")
            print(f"  Genre      : {chars.genre} / {chars.style}")
            print(f"  Tempo      : {args.tempo} BPM  |  Bars: {args.bars}")
            print(f"  Confidence : {info.confidence:.0%}")
            if info.suggestions:
                print(f"  Tip        : {info.suggestions[0]}")

    except Exception as e:
        print(f"AI generation failed: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "prompt":
        handle_prompt_command(args)
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
        elif args.reaper_command == "presets":
            handle_reaper_presets_command(args)
        else:
            print(
                "Error: Please specify a reaper subcommand "
                "(export, add-markers, or presets)",
                file=sys.stderr,
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
