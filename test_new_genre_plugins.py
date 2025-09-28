#!/usr/bin/env python3
"""
Comprehensive test for all new genre plugins.
Tests plugin loading, pattern generation, and drummer compatibility for
rock, jazz, and funk.
"""

from pathlib import Path

from midi_drums import DrumGenerator
from midi_drums.api.python_api import DrumGeneratorAPI


def test_genre_plugin_loading():
    """Test that all genre plugins load correctly."""
    print("[TEST] Testing all genre plugin loading...")

    try:
        generator = DrumGenerator()
        available_genres = generator.get_available_genres()

        print(f"Available genres: {sorted(available_genres)}")

        expected_genres = ["metal", "rock", "jazz", "funk"]
        missing_genres = [
            g for g in expected_genres if g not in available_genres
        ]

        if missing_genres:
            print(f"[FAIL] Missing genres: {missing_genres}")
            return False

        print(f"[PASS] All {len(expected_genres)} genre plugins loaded")
        return True

    except Exception as e:
        print(f"[FAIL] Error loading genre plugins: {e}")
        return False


def test_genre_style_support():
    """Test each genre's style support."""
    print("\n[TEST] Testing genre style support...")

    generator = DrumGenerator()

    expected_styles = {
        "metal": [
            "heavy",
            "death",
            "power",
            "progressive",
            "thrash",
            "doom",
            "breakdown",
        ],
        "rock": [
            "classic",
            "blues",
            "alternative",
            "progressive",
            "punk",
            "hard",
            "pop",
        ],
        "jazz": [
            "swing",
            "bebop",
            "fusion",
            "latin",
            "ballad",
            "hard_bop",
            "contemporary",
        ],
        "funk": [
            "classic",
            "pfunk",
            "shuffle",
            "new_orleans",
            "fusion",
            "minimal",
            "heavy",
        ],
    }

    results = {}

    for genre, expected in expected_styles.items():
        try:
            available_styles = generator.get_styles_for_genre(genre)
            print(f"  {genre.capitalize()}: {len(available_styles)} styles")

            missing_styles = [s for s in expected if s not in available_styles]
            if missing_styles:
                print(f"    Missing: {missing_styles}")
                results[genre] = False
            else:
                print(f"    All styles present: {available_styles}")
                results[genre] = True

        except Exception as e:
            print(f"[FAIL] Error testing {genre} styles: {e}")
            results[genre] = False

    passed = sum(results.values())
    total = len(results)

    if passed == total:
        print(f"[PASS] All {total} genres have correct style support")
        return True
    else:
        print(f"[PARTIAL] {passed}/{total} genre style tests passed")
        return False


def test_pattern_generation():
    """Test pattern generation for each genre and style."""
    print("\n[TEST] Testing pattern generation...")

    generator = DrumGenerator()

    test_cases = [
        ("rock", "classic", "verse"),
        ("rock", "blues", "chorus"),
        ("jazz", "swing", "verse"),
        ("jazz", "bebop", "bridge"),
        ("funk", "classic", "verse"),
        ("funk", "pfunk", "breakdown"),
        ("metal", "heavy", "verse"),  # Existing control
    ]

    results = {}

    for genre, style, section in test_cases:
        try:
            pattern = generator.generate_pattern(genre, section, style=style)
            if pattern and len(pattern.beats) > 0:
                beat_count = len(pattern.beats)
                print(f"  {genre}/{style}/{section}: {beat_count} beats ✓")
                results[f"{genre}_{style}_{section}"] = True
            else:
                print(f"  {genre}/{style}/{section}: No pattern generated ✗")
                results[f"{genre}_{style}_{section}"] = False

        except Exception as e:
            print(f"  {genre}/{style}/{section}: Error - {e} ✗")
            results[f"{genre}_{style}_{section}"] = False

    passed = sum(results.values())
    total = len(results)

    if passed == total:
        print(f"[PASS] All {total} pattern generation tests passed")
        return True
    else:
        print(f"[PARTIAL] {passed}/{total} pattern generation tests passed")
        return False


def test_drummer_genre_compatibility():
    """Test drummer compatibility with new genres."""
    print("\n[TEST] Testing drummer-genre compatibility...")

    generator = DrumGenerator()

    compatibility_matrix = {
        "bonham": ["rock", "metal"],
        "porcaro": ["rock", "funk", "jazz"],
        "weckl": ["jazz", "funk"],
        "chambers": ["funk", "jazz"],
        "roeder": ["metal", "rock"],
        "dee": ["metal", "rock"],
        "hoglan": ["metal"],
    }

    # Map genres to their default/first valid style
    genre_styles = {
        "rock": "classic",
        "jazz": "swing",
        "funk": "classic",
        "metal": "heavy",
    }

    results = {}

    for drummer, compatible_genres in compatibility_matrix.items():
        try:
            compatible_count = 0
            for genre in compatible_genres:
                # Test pattern generation and drummer style application
                style = genre_styles.get(genre, "classic")
                pattern = generator.generate_pattern(
                    genre, "verse", style=style
                )
                if pattern:
                    styled = generator.apply_drummer_style(pattern, drummer)
                    if styled and len(styled.beats) > 0:
                        compatible_count += 1

            success_rate = compatible_count / len(compatible_genres)
            print(
                f"  {drummer.capitalize()}: {compatible_count}/"
                f"{len(compatible_genres)} genres compatible "
                f"({success_rate:.1%})"
            )
            results[drummer] = success_rate >= 0.8  # 80% success rate

        except Exception as e:
            print(f"[FAIL] Error testing {drummer} compatibility: {e}")
            results[drummer] = False

    passed = sum(results.values())
    total = len(results)

    if passed == total:
        print(f"[PASS] All {total} drummers are properly compatible")
        return True
    else:
        print(f"[PARTIAL] {passed}/{total} drummer compatibility tests passed")
        return False


def test_complete_song_generation():
    """Test generating complete songs with new genres."""
    print("\n[TEST] Testing complete song generation...")

    api = DrumGeneratorAPI()

    test_songs = [
        ("rock", "classic", 140, "bonham"),
        ("jazz", "swing", 120, "weckl"),
        ("funk", "classic", 110, "chambers"),
        ("rock", "blues", 90, "porcaro"),
    ]

    results = {}

    for genre, style, tempo, drummer in test_songs:
        try:
            song = api.create_song(
                genre=genre,
                style=style,
                tempo=tempo,
                drummer=drummer,
                name=f"Test_{genre}_{style}_{drummer}",
            )

            if song and len(song.sections) > 0:
                total_beats = sum(
                    len(section.pattern.beats) for section in song.sections
                )
                print(
                    f"  {genre}/{style} with {drummer}: "
                    f"{len(song.sections)} sections, {total_beats} beats"
                )

                # Try to export
                output_path = Path(f"test_{genre}_{style}_{drummer}_song.mid")
                api.save_as_midi(song, output_path)

                if output_path.exists():
                    file_size = output_path.stat().st_size
                    print(f"    Exported: {file_size} bytes ✓")
                    results[f"{genre}_{style}_{drummer}"] = True
                    # Clean up
                    output_path.unlink()
                else:
                    print("    Export failed ✗")
                    results[f"{genre}_{style}_{drummer}"] = False
            else:
                print(
                    f"  {genre}/{style} with {drummer}: "
                    f"Failed to generate song ✗"
                )
                results[f"{genre}_{style}_{drummer}"] = False

        except Exception as e:
            print(f"[FAIL] Error generating {genre}/{style} song: {e}")
            results[f"{genre}_{style}_{drummer}"] = False

    passed = sum(results.values())
    total = len(results)

    if passed == total:
        print(f"[PASS] All {total} complete song generation tests passed")
        return True
    else:
        print(f"[PARTIAL] {passed}/{total} song generation tests passed")
        return False


def test_genre_fill_patterns():
    """Test that each genre provides appropriate fill patterns."""
    print("\n[TEST] Testing genre fill patterns...")

    from midi_drums.plugins.genres.funk import FunkGenrePlugin
    from midi_drums.plugins.genres.jazz import JazzGenrePlugin
    from midi_drums.plugins.genres.rock import RockGenrePlugin

    plugins = [
        ("rock", RockGenrePlugin()),
        ("jazz", JazzGenrePlugin()),
        ("funk", FunkGenrePlugin()),
    ]

    results = {}

    for genre, plugin in plugins:
        try:
            fills = plugin.get_common_fills()
            fill_count = len(fills)

            if fill_count > 0:
                print(f"  {genre.capitalize()}: {fill_count} common fills")

                # Test each fill has a valid pattern
                valid_fills = 0
                for i, fill in enumerate(fills):
                    beats = len(fill.pattern.beats)
                    prob = fill.trigger_probability
                    if beats > 0 and 0.0 <= prob <= 1.0:
                        valid_fills += 1
                    print(f"    Fill {i+1}: {beats} beats, prob={prob}")

                results[genre] = valid_fills == fill_count
            else:
                print(f"  {genre.capitalize()}: No fills available ✗")
                results[genre] = False

        except Exception as e:
            print(f"[FAIL] Error testing {genre} fills: {e}")
            results[genre] = False

    passed = sum(results.values())
    total = len(results)

    if passed == total:
        print(f"[PASS] All {total} genres have valid fill patterns")
        return True
    else:
        print(f"[PARTIAL] {passed}/{total} genre fill tests passed")
        return False


def main():
    """Run all new genre plugin tests."""
    print("=" * 70)
    print("Comprehensive New Genre Plugin Test Suite")
    print("Testing: Rock, Jazz, Funk (+ existing Metal)")
    print("=" * 70)

    tests = [
        test_genre_plugin_loading,
        test_genre_style_support,
        test_pattern_generation,
        test_drummer_genre_compatibility,
        test_complete_song_generation,
        test_genre_fill_patterns,
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
        print("[SUCCESS] All genre plugin tests passed!")
        print("\nAvailable genres and their styles:")

        generator = DrumGenerator()
        for genre in sorted(generator.get_available_genres()):
            styles = generator.get_styles_for_genre(genre)
            print(f"- {genre.upper()}: {', '.join(styles)}")

    else:
        print("[WARNING] Some genre tests failed. Check output above.")

    print("=" * 70)


if __name__ == "__main__":
    main()
