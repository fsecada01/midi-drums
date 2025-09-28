#!/usr/bin/env python3
"""
Test script to verify the new MIDI drums architecture works correctly.
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all modules can be imported."""
    print("🧪 Testing imports...")

    try:
        # Test that imports work (imports are only used for testing)
        from midi_drums import Beat, DrumGenerator  # noqa: F401
        from midi_drums.api.python_api import DrumGeneratorAPI  # noqa: F401
        from midi_drums.models.pattern import DrumInstrument  # noqa: F401
        from midi_drums.models.pattern import PatternBuilder  # noqa: F401
        from midi_drums.models.song import GenerationParameters  # noqa: F401
        from midi_drums.plugins.genres.metal import (  # noqa: F401
            MetalGenrePlugin,
        )

        print("✅ All core imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_pattern_creation():
    """Test pattern creation and manipulation."""
    print("🧪 Testing pattern creation...")

    try:
        from midi_drums.models.pattern import PatternBuilder

        # Create a simple pattern
        builder = PatternBuilder("test_pattern")
        pattern = (
            builder.kick(0.0, 110)
            .snare(1.0, 115)
            .hihat(0.0, 80)
            .hihat(0.5, 75)
            .hihat(1.0, 80)
            .hihat(1.5, 75)
            .build()
        )

        print(
            f"✅ Created pattern: {pattern.name} with "
            f"{len(pattern.beats)} beats"
        )

        # Test humanization
        humanized = pattern.humanize()
        print(f"✅ Humanized pattern: {humanized.name}")

        return True
    except Exception as e:
        print(f"❌ Pattern creation failed: {e}")
        return False


def test_metal_plugin():
    """Test metal genre plugin."""
    print("🧪 Testing metal plugin...")

    try:
        from midi_drums.models.song import GenerationParameters
        from midi_drums.plugins.genres.metal import MetalGenrePlugin

        plugin = MetalGenrePlugin()
        params = GenerationParameters(genre="metal", style="heavy")

        # Test pattern generation
        verse = plugin.generate_pattern("verse", params)
        chorus = plugin.generate_pattern("chorus", params)

        print(f"✅ Generated verse: {verse.name} ({len(verse.beats)} beats)")
        print(f"✅ Generated chorus: {chorus.name} ({len(chorus.beats)} beats)")

        # Test fills
        fills = plugin.get_common_fills()
        print(f"✅ Generated {len(fills)} fill patterns")

        return True
    except Exception as e:
        print(f"❌ Metal plugin test failed: {e}")
        return False


def test_engine():
    """Test the main drum generation engine."""
    print("🧪 Testing drum generator engine...")

    try:
        from midi_drums import DrumGenerator

        generator = DrumGenerator()

        # Test pattern generation
        pattern = generator.generate_pattern("metal", "verse", style="heavy")
        if not pattern:
            print("❌ Pattern generation failed")
            return False

        print(f"✅ Engine generated pattern: {pattern.name}")

        # Test song creation
        song = generator.create_song("metal", "heavy", 155)
        print(
            f"✅ Engine generated song: {song.name} with "
            f"{len(song.sections)} sections"
        )

        return True
    except Exception as e:
        print(f"❌ Engine test failed: {e}")
        return False


def test_midi_export():
    """Test MIDI file export."""
    print("🧪 Testing MIDI export...")

    try:
        from midi_drums.api.python_api import DrumGeneratorAPI

        api = DrumGeneratorAPI()

        # Generate a simple pattern
        pattern = api.generate_pattern("metal", "verse", "heavy")
        if not pattern:
            print("❌ Pattern generation failed")
            return False

        # Export pattern
        pattern_file = "test_pattern.mid"
        api.save_pattern_as_midi(pattern, pattern_file)

        if Path(pattern_file).exists():
            print(f"✅ Pattern exported to: {pattern_file}")
        else:
            print("❌ Pattern file not created")
            return False

        # Generate and export song
        song = api.create_song("metal", "heavy", 140)
        song_file = "test_song.mid"
        api.save_as_midi(song, song_file)

        if Path(song_file).exists():
            print(f"✅ Song exported to: {song_file}")
        else:
            print("❌ Song file not created")
            return False

        return True
    except Exception as e:
        print(f"❌ MIDI export test failed: {e}")
        return False


def test_api():
    """Test the high-level API."""
    print("🧪 Testing API...")

    try:
        from midi_drums.api.python_api import DrumGeneratorAPI

        api = DrumGeneratorAPI()

        # Test info methods
        genres = api.list_genres()
        print(f"✅ Available genres: {genres}")

        if "metal" in genres:
            styles = api.list_styles("metal")
            print(f"✅ Metal styles: {styles}")

        # Test quick generation methods
        song = api.metal_song("heavy", 140, 0.5)
        print(f"✅ Quick metal song: {song.name}")

        info = api.get_song_info(song)
        print(f"✅ Song info retrieved: {info['total_bars']} bars")

        return True
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def cleanup_test_files():
    """Clean up test files."""
    test_files = [
        "test_pattern.mid",
        "test_song.mid",
        "metal_heavy_verse.mid",
        "metal_death_chorus.mid",
    ]

    for file in test_files:
        path = Path(file)
        if path.exists():
            path.unlink()
            print(f"🧹 Cleaned up: {file}")


def main():
    """Run all tests."""
    print("🎵 MIDI Drums - Architecture Test Suite")
    print("=" * 50)

    tests = [
        ("Imports", test_imports),
        ("Pattern Creation", test_pattern_creation),
        ("Metal Plugin", test_metal_plugin),
        ("Engine", test_engine),
        ("MIDI Export", test_midi_export),
        ("API", test_api),
    ]

    results = []
    for test_name, test_func in tests:
        print()
        success = test_func()
        results.append((test_name, success))

    print("\n" + "=" * 50)
    print("📊 Test Results:")

    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        if success:
            passed += 1

    print(f"\n📈 Summary: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All tests passed! Architecture is working correctly.")
        cleanup_test_files()
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
