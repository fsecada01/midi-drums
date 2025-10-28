#!/usr/bin/env python3
"""Test script for genre context adaptation feature.

Demonstrates how patterns adapt to song genre context while maintaining
their characteristic feel.
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from midi_drums import DrumGenerator


def test_intensity_profiles():
    """Display intensity profiles for all genres."""
    print("=" * 70)
    print("Genre Intensity Profiles")
    print("=" * 70)
    print()

    generator = DrumGenerator()
    genres = generator.get_available_genres()

    for genre in genres:
        plugin = generator.plugin_manager.get_genre_plugin(genre)
        if plugin:
            profile = plugin.intensity_profile
            print(f"{genre.upper()}")
            print(f"  Aggression: {profile['aggression']:.2f}")
            print(f"  Speed:      {profile['speed']:.2f}")
            print(f"  Density:    {profile['density']:.2f}")
            print(f"  Power:      {profile['power']:.2f}")
            print(f"  Complexity: {profile['complexity']:.2f}")
            print(f"  Darkness:   {profile['darkness']:.2f}")
            print()


def analyze_pattern_characteristics(pattern, name):
    """Analyze and display pattern characteristics."""
    if not pattern:
        print("  ❌ Failed to generate")
        return

    # Calculate statistics
    kick_beats = [b for b in pattern.beats if b.instrument.value == 36]
    snare_beats = [b for b in pattern.beats if b.instrument.value == 38]

    avg_kick_velocity = (
        sum(b.velocity for b in kick_beats) / len(kick_beats)
        if kick_beats
        else 0
    )
    avg_snare_velocity = (
        sum(b.velocity for b in snare_beats) / len(snare_beats)
        if snare_beats
        else 0
    )

    print(f"{name}:")
    print(f"  Total beats:       {len(pattern.beats)}")
    print(f"  Kick hits:         {len(kick_beats)}")
    print(f"  Snare hits:        {len(snare_beats)}")
    print(f"  Avg kick vel:      {avg_kick_velocity:.1f}")
    print(f"  Avg snare vel:     {avg_snare_velocity:.1f}")
    print()


def test_progressive_metal_context():
    """Test progressive patterns with and without metal context."""
    print("=" * 70)
    print("Test: Progressive Patterns in Metal Context")
    print("=" * 70)
    print()

    generator = DrumGenerator()

    # Pure progressive pattern
    print("Generating PURE progressive pattern (no context)...")
    pure_prog = generator.generate_pattern(
        genre="metal",
        style="progressive",
        section="bridge",
        bars=4,
    )
    analyze_pattern_characteristics(pure_prog, "Pure Progressive")

    # Progressive with light metal context
    print("Generating progressive with LIGHT metal context (30%)...")
    light_blend = generator.generate_pattern(
        genre="metal",
        style="progressive",
        section="bridge",
        bars=4,
        song_genre_context="metal",
        context_blend=0.3,
    )
    analyze_pattern_characteristics(light_blend, "Light Metal Blend (30%)")

    # Progressive with heavy metal context
    print("Generating progressive with HEAVY metal context (60%)...")
    heavy_blend = generator.generate_pattern(
        genre="metal",
        style="progressive",
        section="bridge",
        bars=4,
        song_genre_context="metal",
        context_blend=0.6,
    )
    analyze_pattern_characteristics(heavy_blend, "Heavy Metal Blend (60%)")

    # Export for comparison
    output_dir = Path("test_context_output")
    output_dir.mkdir(exist_ok=True)

    if pure_prog:
        generator.export_pattern_midi(
            pure_prog, output_dir / "progressive_pure.mid", tempo=160
        )
    if light_blend:
        generator.export_pattern_midi(
            light_blend, output_dir / "progressive_metal_30.mid", tempo=160
        )
    if heavy_blend:
        generator.export_pattern_midi(
            heavy_blend, output_dir / "progressive_metal_60.mid", tempo=160
        )

    print(f"✅ Exported MIDI files to: {output_dir}")
    print()


def test_funk_in_rock_context():
    """Test funk patterns adapted to rock context."""
    print("=" * 70)
    print("Test: Funk Patterns in Rock Context")
    print("=" * 70)
    print()

    generator = DrumGenerator()

    # Pure funk
    print("Generating PURE funk pattern...")
    pure_funk = generator.generate_pattern(
        genre="funk", style="classic", section="verse", bars=4
    )
    analyze_pattern_characteristics(pure_funk, "Pure Funk")

    # Funk with rock context
    print("Generating funk with ROCK context (40%)...")
    rock_funk = generator.generate_pattern(
        genre="funk",
        style="classic",
        section="verse",
        bars=4,
        song_genre_context="rock",
        context_blend=0.4,
    )
    analyze_pattern_characteristics(rock_funk, "Funk with Rock Context (40%)")

    # Export
    output_dir = Path("test_context_output")
    output_dir.mkdir(exist_ok=True)

    if pure_funk:
        generator.export_pattern_midi(
            pure_funk, output_dir / "funk_pure.mid", tempo=100
        )
    if rock_funk:
        generator.export_pattern_midi(
            rock_funk, output_dir / "funk_rock_40.mid", tempo=100
        )

    print(f"✅ Exported MIDI files to: {output_dir}")
    print()


def test_jazz_in_metal_context():
    """Test jazz patterns adapted to metal context (extreme example)."""
    print("=" * 70)
    print("Test: Jazz Patterns in Metal Context (Extreme)")
    print("=" * 70)
    print()

    generator = DrumGenerator()

    # Pure jazz fusion
    print("Generating PURE jazz fusion pattern...")
    pure_jazz = generator.generate_pattern(
        genre="jazz", style="fusion", section="verse", bars=4
    )
    analyze_pattern_characteristics(pure_jazz, "Pure Jazz Fusion")

    # Jazz with metal context (subtle blend)
    print("Generating jazz fusion with METAL context (25%)...")
    metal_jazz = generator.generate_pattern(
        genre="jazz",
        style="fusion",
        section="verse",
        bars=4,
        song_genre_context="metal",
        context_blend=0.25,
    )
    analyze_pattern_characteristics(
        metal_jazz, "Jazz Fusion with Metal Context (25%)"
    )

    # Export
    output_dir = Path("test_context_output")
    output_dir.mkdir(exist_ok=True)

    if pure_jazz:
        generator.export_pattern_midi(
            pure_jazz, output_dir / "jazz_pure.mid", tempo=140
        )
    if metal_jazz:
        generator.export_pattern_midi(
            metal_jazz, output_dir / "jazz_metal_25.mid", tempo=140
        )

    print(f"✅ Exported MIDI files to: {output_dir}")
    print()


def main():
    """Run all context adaptation tests."""
    print()
    print("╔═════════════════════════════════════════════════════════════════╗")
    print("║         Genre Context Adaptation Feature Test Suite            ║")
    print("╚═════════════════════════════════════════════════════════════════╝")
    print()

    # Show intensity profiles
    test_intensity_profiles()

    # Test progressive in metal
    test_progressive_metal_context()

    # Test funk in rock
    test_funk_in_rock_context()

    # Test jazz in metal (extreme example)
    test_jazz_in_metal_context()

    print("=" * 70)
    print("All Tests Complete!")
    print("=" * 70)
    print()
    print("Compare the generated MIDI files in 'test_context_output/' to hear")
    print("how patterns adapt to different genre contexts while maintaining")
    print("their core characteristics.")
    print()


if __name__ == "__main__":
    main()
