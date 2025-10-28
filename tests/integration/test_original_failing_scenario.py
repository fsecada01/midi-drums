"""Test exact scenario from epic_complex_death_metal_song that failed.

From project_metadata.json:
- Section 05: bridge_progressive_chambers @ 160bpm - FAILED: "pop from empty list"
- Stem: chambers_compilation - FAILED: "pop from empty list"
"""

import sys

from midi_drums.core.engine import DrumGenerator

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def test_exact_failing_section():
    """Test the exact section that failed: bridge/progressive/chambers/160bpm."""
    print(
        "Testing exact failing scenario from epic_complex_death_metal_song..."
    )
    print("  Section: bridge")
    print("  Style: progressive")
    print("  Drummer: chambers")
    print("  Tempo: 160 BPM")
    print("  Bars: 6")
    print()

    generator = DrumGenerator()

    try:
        # This exact call was failing with "pop from empty list"
        pattern = generator.generate_pattern(
            genre="metal",
            section="bridge",
            style="progressive",
            bars=6,
            drummer="chambers",
        )

        if pattern is None:
            print("❌ FAIL: Pattern generation returned None")
            return False

        if len(pattern.beats) == 0:
            print("❌ FAIL: Pattern has no beats (empty pattern)")
            return False

        print(f"✅ SUCCESS: Pattern generated with {len(pattern.beats)} beats")
        print(f"   Pattern name: {pattern.name}")
        print(f"   Duration: {pattern.duration_bars()} bars")
        return True

    except IndexError as e:
        if "pop from empty list" in str(e):
            print(f"❌ FAIL: Original bug still exists - {e}")
        else:
            print(f"❌ FAIL: Different IndexError - {e}")
        import traceback

        traceback.print_exc()
        return False

    except Exception as e:
        print(f"❌ FAIL: Unexpected error - {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Original Failing Scenario Test")
    print("=" * 70)
    print()

    success = test_exact_failing_section()

    print()
    print("=" * 70)
    if success:
        print("🎉 BUG FIXED! The original failing scenario now works.")
    else:
        print("⚠️  BUG STILL EXISTS! The scenario is still failing.")
    print("=" * 70)
