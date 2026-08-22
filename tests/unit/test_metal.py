"""Test the template-based Metal genre plugin."""

from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.plugins.genres.metal import MetalGenrePlugin


def test_refactored_metal_plugin_basic():
    """Test basic plugin structure."""
    print("Testing metal plugin basic structure...")

    refactored = MetalGenrePlugin()

    assert refactored.genre_name == "metal"
    print(f"  [OK] Genre name: {refactored.genre_name}")

    assert len(refactored.supported_styles) == 7
    print(f"  [OK] Styles: {len(refactored.supported_styles)} styles")


def test_refactored_all_styles_all_sections():
    """Test that refactored plugin generates all combinations."""
    print("Testing all metal styles and sections...")

    refactored = MetalGenrePlugin()
    styles = refactored.supported_styles
    sections = ["intro", "verse", "chorus", "breakdown", "bridge", "outro"]

    generated_count = 0
    for style in styles:
        for section in sections:
            params = GenerationParameters(
                genre="metal", style=style, complexity=0.7, humanization=0.3
            )

            pattern = refactored.generate_pattern(section, params)

            assert pattern is not None, f"Failed to generate {style} {section}"
            assert (
                len(pattern.beats) > 0
            ), f"Empty pattern for {style} {section}"
            assert pattern.name.startswith(
                "metal_"
            ), f"Wrong name format: {pattern.name}"

            generated_count += 1

    print(
        f"  [OK] Generated {generated_count} patterns (7 styles × 6 sections)"
    )


def test_refactored_death_metal_blast_beats():
    """Test that death metal generates blast beat patterns."""
    print("Testing death metal blast beats...")

    refactored = MetalGenrePlugin()
    params = GenerationParameters(
        genre="metal", style="death", complexity=0.8, humanization=0.2
    )

    verse = refactored.generate_pattern("verse", params)

    # Death metal verse should have many kicks and snares (blast beats)
    kick_count = sum(
        1 for b in verse.beats if b.instrument == DrumInstrument.KICK
    )
    snare_count = sum(
        1 for b in verse.beats if b.instrument == DrumInstrument.SNARE
    )

    assert (
        kick_count >= 8
    ), f"Expected many kicks in blast beat, got {kick_count}"
    assert (
        snare_count >= 8
    ), f"Expected many snares in blast beat, got {snare_count}"

    print(f"  [OK] Death metal: {kick_count} kicks, {snare_count} snares")


def test_refactored_power_metal_gallop():
    """Test that power metal generates galloping patterns."""
    print("Testing power metal gallop patterns...")

    refactored = MetalGenrePlugin()
    params = GenerationParameters(
        genre="metal", style="power", complexity=0.7, humanization=0.3
    )

    verse = refactored.generate_pattern("verse", params)

    # Power metal should have galloping kicks (6 per bar for gallop pattern)
    kick_count = sum(
        1 for b in verse.beats if b.instrument == DrumInstrument.KICK
    )

    # Gallop pattern produces 6 kicks per bar
    assert kick_count >= 4, f"Expected galloping kicks, got {kick_count}"

    print(f"  [OK] Power metal: {kick_count} kicks (gallop pattern)")


def test_refactored_doom_metal_slow():
    """Test that doom metal is slower and heavier."""
    print("Testing doom metal slow patterns...")

    refactored = MetalGenrePlugin()
    params = GenerationParameters(
        genre="metal", style="doom", complexity=0.5, humanization=0.3
    )

    verse = refactored.generate_pattern("verse", params)

    # Doom should have fewer total beats (slower subdivisions)
    total_beats = len(verse.beats)

    # Quarter note hihat = fewer beats for slowness
    # Expect: 2 kicks + 2 snares + 4 hihats = ~8-12 beats
    assert (
        total_beats < 20
    ), f"Doom should have fewer beats for slowness, got {total_beats}"

    print(f"  [OK] Doom metal: {total_beats} beats (slow and heavy)")


def test_refactored_progressive_complexity():
    """Test that progressive metal has higher complexity."""
    print("Testing progressive metal complexity...")

    refactored = MetalGenrePlugin()
    params = GenerationParameters(
        genre="metal", style="progressive", complexity=0.8, humanization=0.2
    )

    verse = refactored.generate_pattern("verse", params)

    # Progressive should have syncopated kicks and 16th note hihats
    kick_positions = [
        b.position for b in verse.beats if b.instrument == DrumInstrument.KICK
    ]
    hihat_count = sum(
        1 for b in verse.beats if b.instrument == DrumInstrument.CLOSED_HH
    )

    # Should have syncopated kicks (at least one off-beat)
    has_syncopation = any(pos % 1.0 not in [0.0, 0.5] for pos in kick_positions)

    # Should have many hihats (16th subdivision = 16 per bar)
    assert (
        hihat_count >= 12
    ), f"Expected many hihats in progressive, got {hihat_count}"
    assert has_syncopation, "Expected syncopated kicks in progressive metal"

    print(f"  [OK] Progressive metal: {hihat_count} hihats, syncopated kicks")


def test_refactored_breakdown_pattern():
    """Test that breakdown generates heavy syncopated pattern."""
    print("Testing breakdown pattern...")

    refactored = MetalGenrePlugin()
    params = GenerationParameters(
        genre="metal", style="heavy", complexity=0.6, humanization=0.3
    )

    breakdown = refactored.generate_pattern("breakdown", params)

    # Breakdown should have syncopated kicks
    kick_positions = [
        b.position
        for b in breakdown.beats
        if b.instrument == DrumInstrument.KICK
    ]

    # Should have kicks at 0.0, 1.5, 2.5 (syncopated)
    assert len(kick_positions) >= 2, "Expected multiple kicks in breakdown"

    # Check for syncopation (not all on beats 0, 1, 2, 3)
    has_offbeat = any(pos % 1.0 != 0.0 for pos in kick_positions)
    assert has_offbeat, "Expected syncopated kicks in breakdown"

    print(f"  [OK] Breakdown: {len(kick_positions)} syncopated kicks")


def test_refactored_chorus_intensity():
    """Test that chorus is more intense than verse."""
    print("Testing chorus intensity...")

    refactored = MetalGenrePlugin()
    params = GenerationParameters(
        genre="metal", style="heavy", complexity=0.7, humanization=0.3
    )

    verse = refactored.generate_pattern("verse", params)
    chorus = refactored.generate_pattern("chorus", params)

    # Chorus should have more elements (crashes, more kicks, etc.)
    verse_beats = len(verse.beats)
    chorus_beats = len(chorus.beats)

    # Chorus should have crash cymbal
    has_crash = any(b.instrument == DrumInstrument.CRASH for b in chorus.beats)

    assert has_crash, "Expected crash cymbal in chorus"
    assert (
        chorus_beats >= verse_beats
    ), f"Chorus should be more intense: {chorus_beats} vs {verse_beats}"

    print(
        f"  [OK] Chorus intensity: {chorus_beats} beats vs verse {verse_beats}"
    )


def test_refactored_fills():
    """Test that common fills are generated."""
    print("Testing metal fills...")

    refactored = MetalGenrePlugin()
    fills = refactored.get_common_fills()

    assert len(fills) >= 2, f"Expected at least 2 fills, got {len(fills)}"

    for i, fill in enumerate(fills):
        assert fill.pattern is not None, f"Fill {i} has no pattern"
        assert len(fill.pattern.beats) > 0, f"Fill {i} is empty"
        print(f"  [OK] Fill {i+1}: {len(fill.pattern.beats)} beats")

    print(f"  [OK] Total fills: {len(fills)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Refactored Metal Genre Plugin Tests")
    print("=" * 60)

    test_refactored_metal_plugin_basic()
    test_refactored_all_styles_all_sections()
    test_refactored_death_metal_blast_beats()
    test_refactored_power_metal_gallop()
    test_refactored_doom_metal_slow()
    test_refactored_progressive_complexity()
    test_refactored_breakdown_pattern()
    test_refactored_chorus_intensity()
    test_refactored_fills()

    print("=" * 60)
    print("All metal tests passed!")
    print("=" * 60)
