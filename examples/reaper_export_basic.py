#!/usr/bin/env python3
"""Basic example: Export MIDI drums to Reaper with markers."""

from midi_drums import DrumGenerator
from midi_drums.exporters import ReaperExporter


def main():
    print("=" * 70)
    print("REAPER EXPORT - BASIC EXAMPLE")
    print("=" * 70)

    # 1. Generate MIDI drum track
    print("\n1. Generating doom metal drum track...")
    generator = DrumGenerator()

    song = generator.create_song(
        genre="metal",
        style="doom",
        tempo=120,
        structure=[
            ("intro", 4),
            ("verse", 8),
            ("chorus", 8),
            ("verse", 8),
            ("chorus", 8),
            ("bridge", 4),
            ("chorus", 8),
            ("outro", 4),
        ],
        complexity=0.7,
        humanization=0.3,
    )

    print(f"   Generated {len(song.sections)} sections")
    print(f"   Total bars: {sum(s.bars for s in song.sections)}")
    print(f"   Tempo: {song.tempo} BPM")

    # 2. Export to Reaper project with markers
    print("\n2. Exporting to Reaper project...")
    exporter = ReaperExporter()

    exporter.export_with_markers(
        song=song, output_rpp="output/doom_metal_basic.rpp"
    )

    print("   [OK] Created doom_metal_basic.rpp with section markers")

    # 3. Also export MIDI file separately
    print("\n3. Exporting MIDI file...")
    exporter.export_with_midi(
        song=song,
        output_rpp="output/doom_metal_with_midi.rpp",
        output_midi="output/doom_metal_drums.mid",
    )

    print("   [OK] Created doom_metal_with_midi.rpp")
    print("   [OK] Created doom_metal_drums.mid")

    print("\n" + "=" * 70)
    print("EXPORT COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Open doom_metal_basic.rpp in Reaper")
    print("2. Verify markers appear at correct positions")
    print("3. Import doom_metal_drums.mid to a track")
    print("4. Add EZDrummer 3 to the track")
    print("5. Play and enjoy!")


if __name__ == "__main__":
    import os

    os.makedirs("output", exist_ok=True)
    main()
