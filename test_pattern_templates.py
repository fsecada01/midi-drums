"""Test pattern template system.

This test suite validates the pattern template system including:
- Base template functionality
- Individual template implementations
- Template composition
- Integration with existing pattern system
"""

from midi_drums.config import TIMING
from midi_drums.models.pattern import DrumInstrument
from midi_drums.patterns import (
    BasicGroove,
    BlastBeat,
    CrashAccents,
    DoubleBassPedal,
    FunkGhostNotes,
    JazzRidePattern,
    TemplateComposer,
    TomFill,
    create_basic_rock_pattern,
    create_metal_pattern,
)


def test_basic_groove_template():
    """Test BasicGroove template."""
    print("Testing BasicGroove template...")

    template = BasicGroove(
        kick_positions=[0.0, 2.0],
        snare_positions=[1.0, 3.0],
        hihat_subdivision=TIMING.EIGHTH,
    )

    pattern = (
        TemplateComposer("test_basic")
        .add(template)
        .build(bars=1, complexity=0.5)
    )

    # Should have kicks, snares, and hihats
    kick_count = sum(
        1 for b in pattern.beats if b.instrument == DrumInstrument.KICK
    )
    snare_count = sum(
        1 for b in pattern.beats if b.instrument == DrumInstrument.SNARE
    )
    hihat_count = sum(
        1 for b in pattern.beats if b.instrument == DrumInstrument.CLOSED_HH
    )

    assert kick_count == 2, f"Expected 2 kicks, got {kick_count}"
    assert snare_count == 2, f"Expected 2 snares, got {snare_count}"
    assert hihat_count == 8, f"Expected 8 hihats, got {hihat_count}"

    print(
        f"  [OK] BasicGroove: {kick_count} kicks, {snare_count} snares, {hihat_count} hihats"
    )


def test_double_bass_template():
    """Test DoubleBassPedal template."""
    print("Testing DoubleBassPedal template...")

    # Continuous pattern
    template = DoubleBassPedal(
        subdivision=TIMING.SIXTEENTH,
        intensity=0.9,
        pattern_type="continuous",
    )

    pattern = TemplateComposer("test_double_bass").add(template).build(bars=1)

    kick_count = sum(
        1 for b in pattern.beats if b.instrument == DrumInstrument.KICK
    )

    # Should have 16th note kicks (16 per bar)
    assert kick_count == 16, f"Expected 16 kicks, got {kick_count}"

    # Test gallop pattern
    gallop = DoubleBassPedal(pattern_type="gallop")
    gallop_pattern = TemplateComposer("test_gallop").add(gallop).build(bars=1)
    gallop_kicks = sum(
        1 for b in gallop_pattern.beats if b.instrument == DrumInstrument.KICK
    )

    assert gallop_kicks == 6, f"Expected 6 gallop kicks, got {gallop_kicks}"

    print(
        f"  [OK] DoubleBassPedal: continuous={kick_count}, gallop={gallop_kicks}"
    )


def test_blast_beat_template():
    """Test BlastBeat template."""
    print("Testing BlastBeat template...")

    # Traditional blast beat
    template = BlastBeat(style="traditional", intensity=1.0)

    pattern = TemplateComposer("test_blast").add(template).build(bars=1)

    kick_count = sum(
        1 for b in pattern.beats if b.instrument == DrumInstrument.KICK
    )
    snare_count = sum(
        1 for b in pattern.beats if b.instrument == DrumInstrument.SNARE
    )

    # Traditional blast: kick + snare on every 8th (8 times)
    assert kick_count == 8, f"Expected 8 kicks, got {kick_count}"
    assert snare_count == 8, f"Expected 8 snares, got {snare_count}"

    # Test hammer blast
    hammer = BlastBeat(style="hammer")
    hammer_pattern = TemplateComposer("test_hammer").add(hammer).build(bars=1)
    hammer_snares = sum(
        1 for b in hammer_pattern.beats if b.instrument == DrumInstrument.SNARE
    )

    # Hammer blast has 16th note snares (16 per bar)
    assert (
        hammer_snares == 16
    ), f"Expected 16 hammer snares, got {hammer_snares}"

    print(
        f"  [OK] BlastBeat: traditional={kick_count + snare_count} beats, hammer={hammer_snares} snares"
    )


def test_jazz_ride_template():
    """Test JazzRidePattern template."""
    print("Testing JazzRidePattern template...")

    template = JazzRidePattern(swing_ratio=0.33, accent_pattern="standard")

    pattern = TemplateComposer("test_jazz").add(template).build(bars=1)

    ride_count = sum(
        1 for b in pattern.beats if b.instrument == DrumInstrument.RIDE
    )

    # Should have ride cymbal hits on swing pattern
    assert ride_count > 0, f"Expected ride hits, got {ride_count}"
    assert ride_count <= 12, f"Too many ride hits: {ride_count}"

    print(f"  [OK] JazzRidePattern: {ride_count} ride hits with swing")


def test_funk_ghost_notes_template():
    """Test FunkGhostNotes template."""
    print("Testing FunkGhostNotes template...")

    template = FunkGhostNotes(
        density=0.7,
        emphasize_one=True,
        main_snare_positions=[1.0, 3.0],
    )

    pattern = TemplateComposer("test_funk").add(template).build(bars=1)

    snare_count = sum(
        1 for b in pattern.beats if b.instrument == DrumInstrument.SNARE
    )
    ghost_count = sum(
        1
        for b in pattern.beats
        if b.instrument == DrumInstrument.SNARE and b.ghost_note
    )

    # Should have main snares + ghost notes
    assert snare_count >= 2, f"Expected at least 2 snares, got {snare_count}"
    assert ghost_count > 0, f"Expected ghost notes, got {ghost_count}"

    print(
        f"  [OK] FunkGhostNotes: {snare_count} total snares, {ghost_count} ghost notes"
    )


def test_crash_accents_template():
    """Test CrashAccents template."""
    print("Testing CrashAccents template...")

    template = CrashAccents(positions=[0.0, 2.0], use_china=False)

    pattern = TemplateComposer("test_crash").add(template).build(bars=1)

    crash_count = sum(
        1 for b in pattern.beats if b.instrument == DrumInstrument.CRASH
    )

    assert crash_count == 2, f"Expected 2 crashes, got {crash_count}"

    print(f"  [OK] CrashAccents: {crash_count} crash hits")


def test_tom_fill_template():
    """Test TomFill template."""
    print("Testing TomFill template...")

    template = TomFill(
        pattern="descending", subdivision=TIMING.SIXTEENTH, start_position=3.0
    )

    pattern = TemplateComposer("test_fill").add(template).build(bars=1)

    tom_count = sum(
        1
        for b in pattern.beats
        if b.instrument in [DrumInstrument.MID_TOM, DrumInstrument.FLOOR_TOM]
    )

    assert tom_count > 0, f"Expected tom fills, got {tom_count}"

    print(f"  [OK] TomFill: {tom_count} tom hits")


def test_template_composition():
    """Test combining multiple templates."""
    print("Testing template composition...")

    pattern = (
        TemplateComposer("complex_pattern")
        .add(
            BasicGroove(
                kick_positions=[0.0, 2.0],
                snare_positions=[1.0, 3.0],
            )
        )
        .add(CrashAccents(positions=[0.0]))
        .add(TomFill(pattern="descending", start_position=3.5))
        .build(bars=1, complexity=0.7)
    )

    # Should have beats from all templates
    total_beats = len(pattern.beats)

    # At minimum: 2 kicks + 2 snares + 8 hihats + 1 crash + tom fills
    assert total_beats >= 13, f"Expected at least 13 beats, got {total_beats}"

    # Check we have variety
    instruments = {b.instrument for b in pattern.beats}
    assert (
        len(instruments) >= 4
    ), f"Expected at least 4 instrument types, got {len(instruments)}"

    print(
        f"  [OK] Composition: {total_beats} beats, {len(instruments)} instruments"
    )


def test_convenience_functions():
    """Test convenience pattern creation functions."""
    print("Testing convenience functions...")

    # Basic rock pattern
    rock = create_basic_rock_pattern("rock_test", bars=2, complexity=0.5)

    assert rock is not None
    assert len(rock.beats) > 0
    # Duration is based on max beat position, not bars parameter
    # With bars=2, we expect beats up to position 8.0
    max_pos = max(b.position for b in rock.beats)
    assert max_pos >= 4.0, f"Expected beats in bar 2, max position: {max_pos}"

    # Metal pattern
    metal = create_metal_pattern(
        "metal_test", bars=1, complexity=0.8, use_double_bass=True
    )

    assert metal is not None
    assert len(metal.beats) > 0

    # Metal with double bass should have more kicks
    kick_count = sum(
        1 for b in metal.beats if b.instrument == DrumInstrument.KICK
    )
    assert (
        kick_count >= 16
    ), f"Expected many kicks in metal pattern, got {kick_count}"

    print(
        f"  [OK] Convenience: rock={len(rock.beats)} beats, metal={len(metal.beats)} beats"
    )


def test_multi_bar_patterns():
    """Test patterns across multiple bars."""
    print("Testing multi-bar patterns...")

    pattern = (
        TemplateComposer("multibar")
        .add(BasicGroove())
        .add(CrashAccents(positions=[0.0]))
        .build(bars=4, complexity=0.6)
    )

    # Should span approximately 4 bars (may be slightly over due to fills)
    duration = pattern.duration_bars()
    assert 3.9 <= duration <= 4.2, f"Expected ~4 bars, got {duration}"

    # Should have beats across all bars
    max_position = max(b.position for b in pattern.beats)
    assert (
        max_position >= 12.0
    ), f"Expected beats up to bar 4, max position: {max_position}"

    print(f"  [OK] Multi-bar: {duration} bars, max position {max_position:.1f}")


def test_template_with_parameters():
    """Test that templates respect complexity and dynamics parameters."""
    print("Testing parameter handling...")

    # Low complexity
    low = (
        TemplateComposer("low_complexity")
        .add(BasicGroove())
        .build(bars=1, complexity=0.2, dynamics=0.3)
    )

    # High complexity
    high = (
        TemplateComposer("high_complexity")
        .add(BasicGroove())
        .build(bars=1, complexity=0.9, dynamics=0.9)
    )

    # High complexity should have higher velocities
    low_velocities = [b.velocity for b in low.beats]
    high_velocities = [b.velocity for b in high.beats]

    avg_low = sum(low_velocities) / len(low_velocities)
    avg_high = sum(high_velocities) / len(high_velocities)

    assert (
        avg_high > avg_low
    ), f"Expected higher avg velocity for high complexity: {avg_high} vs {avg_low}"

    print(f"  [OK] Parameters: low_avg={avg_low:.1f}, high_avg={avg_high:.1f}")


if __name__ == "__main__":
    print("=" * 60)
    print("Pattern Template System Tests")
    print("=" * 60)

    test_basic_groove_template()
    test_double_bass_template()
    test_blast_beat_template()
    test_jazz_ride_template()
    test_funk_ghost_notes_template()
    test_crash_accents_template()
    test_tom_fill_template()
    test_template_composition()
    test_convenience_functions()
    test_multi_bar_patterns()
    test_template_with_parameters()

    print("=" * 60)
    print("All pattern template tests passed!")
    print("=" * 60)
