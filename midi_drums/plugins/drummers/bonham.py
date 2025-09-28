"""
John Bonham drummer plugin.

Implements John Bonham's signature drumming techniques based on research.
Known for triplet-based playing, "behind the beat" timing, and following
guitar riffs rather than bass lines. Master of the legendary Led Zeppelin sound.
"""

import random

from midi_drums.models.pattern import Beat, DrumInstrument, Pattern
from midi_drums.models.song import Fill
from midi_drums.plugins.base import DrummerPlugin

# Type annotations use built-in list for Python 3.9+


class BonhamPlugin(DrummerPlugin):
    """John Bonham drummer style plugin.

    Characteristics:
    - Triplet-based rhythmic vocabulary (sixtuplets)
    - "Behind the beat" timing and swing feel
    - Following guitar riffs instead of bass lines
    - Complex time signature interplay
    - Big, powerful sound with heavy kick emphasis
    - Masterful use of space and dynamics
    """

    @property
    def drummer_name(self) -> str:
        return "bonham"

    @property
    def compatible_genres(self) -> list[str]:
        return ["rock", "metal", "blues", "hard_rock"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply John Bonham's signature style to a pattern.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Bonham's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_bonham"

        # 1. Apply behind-the-beat timing
        styled_pattern = self._apply_behind_beat_timing(styled_pattern)

        # 2. Add triplet-based fills and variations
        styled_pattern = self._add_triplet_vocabulary(styled_pattern)

        # 3. Enhance kick drum patterns (following guitar)
        styled_pattern = self._enhance_kick_patterns(styled_pattern)

        # 4. Add sixtuplet fills
        styled_pattern = self._add_sixtuplet_fills(styled_pattern)

        # 5. Apply Bonham's dynamics and accents
        styled_pattern = self._apply_bonham_dynamics(styled_pattern)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return John Bonham's signature fill patterns."""
        fills = []

        # Famous "Moby Dick" style triplet fill
        moby_dick_fill = Fill(
            pattern=self._create_moby_dick_fill(),
            trigger_probability=0.9,
            section_position="end",
        )
        fills.append(moby_dick_fill)

        # Sixtuplet fill (6 notes in place of 4)
        sixtuplet_fill = Fill(
            pattern=self._create_sixtuplet_fill(),
            trigger_probability=0.8,
            section_position="middle",
        )
        fills.append(sixtuplet_fill)

        # "Good Times Bad Times" triplet pattern
        gtbt_fill = Fill(
            pattern=self._create_gtbt_triplet_fill(),
            trigger_probability=0.7,
            section_position="start",
        )
        fills.append(gtbt_fill)

        # Hand drumming inspired fill
        hand_fill = Fill(
            pattern=self._create_hand_drumming_fill(),
            trigger_probability=0.6,
            section_position="end",
        )
        fills.append(hand_fill)

        return fills

    def _apply_behind_beat_timing(self, pattern: Pattern) -> Pattern:
        """Apply Bonham's signature 'behind the beat' timing."""
        # Slightly delay snare hits to create laid-back feel
        behind_beat_offset = 0.02  # Small delay for behind-beat feel

        new_beats = []
        for beat in pattern.beats:
            if beat.instrument == DrumInstrument.SNARE:
                # Apply behind-beat timing to snare
                new_beat = Beat(
                    position=beat.position + behind_beat_offset,
                    instrument=beat.instrument,
                    velocity=min(
                        127, beat.velocity + random.randint(5, 15)
                    ),  # More power
                    duration=beat.duration,
                )
                new_beats.append(new_beat)
            else:
                new_beats.append(beat)

        pattern.beats = new_beats
        return pattern

    def _add_triplet_vocabulary(self, pattern: Pattern) -> Pattern:
        """Add Bonham's triplet-based rhythmic vocabulary."""
        new_beats = list(pattern.beats)

        # Find strong beats to add triplet patterns
        strong_beats = [0.0, 1.0, 2.0, 3.0]  # Downbeats

        for beat_pos in strong_beats:
            if random.random() < 0.2:  # 20% chance per strong beat
                # Add triplet pattern: thump-pe-da
                triplet_subdivision = 1.0 / 3.0

                # Kick on 1
                new_beats.append(
                    Beat(
                        position=beat_pos,
                        instrument=DrumInstrument.KICK,
                        velocity=110,
                        duration=0.15,
                    )
                )

                # Snare on 2nd triplet
                new_beats.append(
                    Beat(
                        position=beat_pos + triplet_subdivision,
                        instrument=DrumInstrument.SNARE,
                        velocity=95,
                        duration=0.1,
                    )
                )

                # Tom on 3rd triplet
                new_beats.append(
                    Beat(
                        position=beat_pos + (2 * triplet_subdivision),
                        instrument=DrumInstrument.FLOOR_TOM,
                        velocity=100,
                        duration=0.1,
                    )
                )

        pattern.beats = new_beats
        return pattern

    def _enhance_kick_patterns(self, pattern: Pattern) -> Pattern:
        """Enhance kick patterns to follow guitar-like riffs."""
        # Add syncopated kick patterns that "follow the guitar"
        new_beats = list(pattern.beats)

        # Add off-beat kicks for guitar-following feel
        off_beat_positions = [0.75, 1.75, 2.75, 3.75]  # Between beats

        for pos in off_beat_positions:
            if random.random() < 0.3:  # 30% chance
                new_beats.append(
                    Beat(
                        position=pos,
                        instrument=DrumInstrument.KICK,
                        velocity=min(127, 105 + random.randint(-5, 10)),
                        duration=0.1,
                    )
                )

        pattern.beats = new_beats
        return pattern

    def _add_sixtuplet_fills(self, pattern: Pattern) -> Pattern:
        """Add Bonham's signature sixtuplet fills (6 notes in place of 4)."""
        # Find spots for sixtuplet fills
        fill_spots = []

        for beat in pattern.beats:
            if (
                beat.instrument == DrumInstrument.SNARE
                and beat.position % 2.0 == 0  # On strong beats
                and random.random() < 0.15
            ):  # 15% chance
                fill_spots.append(beat.position + 0.5)  # After the snare

        new_beats = list(pattern.beats)

        for spot in fill_spots:
            # Create 6-note sixtuplet pattern
            sixtuplet_duration = 0.5 / 6  # 6 notes in half beat

            instruments = [
                DrumInstrument.MID_TOM,
                DrumInstrument.MID_TOM,
                DrumInstrument.FLOOR_TOM,
                DrumInstrument.FLOOR_TOM,
                DrumInstrument.KICK,
                DrumInstrument.SNARE,
            ]

            for i, instrument in enumerate(instruments):
                sixtuplet_position = spot + (i * sixtuplet_duration)
                velocity = 85 + (i * 5)  # Building intensity

                new_beats.append(
                    Beat(
                        position=sixtuplet_position,
                        instrument=instrument,
                        velocity=velocity,
                        duration=0.05,
                    )
                )

        pattern.beats = new_beats
        return pattern

    def _apply_bonham_dynamics(self, pattern: Pattern) -> Pattern:
        """Apply Bonham's signature dynamics and power."""
        for beat in pattern.beats:
            if beat.instrument == DrumInstrument.KICK:
                # Powerful, driving kick drum
                beat.velocity = min(127, beat.velocity + 15)
            elif beat.instrument == DrumInstrument.SNARE:
                # Big backbeat snare
                beat.velocity = min(127, beat.velocity + 10)
            elif beat.instrument in [
                DrumInstrument.MID_TOM,
                DrumInstrument.FLOOR_TOM,
            ]:
                # Prominent tom sounds
                beat.velocity = min(127, beat.velocity + 8)

        return pattern

    def _create_moby_dick_fill(self) -> Pattern:
        """Create Moby Dick inspired triplet fill."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("bonham_moby_dick")

        # Famous triplet pattern around the kit
        builder.kick(0.0, 110)
        builder.pattern.add_beat(1 / 3, DrumInstrument.MID_TOM, 105)
        builder.pattern.add_beat(2 / 3, DrumInstrument.FLOOR_TOM, 108)

        builder.snare(1.0, 115)
        builder.kick(1.33, 108)
        builder.pattern.add_beat(1.66, DrumInstrument.MID_TOM, 100)

        return builder.build()

    def _create_sixtuplet_fill(self) -> Pattern:
        """Create signature sixtuplet fill pattern."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("bonham_sixtuplet")

        # 6 notes in place of 4 16th notes
        subdivision = 1.0 / 6
        instruments = [
            DrumInstrument.SNARE,
            DrumInstrument.MID_TOM,
            DrumInstrument.MID_TOM,
            DrumInstrument.FLOOR_TOM,
            DrumInstrument.FLOOR_TOM,
            DrumInstrument.KICK,
        ]

        for i, instrument in enumerate(instruments):
            position = i * subdivision
            velocity = min(127, 90 + (i * 4))
            builder.pattern.add_beat(position, instrument, velocity)

        return builder.build()

    def _create_gtbt_triplet_fill(self) -> Pattern:
        """Create 'Good Times Bad Times' triplet pattern."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("bonham_gtbt_triplets")

        # Famous opening triplet pattern
        builder.kick(0.0, 110)
        builder.kick(1 / 3, 108)
        builder.kick(2 / 3, 105)

        # Follow with snare accent
        builder.snare(1.0, 115)

        return builder.build()

    def _create_hand_drumming_fill(self) -> Pattern:
        """Create hand drumming inspired fill (Moby Dick live versions)."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("bonham_hand_drumming")

        # Simulate hand drumming with varied tom hits
        positions = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75]
        instruments = [
            DrumInstrument.MID_TOM,
            DrumInstrument.FLOOR_TOM,
            DrumInstrument.MID_TOM,
            DrumInstrument.SNARE,
            DrumInstrument.FLOOR_TOM,
            DrumInstrument.MID_TOM,
            DrumInstrument.SNARE,
            DrumInstrument.FLOOR_TOM,
        ]

        for pos, inst in zip(positions, instruments, strict=False):
            # Vary velocity for hand-like feel
            velocity = min(127, 85 + random.randint(-10, 20))
            builder.pattern.add_beat(pos, inst, velocity)

        return builder.build()
