"""
Generate doom metal/blues song with ENHANCED humanization.

This version uses the new AdvancedHumanizer for professional-grade realism:
- Gaussian timing distribution (not uniform)
- Instrument-specific timing characteristics
- Context-aware velocity curves
- Micro-timing relationships (kick+snare flams)
- Subtle fatigue modeling

Outputs:
1. Metadata JSON with song structure and parameters
2. Single unified MIDI track for DAW import
3. Individual section MIDI files for granular control
"""

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from midi_drums.api.python_api import DrumGeneratorAPI
from midi_drums.humanization import AdvancedHumanizer


def create_output_directory(base_name: str) -> Path:
    """Create date-stamped output directory (overwrites if exists)."""
    date_stamp = datetime.now().strftime("%Y%m%d")
    output_dir = Path(f"output/{base_name}_{date_stamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def generate_metadata(song, output_dir: Path, humanization_info: dict) -> dict:
    """Generate comprehensive metadata JSON."""
    metadata = {
        "song": {
            "name": song.name,
            "tempo": song.tempo,
            "time_signature": f"{song.time_signature.numerator}/{song.time_signature.denominator}",
            "total_bars": sum(s.bars for s in song.sections),
            "duration_seconds": (
                sum(s.bars for s in song.sections) * 4 / song.tempo
            )
            * 60,
            "genre": "metal",
            "style": "doom",
            "description": "Doom metal with blues influences (Crowbar/Sleep inspired)",
        },
        "humanization": humanization_info,
        "structure": [
            {
                "section_number": i + 1,
                "name": section.name,
                "bars": section.bars,
                "pattern_name": section.pattern.name,
                "beats_in_pattern": len(section.pattern.beats),
            }
            for i, section in enumerate(song.sections)
        ],
        "generation": {
            "timestamp": datetime.now().isoformat(),
            "generator": "MIDI Drums Generator v1.0 + Advanced Humanization",
            "parameters": {
                "complexity": (
                    song.global_parameters.complexity
                    if song.global_parameters
                    else 0.7
                ),
                "humanization": "advanced (Gaussian timing, context-aware velocity)",
            },
        },
        "files": {
            "full_song": f"{song.name}_complete.mid",
            "sections": [
                f"{song.name}_section_{i+1:02d}_{section.name}.mid"
                for i, section in enumerate(song.sections)
            ],
        },
    }

    # Save metadata
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.success(f"Metadata saved: {metadata_file}")
    return metadata


def export_individual_sections(api, song, output_dir: Path):
    """Export each song section as individual MIDI file."""
    logger.info("\\nExporting individual sections...")

    section_dir = output_dir / "sections"
    section_dir.mkdir(exist_ok=True)

    for i, section in enumerate(song.sections):
        section_filename = f"{song.name}_section_{i+1:02d}_{section.name}.mid"
        section_path = section_dir / section_filename

        # Create a temporary song with just this section
        from midi_drums.models.song import Song

        single_section_song = Song(
            name=f"{section.name}_{i+1}",
            tempo=song.tempo,
            sections=[section],
            time_signature=song.time_signature,
            global_parameters=song.global_parameters,
        )

        api.save_as_midi(single_section_song, str(section_path))
        logger.info(f"  [{i+1}/{len(song.sections)}] {section_filename}")

    logger.success(
        f"Exported {len(song.sections)} section files to {section_dir}"
    )


def main():
    """Generate complete doom metal/blues song with enhanced humanization."""
    logger.info("=" * 70)
    logger.info("Enhanced Doom Metal/Blues Song Generator")
    logger.info("=" * 70)

    # Create output directory
    output_dir = create_output_directory("doom_blues_enhanced")
    logger.info(f"Output directory: {output_dir}")

    # Initialize API
    api = DrumGeneratorAPI()

    # Define song structure
    structure = [
        ("intro", 4),  # Atmospheric intro
        ("verse", 8),  # Main heavy riff
        ("verse", 8),  # Repeat
        ("chorus", 8),  # Heavier section
        ("verse", 8),  # Back to main riff
        ("bridge", 4),  # Breakdown
        ("chorus", 8),  # Heavy chorus
        ("outro", 8),  # Fade out
    ]

    total_bars = sum(bars for _, bars in structure)
    duration_seconds = (total_bars * 4 / 70) * 60
    duration_minutes = duration_seconds / 60

    logger.info("\\nSong Structure:")
    for i, (section_name, bars) in enumerate(structure, 1):
        logger.info(f"  {i}. {section_name:8s} - {bars:2d} bars")
    logger.info(f"\\nTotal: {total_bars} bars, ~{duration_minutes:.1f} minutes")

    # Generate base song WITHOUT basic humanization (we'll apply advanced humanization)
    logger.info("\\nGenerating base doom metal song...")
    logger.info("  Style: Doom metal (slow and heavy)")
    logger.info("  Tempo: 70 BPM")
    logger.info("  Humanization: DISABLED (will apply advanced humanization)")

    song = api.create_song(
        genre="metal",
        style="doom",
        tempo=70,
        structure=structure,
        complexity=0.7,
        humanization=0.0,  # Disable basic humanization
        name="doom_blues_enhanced",
    )

    logger.success(
        f"Base song generated: {len(song.sections)} sections, {sum(s.bars for s in song.sections)} bars"
    )

    # Apply ADVANCED HUMANIZATION to each section
    logger.info("\\n" + "=" * 70)
    logger.info("Applying Advanced Humanization")
    logger.info("=" * 70)

    humanizer = AdvancedHumanizer(
        tempo=70,
        style="loose",  # Doom metal = loose, heavy feel
        humanization_amount=0.7,  # Moderate-strong humanization
    )

    logger.info("\\nHumanization Settings:")
    logger.info("  Tempo: 70 BPM")
    logger.info("  Style: loose (live energy, doom metal appropriate)")
    logger.info("  Amount: 0.7 (moderate-strong)")
    logger.info("\\nFeatures:")
    logger.info("  ✓ Gaussian timing distribution (not uniform)")
    logger.info("  ✓ Instrument-specific timing (kick leads, crashes lag)")
    logger.info("  ✓ Context-aware velocity (chorus louder, intro softer)")
    logger.info("  ✓ Micro-timing flams (kick+snare natural offset)")
    logger.info("  ✓ Subtle fatigue modeling (long sections)")

    for i, section in enumerate(song.sections):
        # Determine section type from name (intro_1 -> intro)
        section_name_parts = section.name.split("_")
        section_type = section_name_parts[0] if section_name_parts else "verse"

        logger.info(
            f"\\n  Humanizing section {i+1}/{len(song.sections)}: {section.name} (type: {section_type})"
        )

        # Apply advanced humanization
        original_beat_count = len(section.pattern.beats)
        section.pattern = humanizer.humanize_pattern(
            section.pattern, section_type=section_type
        )

        # Verify no beats were lost
        if len(section.pattern.beats) != original_beat_count:
            logger.warning(
                f"    Beat count changed: {original_beat_count} -> {len(section.pattern.beats)}"
            )
        else:
            logger.success(f"    Humanized {len(section.pattern.beats)} beats")

    logger.success("All sections humanized successfully!")

    # Generate metadata
    logger.info("\\nGenerating metadata...")
    humanization_info = {
        "engine": "AdvancedHumanizer",
        "version": "1.0",
        "tempo": 70,
        "style": "loose",
        "amount": 0.7,
        "features": [
            "Gaussian timing distribution",
            "Instrument-specific timing characteristics",
            "Context-aware velocity curves",
            "Micro-timing relationships (flams)",
            "Subtle fatigue modeling",
        ],
        "timing_characteristics": {
            "kick": "leads by ~2ms (drives rhythm)",
            "snare": "reference timing",
            "hi_hat": "metronomic (tightest)",
            "ride": "behind by ~1ms",
            "crash": "behind by ~2ms (heavy cymbals)",
        },
        "velocity_ranges": {
            "ghost_notes": "25-45",
            "normal_hits": "65-90",
            "accents": "95-115",
            "maximum": "115-127",
        },
    }

    metadata = generate_metadata(song, output_dir, humanization_info)

    # Export full song
    logger.info("\\nExporting complete song...")
    full_song_path = output_dir / f"{song.name}_complete.mid"
    api.save_as_midi(song, str(full_song_path))
    logger.success(f"Complete song: {full_song_path}")

    # Export individual sections
    export_individual_sections(api, song, output_dir)

    # Final summary
    logger.info("\\n" + "=" * 70)
    logger.success("Generation Complete!")
    logger.info("=" * 70)

    logger.info(f"\\nOutput Directory: {output_dir}")
    logger.info("\\nGenerated Files:")
    logger.info(
        "  1. metadata.json - Complete song information + humanization details"
    )
    logger.info(
        f"  2. {song.name}_complete.mid - Full unified track (ENHANCED)"
    )
    logger.info(
        f"  3. sections/ - {len(song.sections)} individual section files"
    )

    logger.info("\\nSong Details:")
    logger.info("  Tempo: 70 BPM")
    logger.info(f"  Duration: ~{duration_minutes:.1f} minutes")
    logger.info(f"  Total bars: {total_bars}")
    logger.info(f"  Sections: {len(song.sections)}")
    logger.info("  Humanization: ADVANCED (Gaussian, context-aware)")

    logger.info("\\nHumanization Improvements vs Original:")
    logger.info(
        "  ✓ Timing: Gaussian distribution (natural) vs uniform (robotic)"
    )
    logger.info("  ✓ Velocity: Context-aware (chorus louder) vs fixed ranges")
    logger.info("  ✓ Micro-timing: Kick+snare flams vs simultaneous")
    logger.info("  ✓ Instrument timing: Characteristic offsets vs generic")
    logger.info("  ✓ Fatigue: Subtle velocity reduction vs constant energy")

    logger.info("\\nUsage:")
    logger.info(
        "  1. Load the complete MIDI file into REAPER/DAW with EZDrummer 3"
    )
    logger.info(
        "  2. Compare with original generate_complete_doom_blues.py output"
    )
    logger.info("  3. Notice improved realism and natural feel")
    logger.info("  4. Use individual section files for fine-tuned editing")
    logger.info(
        "  5. Check metadata.json for complete humanization documentation"
    )

    return output_dir


if __name__ == "__main__":
    output = main()
    print(f"\\n\\nAll files saved to: {output.absolute()}")
