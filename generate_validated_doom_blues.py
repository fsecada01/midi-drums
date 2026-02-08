"""Generate a physically validated doom blues track using the composite drummer.

This demonstrates the physical feasibility validation system in action.
"""

import logging
from datetime import datetime
from pathlib import Path

from midi_drums.core.engine import DrumGenerator
from midi_drums.models.song import GenerationParameters
from midi_drums.validation.physical_constraints import PhysicalValidator

# Set up logging to see validation messages
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    """Generate validated doom blues track."""
    print("=" * 80)
    print("PHYSICALLY VALIDATED DOOM BLUES TRACK GENERATION")
    print("=" * 80)
    print()
    print("This track uses the composite_doom_blues drummer which combines:")
    print("  - Jason Roeder (Neurosis) - Atmospheric sludge foundation")
    print("  - Jeff Porcaro (Toto) - Blues shuffle and ghost notes")
    print("  - Dennis Chambers (Funk) - Deep pocket and dynamics")
    print()
    print("With NEW physical feasibility validation:")
    print("  [OK] Detects ride + hi-hat conflicts")
    print("  [OK] Automatically resolves conflicts")
    print("  [OK] Ensures all patterns are playable by real drummers")
    print()
    print("-" * 80)

    # Initialize generator and validator
    generator = DrumGenerator()
    validator = PhysicalValidator()

    # Song structure - doom metal meets blues
    structure = [
        ("intro", 4),  # Atmospheric intro
        ("verse", 8),  # Heavy doom verse
        ("verse", 8),  # Build intensity
        ("chorus", 8),  # Explosive chorus
        ("bridge", 4),  # Breakdown/transition
        ("verse", 8),  # Return to heaviness
        ("chorus", 8),  # Final chorus
        ("outro", 4),  # Fade out
    ]

    # Generation parameters
    params = GenerationParameters(
        genre="metal",
        style="doom",
        tempo=80,  # Slow doom tempo
        time_signature=(4, 4),
        complexity=0.7,  # Moderate complexity
        humanization=0.3,  # Natural feel
        drummer="composite_doom_blues",  # Our validated composite drummer!
    )

    print("Generating doom blues track:")
    print(f"  Genre: {params.genre}")
    print(f"  Style: {params.style}")
    print(f"  Tempo: {params.tempo} BPM")
    print(f"  Drummer: {params.drummer}")
    print(f"  Complexity: {params.complexity}")
    print(f"  Humanization: {params.humanization}")
    print()

    # Generate the song
    print("Generating song structure...")
    song = generator.create_song_from_structure(structure, params)

    print(f"[OK] Generated {len(song.sections)} sections")
    print()

    # Validate each section
    print("Validating physical feasibility of all sections...")
    print("-" * 80)

    total_conflicts = 0
    for i, section in enumerate(song.sections, 1):
        conflicts = validator.validate_pattern(section.pattern)
        status = (
            "[OK] VALID"
            if len(conflicts) == 0
            else f"[!!] {len(conflicts)} CONFLICTS"
        )
        print(f"  Section {i:2d} ({section.name:10s}): {status}")
        total_conflicts += len(conflicts)

    print("-" * 80)
    print()

    if total_conflicts == 0:
        print("*** SUCCESS! All sections are physically valid! ***")
        print("    No ride + hi-hat conflicts detected")
        print("    All patterns playable by real drummers")
    else:
        print(f"!!! WARNING: {total_conflicts} conflicts found !!!")
        print("    (This should not happen with the validation enabled)")

    print()

    # Export MIDI
    output_dir = Path("output/validated_doom_blues")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"doom_blues_validated_{timestamp}.mid"

    print("Exporting MIDI file...")
    generator.export_midi(song, str(output_file))

    print(f"[OK] Saved to: {output_file}")
    print()

    # Also export individual sections
    sections_dir = output_dir / "sections"
    sections_dir.mkdir(exist_ok=True)

    print("Exporting individual sections...")
    for i, section in enumerate(song.sections, 1):
        section_file = sections_dir / f"section_{i:02d}_{section.name}.mid"
        generator.export_pattern_midi(
            section.pattern, str(section_file), tempo=params.tempo
        )
        print(f"  [OK] Section {i}: {section_file.name}")

    print()
    print("=" * 80)
    print("GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print(f"Output directory: {output_dir}")
    print(f"Main file: {output_file.name}")
    print(f"Total sections: {len(song.sections)}")
    print(
        f"Total duration: ~{len(song.sections) * 4 * 60 / params.tempo:.1f} seconds at {params.tempo} BPM"
    )
    print()
    print("Load this into EZDrummer 3 to hear the doom metal/blues fusion!")
    print()

    # Print statistics
    stats = validator.get_statistics(song.sections[0].pattern)
    print("Sample Section Statistics:")
    print(f"  Total beats: {stats['total_beats']}")
    print(f"  Conflicts: {stats['total_conflicts']}")
    print(f"  Valid: {'Yes' if stats['is_valid'] else 'No'}")
    print()


if __name__ == "__main__":
    main()
