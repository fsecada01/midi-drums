"""
Gene Hoglan "The Atomic Clock" drummer plugin.

Implements Gene Hoglan's signature drumming techniques based on research.
Known for mechanical precision, complex double bass patterns, blast beat
mastery, and progressive fill complexity.
"""

import random

from midi_drums.models.pattern import Beat, DrumInstrument, Pattern
from midi_drums.models.song import Fill
from midi_drums.plugins.base import DrummerPlugin

# Type annotations use built-in list for Python 3.9+


class HoglanPlugin(DrummerPlugin):
    """Gene Hoglan 'The Atomic Clock' drummer style plugin.

    Characteristics:
    - Machine-like precision ("The Atomic Clock")
    - Complex double bass patterns and kick triplets
    - Blast beat variations with hand-foot coordination
    - Progressive fill complexity (builds throughout song)
    - Dual ride cymbal usage
    - 32nd-note kick flurries
    - Technical precision at extreme tempos
    """

    @property
    def drummer_name(self) -> str:
        return "hoglan"

    @property
    def compatible_genres(self) -> list[str]:
        return ["metal", "death", "thrash", "progressive"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Gene Hoglan's signature style to a pattern.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Hoglan's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_hoglan"

        # 1. Apply atomic clock precision (minimal humanization)
        styled_pattern = self._apply_atomic_precision(styled_pattern)

        # 2. Enhance double bass patterns
        styled_pattern = self._add_double_bass_complexity(styled_pattern)

        # 3. Add kick triplets where appropriate
        styled_pattern = self._add_kick_triplets(styled_pattern)

        # 4. Apply blast beat variations if applicable
        if self._is_blast_pattern(styled_pattern):
            styled_pattern = self._apply_blast_variations(styled_pattern)

        # 5. Use dual ride technique
        styled_pattern = self._apply_dual_ride_technique(styled_pattern)

        # 6. Add 32nd note kick flurries
        styled_pattern = self._add_kick_flurries(styled_pattern)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Gene Hoglan's signature fill patterns.

        Based on his progressive complexity approach and technical mastery.
        """
        fills = []

        # Simple kick triplet fill (first occurrence)
        simple_fill = Fill(
            pattern=self._create_simple_kick_triplet_fill(),
            trigger_probability=0.8,
            section_position="end",
        )
        fills.append(simple_fill)

        # Advanced kick triplet with hands (second occurrence)
        advanced_fill = Fill(
            pattern=self._create_advanced_kick_triplet_fill(),
            trigger_probability=0.9,
            section_position="end",
        )
        fills.append(advanced_fill)

        # "Throwing it all against the wall" fill (final occurrence)
        complex_fill = Fill(
            pattern=self._create_atomic_chaos_fill(),
            trigger_probability=1.0,
            section_position="end",
        )
        fills.append(complex_fill)

        # 32nd note kick flurry
        flurry_fill = Fill(
            pattern=self._create_32nd_kick_flurry(),
            trigger_probability=0.7,
            section_position="middle",
        )
        fills.append(flurry_fill)

        return fills

    def _apply_atomic_precision(self, pattern: Pattern) -> Pattern:
        """Apply mechanical timing precision - minimal humanization."""
        precise_beats = []

        for beat in pattern.beats:
            # Reduce timing variations to near-zero (atomic clock precision)
            precise_beat = Beat(
                position=round(
                    beat.position, 3
                ),  # Quantize to precise subdivisions
                instrument=beat.instrument,
                velocity=beat.velocity,
                duration=beat.duration,
            )
            precise_beats.append(precise_beat)

        pattern.beats = precise_beats
        return pattern

    def _add_double_bass_complexity(self, pattern: Pattern) -> Pattern:
        """Add Gene Hoglan's signature double bass complexity."""
        # Find kick drum beats and add complementary patterns
        kick_beats = [
            b for b in pattern.beats if b.instrument == DrumInstrument.KICK
        ]

        if not kick_beats:
            return pattern

        new_beats = []

        for beat in pattern.beats:
            new_beats.append(beat)

            # Add double bass fills between existing kicks
            if beat.instrument == DrumInstrument.KICK:
                # Add quick double stroke (Hoglan's signature)
                if random.random() < 0.3:  # 30% chance
                    double_stroke = Beat(
                        position=beat.position + 0.125,  # 32nd note later
                        instrument=DrumInstrument.KICK,
                        velocity=beat.velocity - 10,  # Slightly softer
                        duration=0.1,
                    )
                    new_beats.append(double_stroke)

        pattern.beats = new_beats
        return pattern

    def _add_kick_triplets(self, pattern: Pattern) -> Pattern:
        """Add Hoglan's famous kick drum triplets."""
        # Find appropriate spots for kick triplets (usually on strong beats)
        triplet_spots = []

        for beat in pattern.beats:
            if (
                beat.instrument == DrumInstrument.KICK
                and beat.position % 1.0 == 0  # On downbeats
                and random.random() < 0.2
            ):  # 20% chance
                triplet_spots.append(beat.position)

        new_beats = list(pattern.beats)

        for spot in triplet_spots:
            # Create kick triplet pattern: kick-kick-kick with precise timing
            triplet_subdivision = 1.0 / 3.0  # Triplet subdivision

            for i in range(3):
                triplet_position = spot + (i * triplet_subdivision)
                triplet_beat = Beat(
                    position=triplet_position,
                    instrument=DrumInstrument.KICK,
                    velocity=105 + (i * 5),  # Increasing velocity
                    duration=0.1,
                )
                new_beats.append(triplet_beat)

        pattern.beats = new_beats
        return pattern

    def _is_blast_pattern(self, pattern: Pattern) -> bool:
        """Determine if pattern is suitable for blast beat treatment."""
        # Look for fast, repetitive snare patterns
        snare_beats = [
            b for b in pattern.beats if b.instrument == DrumInstrument.SNARE
        ]

        if len(snare_beats) < 4:
            return False

        # Check for regular intervals (blast beat characteristic)
        intervals = []
        for i in range(1, len(snare_beats)):
            intervals.append(
                snare_beats[i].position - snare_beats[i - 1].position
            )

        # If most intervals are similar and fast, it's blast-worthy
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            return avg_interval <= 0.25  # 16th notes or faster

        return False

    def _apply_blast_variations(self, pattern: Pattern) -> Pattern:
        """Apply Hoglan's blast beat variations with hand-foot coordination."""
        new_beats = []

        for beat in pattern.beats:
            new_beats.append(beat)

            # Add complementary blast elements
            if beat.instrument == DrumInstrument.SNARE:
                # Add kick on every snare (classic blast)
                kick_beat = Beat(
                    position=beat.position,
                    instrument=DrumInstrument.KICK,
                    velocity=100,
                    duration=0.1,
                )
                new_beats.append(kick_beat)

                # Add china cymbal accents (Hoglan signature)
                if random.random() < 0.15:  # 15% chance
                    china_beat = Beat(
                        position=beat.position,
                        instrument=DrumInstrument.CHINA,
                        velocity=110,
                        duration=0.2,
                    )
                    new_beats.append(china_beat)

        pattern.beats = new_beats
        return pattern

    def _apply_dual_ride_technique(self, pattern: Pattern) -> Pattern:
        """Apply Hoglan's dual ride cymbal technique."""
        ride_beats = [
            b for b in pattern.beats if b.instrument == DrumInstrument.RIDE
        ]

        if not ride_beats:
            return pattern

        new_beats = []

        for beat in pattern.beats:
            if beat.instrument == DrumInstrument.RIDE:
                # Alternate between main ride and second ride
                if random.random() < 0.3:  # 30% to second ride
                    # Use crash as second ride (mapping limitation)
                    new_beat = Beat(
                        position=beat.position,
                        instrument=DrumInstrument.CRASH,
                        velocity=beat.velocity - 5,
                        duration=beat.duration,
                    )
                    new_beats.append(new_beat)
                else:
                    new_beats.append(beat)
            else:
                new_beats.append(beat)

        pattern.beats = new_beats
        return pattern

    def _add_kick_flurries(self, pattern: Pattern) -> Pattern:
        """Add Hoglan's signature 32nd note kick flurries."""
        # Find spots for flurries (usually before strong beats)
        flurry_spots = []

        for beat in pattern.beats:
            if (
                beat.instrument == DrumInstrument.SNARE
                and beat.position % 2.0 == 0  # On strong beats
                and random.random() < 0.1
            ):  # 10% chance
                flurry_spots.append(beat.position - 0.5)  # Half beat before

        new_beats = list(pattern.beats)

        for spot in flurry_spots:
            # Create 32nd note flurry (4 kicks in 1/4 beat)
            subdivision = 0.25 / 4  # 32nd notes

            for i in range(4):
                flurry_position = spot + (i * subdivision)
                flurry_beat = Beat(
                    position=flurry_position,
                    instrument=DrumInstrument.KICK,
                    velocity=95 + (i * 3),  # Building intensity
                    duration=0.05,
                )
                new_beats.append(flurry_beat)

        pattern.beats = new_beats
        return pattern

    def _create_simple_kick_triplet_fill(self) -> Pattern:
        """Create a simple kick triplet fill pattern."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("hoglan_simple_triplets")

        # Basic kick triplet on beat 1
        builder.kick(0.0, 105)
        builder.kick(1 / 3, 108)
        builder.kick(2 / 3, 110)

        # Simple snare on 2 and 4
        builder.snare(1.0, 105)
        builder.snare(3.0, 105)

        return builder.build()

    def _create_advanced_kick_triplet_fill(self) -> Pattern:
        """Create advanced kick triplet with hand coordination."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("hoglan_advanced_triplets")

        # Complex kick triplets with tom accents
        builder.kick(0.0, 105)
        builder.pattern.add_beat(0.25, DrumInstrument.MID_TOM, 100)
        builder.kick(1 / 3, 108)
        builder.pattern.add_beat(0.5, DrumInstrument.MID_TOM, 100)
        builder.kick(2 / 3, 110)
        builder.pattern.add_beat(0.75, DrumInstrument.FLOOR_TOM, 100)

        # Snare and tom combination
        builder.snare(1.0, 110)
        builder.kick(1.25, 105).kick(1.5, 108)

        return builder.build()

    def _create_atomic_chaos_fill(self) -> Pattern:
        """Create maximum complexity 'atomic chaos' fill."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("hoglan_atomic_chaos")

        # Rapid-fire kick patterns
        subdivisions = [0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]
        for i, time in enumerate(subdivisions):
            builder.kick(time, 100 + (i * 2))

            # Add tom hits for complexity
            if i % 2 == 0:
                builder.pattern.add_beat(
                    time + 0.0625, DrumInstrument.MID_TOM, 95
                )
            else:
                builder.pattern.add_beat(
                    time + 0.0625, DrumInstrument.FLOOR_TOM, 95
                )

        # Crash accent at the end
        builder.crash(1.0, 120)

        return builder.build()

    def _create_32nd_kick_flurry(self) -> Pattern:
        """Create signature 32nd note kick flurry."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("hoglan_32nd_flurry")

        # 32nd note kick pattern (16 notes in one beat)
        subdivision = 1.0 / 16

        for i in range(16):
            position = i * subdivision
            velocity = 90 + (i % 4) * 5  # Accented every 4th note
            builder.kick(position, velocity)

        return builder.build()
