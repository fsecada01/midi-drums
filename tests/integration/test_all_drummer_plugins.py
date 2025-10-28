#!/usr/bin/env python3
"""
Comprehensive test for all drummer plugins.
Tests plugin loading, style application, and signature fills for all drummers.
"""

from pathlib import Path

from midi_drums import DrumGenerator
from midi_drums.api.python_api import DrumGeneratorAPI


def test_drummer_plugin_loading():
    """Test that all drummer plugins load correctly."""
    print("[TEST] Testing all drummer plugin loading...")

    try:
        generator = DrumGenerator()
        available_drummers = generator.get_available_drummers()

        print(f"Available drummers: {available_drummers}")

        expected_drummers = [
            "bonham",
            "chambers",
            "dee",
            "hoglan",
            "porcaro",
            "roeder",
            "weckl",
        ]

        missing_drummers = [
            d for d in expected_drummers if d not in available_drummers
        ]
        if missing_drummers:
            print(f"[FAIL] Missing drummers: {missing_drummers}")
            return False

        print(f"[PASS] All {len(expected_drummers)} drummer plugins loaded")
        return True

    except Exception as e:
        print(f"[FAIL] Error loading drummer plugins: {e}")
        return False


def test_drummer_style_applications():
    """Test applying each drummer's style to patterns."""
    print("\n[TEST] Testing drummer style applications...")

    drummers = [
        "bonham",
        "chambers",
        "dee",
        "hoglan",
        "porcaro",
        "roeder",
        "weckl",
    ]
    generator = DrumGenerator()

    results = {}

    for drummer in drummers:
        try:
            # Generate base metal pattern for consistency
            base_pattern = generator.generate_pattern(
                "metal", "verse", style="heavy"
            )
            if not base_pattern:
                print(f"[FAIL] Failed to generate base pattern for {drummer}")
                results[drummer] = False
                continue

            base_beats = len(base_pattern.beats)

            # Apply drummer style
            styled_pattern = generator.apply_drummer_style(
                base_pattern, drummer
            )
            if not styled_pattern:
                print(f"[FAIL] Failed to apply {drummer} style")
                results[drummer] = False
                continue

            styled_beats = len(styled_pattern.beats)

            print(f"  {drummer.capitalize()}: {base_beats} -> {styled_beats}")
            results[drummer] = True

        except Exception as e:
            print(f"[FAIL] Error testing {drummer}: {e}")
            results[drummer] = False

    passed = sum(results.values())
    total = len(results)

    if passed == total:
        print(f"[PASS] All {total} drummer styles applied successfully")
        return True
    else:
        print(f"[PARTIAL] {passed}/{total} drummer styles worked")
        return False


def test_drummer_signature_fills():
    """Test signature fills for each drummer."""
    print("\n[TEST] Testing drummer signature fills...")

    drummers = [
        "bonham",
        "chambers",
        "dee",
        "hoglan",
        "porcaro",
        "roeder",
        "weckl",
    ]

    results = {}

    for drummer in drummers:
        try:
            # Import the specific drummer plugin to test fills directly
            if drummer == "bonham":
                from midi_drums.plugins.drummers.bonham import BonhamPlugin

                plugin = BonhamPlugin()
            elif drummer == "chambers":
                from midi_drums.plugins.drummers.chambers import ChambersPlugin

                plugin = ChambersPlugin()
            elif drummer == "dee":
                from midi_drums.plugins.drummers.dee import DeePlugin

                plugin = DeePlugin()
            elif drummer == "hoglan":
                from midi_drums.plugins.drummers.hoglan import HoglanPlugin

                plugin = HoglanPlugin()
            elif drummer == "porcaro":
                from midi_drums.plugins.drummers.porcaro import PorcaroPlugin

                plugin = PorcaroPlugin()
            elif drummer == "roeder":
                from midi_drums.plugins.drummers.roeder import RoederPlugin

                plugin = RoederPlugin()
            elif drummer == "weckl":
                from midi_drums.plugins.drummers.weckl import WecklPlugin

                plugin = WecklPlugin()
            else:
                print(f"[FAIL] Unknown drummer: {drummer}")
                results[drummer] = False
                continue

            fills = plugin.get_signature_fills()
            fill_count = len(fills)

            if fill_count > 0:
                print(f"  {drummer.capitalize()}: {fill_count} signature fills")

                # Test that fills have patterns
                for i, fill in enumerate(fills):
                    beats = len(fill.pattern.beats)
                    print(
                        f"    Fill {i+1}: {beats} beats, "
                        f"prob={fill.trigger_probability}"
                    )

                results[drummer] = True
            else:
                print(f"[FAIL] {drummer} has no signature fills")
                results[drummer] = False

        except Exception as e:
            print(f"[FAIL] Error testing {drummer} fills: {e}")
            results[drummer] = False

    passed = sum(results.values())
    total = len(results)

    if passed == total:
        print(f"[PASS] All {total} drummer signature fills loaded")
        return True
    else:
        print(f"[PARTIAL] {passed}/{total} drummer fills worked")
        return False


def test_drummer_song_generation():
    """Test generating complete songs with each drummer."""
    print("\n[TEST] Testing complete song generation with drummers...")

    api = DrumGeneratorAPI()
    test_drummers = ["bonham", "porcaro", "weckl", "chambers"]  # Sample test

    results = {}

    for drummer in test_drummers:
        try:
            # Generate song with drummer style (use metal genre)
            song = api.create_song(
                genre="metal",
                style="heavy",
                tempo=140,
                drummer=drummer,
                name=f"Test_Song_{drummer.capitalize()}",
            )

            if song and len(song.sections) > 0:
                total_beats = sum(
                    len(section.pattern.beats) for section in song.sections
                )
                print(
                    f"  {drummer.capitalize()}: {len(song.sections)} sections, "
                    f"{total_beats} total beats"
                )

                # Try to export
                output_path = Path(f"test_{drummer}_song.mid")
                api.save_as_midi(song, output_path)

                if output_path.exists():
                    file_size = output_path.stat().st_size
                    print(f"    Exported: {file_size} bytes")
                    results[drummer] = True
                    # Clean up test files
                    output_path.unlink()
                else:
                    print(f"[FAIL] Failed to export {drummer} song")
                    results[drummer] = False
            else:
                print(f"[FAIL] Failed to generate song with {drummer}")
                results[drummer] = False

        except Exception as e:
            print(f"[FAIL] Error generating song with {drummer}: {e}")
            results[drummer] = False

    passed = sum(results.values())
    total = len(results)

    if passed == total:
        print(f"[PASS] All {total} drummer songs generated successfully")
        return True
    else:
        print(f"[PARTIAL] {passed}/{total} drummer songs worked")
        return False


def test_drummer_genre_compatibility():
    """Test drummer-genre compatibility."""
    print("\n[TEST] Testing drummer-genre compatibility...")

    # Test only with available genres (only metal plugin exists)
    compatibility_tests = [
        ("bonham", ["metal"]),
        ("porcaro", ["metal"]),
        ("weckl", ["metal"]),
        ("chambers", ["metal"]),
        ("hoglan", ["metal"]),
        ("roeder", ["metal"]),
        ("dee", ["metal"]),
    ]

    generator = DrumGenerator()
    results = {}

    for drummer, genres in compatibility_tests:
        try:
            # Test each compatible genre
            compatible_count = 0
            for genre in genres:
                # Generate pattern and apply drummer style
                pattern = generator.generate_pattern(
                    genre, "verse", style="heavy"
                )
                if pattern:
                    styled = generator.apply_drummer_style(pattern, drummer)
                    if styled and len(styled.beats) > 0:
                        compatible_count += 1

            print(
                f"  {drummer.capitalize()}: {compatible_count}/"
                f"{len(genres)} genres compatible"
            )
            results[drummer] = compatible_count == len(genres)

        except Exception as e:
            print(f"[FAIL] Error testing {drummer} compatibility: {e}")
            results[drummer] = False

    passed = sum(results.values())
    total = len(results)

    if passed == total:
        print(f"[PASS] All {total} drummers have proper genre compatibility")
        return True
    else:
        print(f"[PARTIAL] {passed}/{total} drummer compatibility tests passed")
        return False


def main():
    """Run all drummer plugin tests."""
    print("=" * 70)
    print("Comprehensive Drummer Plugin Test Suite")
    print("Testing: Bonham, Porcaro, Weckl, Roeder, Dee, Chambers, Hoglan")
    print("=" * 70)

    tests = [
        test_drummer_plugin_loading,
        test_drummer_style_applications,
        test_drummer_signature_fills,
        test_drummer_song_generation,
        test_drummer_genre_compatibility,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"[FAIL] Test failed with exception: {e}")

    print("\n" + "=" * 70)
    print(f"Test Results: {passed}/{total} test suites passed")

    if passed == total:
        print("[SUCCESS] All drummer plugin tests passed!")
        print("\nAvailable drummers:")
        print("- John Bonham (Led Zeppelin) - Rock/Hard Rock")
        print("- Jeff Porcaro (Toto) - Pop/Rock/Studio")
        print("- Dave Weckl - Jazz Fusion")
        print("- Jason Roeder (Neurosis) - Sludge/Post-Metal")
        print("- Mikkey Dee (Motörhead) - Speed Metal/Punk")
        print("- Dennis Chambers (P-Funk) - Funk/Jazz/R&B")
        print("- Gene Hoglan - Death Metal/Technical")
    else:
        print("[WARNING] Some drummer tests failed. Check output above.")

    print("=" * 70)


if __name__ == "__main__":
    main()
