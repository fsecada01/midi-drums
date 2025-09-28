#!/usr/bin/env python3
"""
Basic usage examples for the MIDI drums system.
Demonstrates the new modular architecture.
"""

from pathlib import Path

from midi_drums.api.python_api import DrumGeneratorAPI


def example_metal_song():
    """Generate a metal song - equivalent to original script."""
    print("🤘 Generating metal song...")

    api = DrumGeneratorAPI()

    # Create a death metal song
    song = api.metal_song(style="heavy", tempo=155, complexity=0.7)

    # Save as MIDI
    output_file = "metal_song_new.mid"
    api.save_as_midi(song, output_file)

    print(f"✅ Generated: {output_file}")
    print(f"📊 Song info: {api.get_song_info(song)}")


def example_pattern_generation():
    """Generate individual patterns."""
    print("🥁 Generating individual patterns...")

    api = DrumGeneratorAPI()

    # Generate different patterns
    patterns = [
        ("metal", "verse", "heavy"),
        ("metal", "chorus", "death"),
        ("metal", "breakdown", "heavy"),
    ]

    for genre, section, style in patterns:
        pattern = api.generate_pattern(genre, section, style)
        if pattern:
            filename = f"{genre}_{style}_{section}.mid"
            api.save_pattern_as_midi(pattern, filename)
            print(f"✅ Generated: {filename} ({len(pattern.beats)} beats)")


def example_system_info():
    """Show available genres and styles."""
    print("📚 System Information:")

    api = DrumGeneratorAPI()

    genres = api.list_genres()
    print(f"Available genres: {genres}")

    for genre in genres:
        styles = api.list_styles(genre)
        print(f"  {genre}: {styles}")

    drummers = api.list_drummers()
    print(f"Available drummers: {drummers}")


def example_batch_generation():
    """Generate multiple songs in batch."""
    print("📁 Batch generation...")

    api = DrumGeneratorAPI()

    # Define multiple song specifications
    songs_specs = [
        {
            "genre": "metal",
            "style": "heavy",
            "tempo": 140,
            "name": "heavy_metal",
        },
        {
            "genre": "metal",
            "style": "death",
            "tempo": 180,
            "name": "death_metal",
        },
        {
            "genre": "metal",
            "style": "power",
            "tempo": 160,
            "name": "power_metal",
        },
    ]

    output_dir = Path("generated_songs")
    generated_files = api.batch_generate(songs_specs, output_dir)

    print(f"✅ Generated {len(generated_files)} songs:")
    for file_path in generated_files:
        print(f"  📁 {file_path}")


def main():
    """Run all examples."""
    print("🎵 MIDI Drums - New Architecture Examples")
    print("=" * 50)

    try:
        example_system_info()
        print()

        example_metal_song()
        print()

        example_pattern_generation()
        print()

        example_batch_generation()
        print()

        print("✅ All examples completed successfully!")

    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
