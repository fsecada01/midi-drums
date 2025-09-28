#!/usr/bin/env python3
"""
Test script for Gene Hoglan drummer plugin.
Tests plugin loading, pattern generation, and style application.
"""

from pathlib import Path

from midi_drums import DrumGenerator
from midi_drums.api.python_api import DrumGeneratorAPI


def test_hoglan_plugin_loading():
    """Test that Gene Hoglan plugin loads correctly."""
    print("[TEST] Testing Gene Hoglan plugin loading...")

    try:
        generator = DrumGenerator()
        available_drummers = generator.get_available_drummers()

        print(f"Available drummers: {available_drummers}")

        if "hoglan" in available_drummers:
            print("[PASS] Gene Hoglan plugin loaded successfully")
            return True
        else:
            print("[FAIL] Gene Hoglan plugin not found in available drummers")
            return False

    except Exception as e:
        print(f"[FAIL] Error loading drummer plugins: {e}")
        return False


def test_hoglan_style_application():
    """Test applying Hoglan style to metal patterns."""
    print("\n[TEST] Testing Hoglan style application...")

    try:
        generator = DrumGenerator()

        # Generate base metal pattern
        base_pattern = generator.generate_pattern(
            "metal", "verse", style="death"
        )
        if not base_pattern:
            print("[FAIL] Failed to generate base metal pattern")
            return False

        print(
            f"Base pattern: {base_pattern.name} with "
            f"{len(base_pattern.beats)} beats"
        )

        # Apply Hoglan style
        hoglan_pattern = generator.apply_drummer_style(base_pattern, "hoglan")
        if not hoglan_pattern:
            print("[FAIL] Failed to apply Hoglan style")
            return False

        print(
            f"Hoglan pattern: {hoglan_pattern.name} with "
            f"{len(hoglan_pattern.beats)} beats"
        )

        # Should have more beats due to double bass and complexity
        if len(hoglan_pattern.beats) >= len(base_pattern.beats):
            print("[PASS] Hoglan style added complexity (more beats)")
        else:
            print("[WARN] Hoglan style didn't increase beat count as expected")

        return True

    except Exception as e:
        print(f"[FAIL] Error applying Hoglan style: {e}")
        return False


def test_hoglan_song_generation():
    """Test generating complete song with Hoglan style."""
    print("\n[TEST] Testing complete Hoglan song generation...")

    try:
        api = DrumGeneratorAPI()

        # Generate death metal song with Hoglan style
        song = api.create_song(
            genre="metal",
            style="death",
            tempo=180,
            complexity=0.8,
            drummer="hoglan",
            name="Death_Metal_Hoglan_Test",
        )

        if not song:
            print("[FAIL] Failed to generate song with Hoglan style")
            return False

        print(f"Generated song: {song.name}")
        print(f"Sections: {len(song.sections)}")

        for section in song.sections:
            print(f"  - {section.name}: {len(section.pattern.beats)} beats")

        # Export test MIDI
        output_path = Path("hoglan_test_song.mid")
        api.save_as_midi(song, output_path)

        if output_path.exists():
            print(f"[PASS] Exported Hoglan test song to {output_path}")
            print(f"File size: {output_path.stat().st_size} bytes")
        else:
            print("[FAIL] Failed to export MIDI file")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] Error generating Hoglan song: {e}")
        return False


def test_hoglan_signature_fills():
    """Test Gene Hoglan's signature fill patterns."""
    print("\n[TEST] Testing Hoglan signature fills...")

    try:
        from midi_drums.plugins.drummers.hoglan import HoglanPlugin

        plugin = HoglanPlugin()
        fills = plugin.get_signature_fills()

        print(f"Hoglan signature fills: {len(fills)}")

        for i, fill in enumerate(fills):
            print(f"  - Fill {i+1}: {fill.pattern.name}")
            print(f"    Trigger probability: {fill.trigger_probability}")
            print(f"    Position: {fill.section_position}")
            print(f"    Beats: {len(fill.pattern.beats)}")

        if len(fills) > 0:
            print("[PASS] Hoglan signature fills loaded successfully")

            # Test exporting a signature fill
            api = DrumGeneratorAPI()
            first_fill = fills[0]
            api.save_pattern_as_midi(
                first_fill.pattern, Path("hoglan_signature_fill.mid"), tempo=160
            )

            print("[PASS] Exported signature fill as MIDI")
            return True
        else:
            print("[FAIL] No signature fills found")
            return False

    except Exception as e:
        print(f"[FAIL] Error testing signature fills: {e}")
        return False


def main():
    """Run all Gene Hoglan plugin tests."""
    print("=" * 60)
    print("Gene Hoglan 'The Atomic Clock' Drummer Plugin Test")
    print("=" * 60)

    tests = [
        test_hoglan_plugin_loading,
        test_hoglan_style_application,
        test_hoglan_song_generation,
        test_hoglan_signature_fills,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"[FAIL] Test failed with exception: {e}")

    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All Gene Hoglan plugin tests passed!")
    else:
        print("[WARNING] Some tests failed. Check output above.")

    print("=" * 60)


if __name__ == "__main__":
    main()
