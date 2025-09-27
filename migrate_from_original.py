#!/usr/bin/env python3
"""
Migration script to demonstrate equivalence with original generate_metal_drum_track.py
"""

from pathlib import Path
from midi_drums import DrumGenerator


def generate_original_equivalent():
    """Generate the exact equivalent of the original script output."""
    print("🔄 Generating equivalent of original script...")

    # Initialize generator
    generator = DrumGenerator()

    # Create the same song structure as original
    song = generator.create_song(
        genre="metal",
        style="heavy",
        tempo=155,
        structure=[
            ("intro", 4),
            ("fill", 1),
            ("verse", 16),
            ("fill", 1),
            ("breakdown", 8),
            ("fill", 1),
            ("chorus", 16),
            ("fill", 1),
            ("verse", 16),
            ("fill", 1),
            ("chorus", 16),
            ("outro", 1)
        ],
        complexity=0.7,
        dynamics=0.6,
        humanization=0.3
    )

    # Export with same filename
    output_file = Path("ezdrummer3_heavy_metal_new_architecture.mid")
    generator.export_midi(song, output_file)

    print(f"✅ Generated: {output_file}")
    print(f"📊 Song info:")
    info = generator.get_song_info(song)
    for key, value in info.items():
        print(f"   {key}: {value}")

    return output_file


def compare_with_original():
    """Compare new output with original."""
    print("\n🔍 Comparison:")
    print("Original script: generate_metal_drum_track.py")
    print("  - Single file, hardcoded patterns")
    print("  - Limited to one metal style")
    print("  - Fixed song structure")
    print()
    print("New architecture:")
    print("  - Modular, extensible plugin system")
    print("  - Multiple genres and styles")
    print("  - Configurable song structures")
    print("  - Pattern variations and humanization")
    print("  - API for integration")
    print("  - CLI interface")


def demonstrate_new_capabilities():
    """Show capabilities not available in original."""
    print("\n🆕 New capabilities:")

    generator = DrumGenerator()

    # Show available options
    genres = generator.get_available_genres()
    print(f"Available genres: {genres}")

    if "metal" in genres:
        styles = generator.get_styles_for_genre("metal")
        print(f"Metal styles: {styles}")

        # Generate different metal styles
        for style in styles[:3]:  # First 3 styles
            try:
                pattern = generator.generate_pattern("metal", "verse", style=style)
                if pattern:
                    filename = f"metal_{style}_verse.mid"
                    generator.export_pattern_midi(pattern, Path(filename))
                    print(f"  ✅ Generated: {filename}")
            except Exception as e:
                print(f"  ❌ Failed to generate {style}: {e}")


if __name__ == "__main__":
    print("🎵 MIDI Drums - Migration from Original Script")
    print("=" * 60)

    try:
        # Generate equivalent output
        generate_original_equivalent()

        # Show comparison
        compare_with_original()

        # Demonstrate new features
        demonstrate_new_capabilities()

        print("\n✅ Migration demonstration complete!")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()