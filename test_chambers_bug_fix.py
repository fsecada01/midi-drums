"""Test script to verify Chambers drummer bug fix.

This reproduces the original error from epic_complex_death_metal_song:
- bridge section with progressive style
- chambers drummer
- Empty pattern causing "pop from empty list" error
"""

import logging
import sys

from midi_drums.core.engine import DrumGenerator

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Enable logging to see warnings
logging.basicConfig(level=logging.WARNING)


def test_chambers_progressive_bridge():
    """Test the exact scenario that failed: chambers + progressive + bridge."""
    print("Testing Chambers drummer with progressive bridge pattern...")

    generator = DrumGenerator()

    # Generate bridge section (this is where it failed with empty pattern)
    try:
        # Generate pattern with chambers drummer applied
        pattern = generator.generate_pattern(
            genre="metal",
            section="bridge",
            style="progressive",
            bars=6,
            drummer="chambers",
        )

        if pattern is None:
            print("❌ Pattern generation returned None")
            return False

        print(
            f"✅ Pattern generated: {pattern.name}, {len(pattern.beats)} beats"
        )

        if len(pattern.beats) == 0:
            print("❌ Pattern has no beats (empty pattern bug)")
            return False

        print("✅ Pattern has beats (bug is fixed!)")
        return True

    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_full_song_generation():
    """Test full song generation with chambers in progressive sections."""
    print("\nTesting full song with chambers drummer...")

    generator = DrumGenerator()

    # Recreate failing song structure
    structure = [
        ("intro", 4),
        ("verse", 8),
        ("chorus", 8),
        ("bridge", 6),  # This section failed with chambers
    ]

    try:
        song = generator.create_song(
            genre="metal",
            style="progressive",
            tempo=160,
            structure=structure,
            complexity=0.9,
            humanization=0.4,
            drummer="chambers",
        )

        print(f"✅ Song generated: {len(song.sections)} sections")

        # Check all sections have beats
        empty_sections = [
            s.name for s in song.sections if len(s.pattern.beats) == 0
        ]
        if empty_sections:
            print(f"❌ Empty sections found: {empty_sections}")
            return False

        print("✅ All sections have beats")
        return True

    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Chambers Drummer Bug Fix Verification")
    print("=" * 60)

    test1 = test_chambers_progressive_bridge()
    test2 = test_full_song_generation()

    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"  Bridge pattern test: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Full song test:      {'✅ PASS' if test2 else '❌ FAIL'}")
    print("=" * 60)

    if test1 and test2:
        print("\n🎉 All tests passed! Bug is fixed.")
    else:
        print("\n⚠️  Some tests failed. Bug may still exist.")
