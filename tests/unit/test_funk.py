"""Test the Funk genre plugin."""

from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.plugins.genres.funk import FunkGenrePlugin


def test_funk_basic_structure():
    """Test basic plugin structure."""
    print("Testing Funk plugin basic structure...")

    refactored = FunkGenrePlugin()

    assert refactored.genre_name == "funk"
    assert len(refactored.supported_styles) == 7

    print(f"  [OK] Genre: {refactored.genre_name}")
    print(f"  [OK] Styles: {len(refactored.supported_styles)}")


def test_funk_all_combinations():
    """Test all style/section combinations."""
    print("Testing all Funk combinations...")

    refactored = FunkGenrePlugin()
    styles = refactored.supported_styles
    sections = ["intro", "verse", "chorus", "breakdown", "bridge", "outro"]

    count = 0
    for style in styles:
        for section in sections:
            params = GenerationParameters(
                genre="funk", style=style, complexity=0.7, humanization=0.3
            )
            pattern = refactored.generate_pattern(section, params)

            assert pattern is not None
            assert len(pattern.beats) > 0
            count += 1

    print(f"  [OK] Generated {count} patterns (7 styles × 6 sections)")


def test_funk_classic_ghost_notes():
    """Test classic funk ghost notes."""
    print("Testing classic funk ghost notes...")

    refactored = FunkGenrePlugin()
    params = GenerationParameters(
        genre="funk", style="classic", complexity=0.7, humanization=0.3
    )

    verse = refactored.generate_pattern("verse", params)

    # Classic funk should have many snare hits (ghost notes)
    snare_count = sum(
        1 for b in verse.beats if b.instrument == DrumInstrument.SNARE
    )
    assert (
        snare_count >= 8
    ), f"Classic funk should have ghost notes, got {snare_count}"

    # Should have varying velocities (ghost notes are soft)
    snare_velocities = [
        b.velocity for b in verse.beats if b.instrument == DrumInstrument.SNARE
    ]
    velocity_range = max(snare_velocities) - min(snare_velocities)
    assert (
        velocity_range >= 20
    ), f"Ghost notes should vary in velocity, range: {velocity_range}"

    print(f"  [OK] Classic funk: {snare_count} snare hits with ghost notes")


def test_funk_shuffle_style():
    """Test shuffle funk style."""
    print("Testing shuffle funk style...")

    refactored = FunkGenrePlugin()
    params = GenerationParameters(
        genre="funk", style="shuffle", complexity=0.7, humanization=0.3
    )

    verse = refactored.generate_pattern("verse", params)

    # Shuffle should have ride cymbal (Purdie shuffle)
    has_ride = any(b.instrument == DrumInstrument.RIDE for b in verse.beats)
    assert has_ride, "Shuffle funk should have ride cymbal"

    print("  [OK] Shuffle funk: ride cymbal verified")


def test_funk_the_one():
    """Test 'the one' emphasis in classic funk."""
    print("Testing 'the one' emphasis...")

    refactored = FunkGenrePlugin()
    params = GenerationParameters(
        genre="funk", style="classic", complexity=0.7, humanization=0.3
    )

    chorus = refactored.generate_pattern("chorus", params)

    # Should have crash on beat 1 (the one)
    has_crash_on_one = any(
        b.instrument == DrumInstrument.CRASH and abs(b.position) < 0.1
        for b in chorus.beats
    )
    assert has_crash_on_one, "Classic funk chorus should emphasize 'the one'"

    print("  [OK] Classic funk: 'the one' crash verified")


def test_funk_pfunk_syncopation():
    """Test P-Funk syncopation."""
    print("Testing P-Funk syncopation...")

    refactored = FunkGenrePlugin()
    params = GenerationParameters(
        genre="funk", style="pfunk", complexity=0.7, humanization=0.3
    )

    verse = refactored.generate_pattern("verse", params)

    # P-Funk should have syncopated kicks
    kick_count = sum(
        1 for b in verse.beats if b.instrument == DrumInstrument.KICK
    )
    assert (
        kick_count >= 3
    ), f"P-Funk should have syncopated kicks, got {kick_count}"

    print(f"  [OK] P-Funk: {kick_count} kicks (syncopated)")


def test_funk_minimal_pocket():
    """Test minimal funk pocket."""
    print("Testing minimal funk pocket...")

    refactored = FunkGenrePlugin()
    params = GenerationParameters(
        genre="funk", style="minimal", complexity=0.7, humanization=0.3
    )

    verse = refactored.generate_pattern("verse", params)

    # Minimal should have fewer notes overall (sparse pocket)
    total_notes = len(verse.beats)
    assert (
        total_notes < 30
    ), f"Minimal funk should be sparse, got {total_notes} notes"

    print(f"  [OK] Minimal funk: {total_notes} notes (sparse pocket)")


def test_funk_fills():
    """Test fill generation."""
    print("Testing Funk fills...")

    refactored = FunkGenrePlugin()
    fills = refactored.get_common_fills()

    assert len(fills) >= 2
    for fill in fills:
        assert fill.pattern is not None
        assert len(fill.pattern.beats) > 0

    print(f"  [OK] Fills: {len(fills)} fills generated")


if __name__ == "__main__":
    print("=" * 60)
    print("Funk Genre Plugin Refactoring Tests")
    print("=" * 60)

    test_funk_basic_structure()
    test_funk_all_combinations()
    test_funk_classic_ghost_notes()
    test_funk_shuffle_style()
    test_funk_the_one()
    test_funk_pfunk_syncopation()
    test_funk_minimal_pocket()
    test_funk_fills()

    print("=" * 60)
    print("All Funk tests passed!")
    print("=" * 60)
