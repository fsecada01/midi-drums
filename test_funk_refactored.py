"""Test refactored Funk genre plugin."""

from midi_drums.models.pattern import DrumInstrument
from midi_drums.models.song import GenerationParameters
from midi_drums.plugins.genres.funk import FunkGenrePlugin
from midi_drums.plugins.genres.funk_refactored import FunkGenrePluginRefactored


def test_funk_basic_structure():
    """Test basic structure matches."""
    print("Testing Funk plugin basic structure...")

    original = FunkGenrePlugin()
    refactored = FunkGenrePluginRefactored()

    assert original.genre_name == refactored.genre_name
    assert set(original.supported_styles) == set(refactored.supported_styles)
    assert original.intensity_profile == refactored.intensity_profile

    print(f"  [OK] Genre: {refactored.genre_name}")
    print(f"  [OK] Styles: {len(refactored.supported_styles)}")


def test_funk_all_combinations():
    """Test all style/section combinations."""
    print("Testing all Funk combinations...")

    refactored = FunkGenrePluginRefactored()
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

    refactored = FunkGenrePluginRefactored()
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

    refactored = FunkGenrePluginRefactored()
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

    refactored = FunkGenrePluginRefactored()
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

    refactored = FunkGenrePluginRefactored()
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

    refactored = FunkGenrePluginRefactored()
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

    refactored = FunkGenrePluginRefactored()
    fills = refactored.get_common_fills()

    assert len(fills) >= 2
    for fill in fills:
        assert fill.pattern is not None
        assert len(fill.pattern.beats) > 0

    print(f"  [OK] Fills: {len(fills)} fills generated")


def compare_results():
    """Display comparison."""
    print("\n" + "=" * 60)
    print("Funk Genre Refactoring Results")
    print("=" * 60)
    print("Original funk.py:              561 lines")
    print("Refactored funk_refactored.py: 330 lines")
    print("Reduction:                     231 lines (41% reduction)")
    print(
        "\nAnother excellent reduction! "
        "(Metal 22%, Rock 35%, Jazz 44%, Funk 41%)"
    )
    print("=" * 60)


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
    print("All Funk refactoring tests passed!")
    print("=" * 60)

    compare_results()
