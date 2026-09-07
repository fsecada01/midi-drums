"""Test the Jazz genre plugin."""

from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.plugins.genres.jazz import JazzGenrePlugin


def test_jazz_basic_structure():
    """Test basic plugin structure."""
    print("Testing Jazz plugin basic structure...")

    refactored = JazzGenrePlugin()

    assert refactored.genre_name == "jazz"
    assert len(refactored.supported_styles) == 7

    print(f"  [OK] Genre: {refactored.genre_name}")
    print(f"  [OK] Styles: {len(refactored.supported_styles)}")


def test_jazz_all_combinations():
    """Test all style/section combinations."""
    print("Testing all Jazz combinations...")

    refactored = JazzGenrePlugin()
    styles = refactored.supported_styles
    sections = ["intro", "verse", "chorus", "breakdown", "bridge", "outro"]

    count = 0
    for style in styles:
        for section in sections:
            params = GenerationParameters(
                genre="jazz", style=style, complexity=0.7, humanization=0.3
            )
            pattern = refactored.generate_pattern(section, params)

            assert pattern is not None
            assert len(pattern.beats) > 0
            count += 1

    print(f"  [OK] Generated {count} patterns (7 styles × 6 sections)")


def test_jazz_swing_style():
    """Test swing jazz style."""
    print("Testing swing jazz style...")

    refactored = JazzGenrePlugin()
    params = GenerationParameters(
        genre="jazz", style="swing", complexity=0.7, humanization=0.3
    )

    verse = refactored.generate_pattern("verse", params)

    # Should have ride cymbal (swing uses ride)
    has_ride = any(b.instrument == DrumInstrument.RIDE for b in verse.beats)
    assert has_ride, "Swing jazz should have ride cymbal"

    print("  [OK] Swing jazz: ride cymbal verified")


def test_jazz_bebop_complexity():
    """Test bebop complexity."""
    print("Testing bebop complexity...")

    refactored = JazzGenrePlugin()
    params = GenerationParameters(
        genre="jazz", style="bebop", complexity=0.7, humanization=0.3
    )

    verse = refactored.generate_pattern("verse", params)

    # Bebop should have ride cymbal
    has_ride = any(b.instrument == DrumInstrument.RIDE for b in verse.beats)
    assert has_ride, "Bebop should have ride cymbal"

    # Bebop should have syncopated kicks
    kick_count = sum(
        1 for b in verse.beats if b.instrument == DrumInstrument.KICK
    )
    assert (
        kick_count >= 3
    ), f"Bebop should have syncopated kicks, got {kick_count}"

    print(f"  [OK] Bebop: {kick_count} kicks (syncopated)")


def test_jazz_fusion_energy():
    """Test fusion jazz energy."""
    print("Testing fusion jazz energy...")

    refactored = JazzGenrePlugin()
    params = GenerationParameters(
        genre="jazz", style="fusion", complexity=0.7, humanization=0.3
    )

    verse = refactored.generate_pattern("verse", params)

    # Fusion should have many hihat/ride notes (16th notes)
    hihat_ride_count = sum(
        1
        for b in verse.beats
        if b.instrument
        in [
            DrumInstrument.CLOSED_HH,
            DrumInstrument.OPEN_HH,
            DrumInstrument.RIDE,
        ]
    )
    assert (
        hihat_ride_count >= 8
    ), f"Fusion should have 16th notes, got {hihat_ride_count}"

    print(f"  [OK] Fusion: {hihat_ride_count} hihat/ride notes")


def test_jazz_ballad_softness():
    """Test ballad softness."""
    print("Testing ballad softness...")

    refactored = JazzGenrePlugin()
    params = GenerationParameters(
        genre="jazz", style="ballad", complexity=0.7, humanization=0.3
    )

    verse = refactored.generate_pattern("verse", params)

    # Ballad should have ride cymbal (soft brushes)
    has_ride = any(b.instrument == DrumInstrument.RIDE for b in verse.beats)
    assert has_ride, "Ballad should have ride cymbal"

    # Ballad should have lower velocities
    avg_velocity = sum(b.velocity for b in verse.beats) / len(verse.beats)
    assert (
        avg_velocity < 90
    ), f"Ballad should be soft, avg velocity: {avg_velocity}"

    print(f"  [OK] Ballad: soft dynamics (avg velocity {avg_velocity:.1f})")


def test_jazz_fills():
    """Test fill generation."""
    print("Testing Jazz fills...")

    refactored = JazzGenrePlugin()
    fills = refactored.get_common_fills()

    assert len(fills) >= 2
    for fill in fills:
        assert fill.pattern is not None
        assert len(fill.pattern.beats) > 0

    print(f"  [OK] Fills: {len(fills)} fills generated")


if __name__ == "__main__":
    print("=" * 60)
    print("Jazz Genre Plugin Refactoring Tests")
    print("=" * 60)

    test_jazz_basic_structure()
    test_jazz_all_combinations()
    test_jazz_swing_style()
    test_jazz_bebop_complexity()
    test_jazz_fusion_energy()
    test_jazz_ballad_softness()
    test_jazz_fills()

    print("=" * 60)
    print("All Jazz tests passed!")
    print("=" * 60)
