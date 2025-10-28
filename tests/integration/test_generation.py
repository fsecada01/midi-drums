#!/usr/bin/env python3
"""Quick test script to verify MIDI generation works correctly."""

import sys
from pathlib import Path

from midi_drums.api.python_api import DrumGeneratorAPI

# Fix Windows console encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")

def test_basic_generation():
    """Test basic MIDI generation across different genres and styles."""
    print("=" * 70)
    print("Testing MIDI Drum Generation")
    print("=" * 70)

    api = DrumGeneratorAPI()
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Test 1: Metal genre with death style
    print("\n[1] Generating Death Metal song (180 BPM, complexity 0.8)...")
    metal_song = api.create_song(
        genre="metal",
        style="death",
        tempo=180,
        complexity=0.8,
        humanization=0.3
    )
    metal_file = output_dir / "test_death_metal.mid"
    api.save_as_midi(metal_song, str(metal_file))
    print(f"✅ Generated: {metal_file}")
    print(f"   Sections: {len(metal_song.sections)}")
    print(f"   Total bars: {sum(s.bars for s in metal_song.sections)}")

    # Test 2: Rock genre with classic style + drummer
    print("\n[2] Generating Classic Rock song with Bonham style (140 BPM)...")
    rock_song = api.create_song(
        genre="rock",
        style="classic",
        tempo=140,
        complexity=0.6,
        drummer="bonham"
    )
    rock_file = output_dir / "test_classic_rock_bonham.mid"
    api.save_as_midi(rock_song, str(rock_file))
    print(f"✅ Generated: {rock_file}")
    print(f"   Sections: {len(rock_song.sections)}")
    print("   Drummer: Bonham (triplets, behind-beat feel)")

    # Test 3: Jazz genre with swing style
    print("\n[3] Generating Jazz Swing song with Weckl style (160 BPM)...")
    jazz_song = api.create_song(
        genre="jazz",
        style="swing",
        tempo=160,
        complexity=0.7,
        drummer="weckl"
    )
    jazz_file = output_dir / "test_jazz_swing_weckl.mid"
    api.save_as_midi(jazz_song, str(jazz_file))
    print(f"✅ Generated: {jazz_file}")
    print(f"   Sections: {len(jazz_song.sections)}")
    print("   Drummer: Weckl (linear, fusion)")

    # Test 4: Funk genre with classic style
    print("\n[4] Generating Classic Funk song with Chambers style (100 BPM)...")
    funk_song = api.create_song(
        genre="funk",
        style="classic",
        tempo=100,
        complexity=0.6,
        drummer="chambers"
    )
    funk_file = output_dir / "test_classic_funk_chambers.mid"
    api.save_as_midi(funk_song, str(funk_file))
    print(f"✅ Generated: {funk_file}")
    print(f"   Sections: {len(funk_song.sections)}")
    print("   Drummer: Chambers (funk mastery, ghost notes)")

    # Test 5: Single pattern generation
    print("\n[5] Generating single breakdown pattern (Metal/Heavy)...")
    pattern = api.generate_pattern(
        genre="metal",
        section="breakdown",
        style="heavy",
        bars=4
    )
    if pattern:
        pattern_file = output_dir / "test_breakdown_pattern.mid"
        api.save_pattern_as_midi(pattern, str(pattern_file), tempo=155)
        print(f"✅ Generated: {pattern_file}")
        print(f"   Beats: {len(pattern.beats)}")
        print(f"   Name: {pattern.name}")

    # Summary
    print("\n" + "=" * 70)
    print("Generation Test Complete!")
    print("=" * 70)
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Files generated: {len(list(output_dir.glob('test_*.mid')))}")
    print("\nYou can now import these MIDI files into:")
    print("  - EZDrummer 3")
    print("  - Any DAW (Logic, Ableton, Reaper, etc.)")
    print("  - MIDI players")
    print("\nAvailable genres:")
    print(f"  {', '.join(api.list_genres())}")
    print("\nAvailable drummers:")
    print(f"  {', '.join(api.list_drummers())}")

if __name__ == "__main__":
    test_basic_generation()
