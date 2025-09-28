"""
Dave Weckl drummer plugin.

Implements Dave Weckl's signature drumming techniques based on research.
Known for fusion jazz mastery, linear playing, sophisticated coordination,
and the famous "Weckl 9" linear patterns. One of the most influential
fusion drummers.
"""

import random

from midi_drums.models.pattern import Beat, DrumInstrument, Pattern
from midi_drums.models.song import Fill
from midi_drums.plugins.base import DrummerPlugin

# Type annotations use built-in list for Python 3.9+


class WecklPlugin(DrummerPlugin):
    """Dave Weckl drummer style plugin.

    Characteristics:
    - Linear playing (no limbs play simultaneously)
    - Sophisticated jazz fusion patterns
    - Complex hand-foot coordination
    - Ghost notes with session finesse
    - Dynamic control and musical sophistication
    - "Weckl 9" and other signature linear patterns
    """

    @property
    def drummer_name(self) -> str:
        return "weckl"

    @property
    def compatible_genres(self) -> list[str]:
        return ["jazz", "fusion", "funk", "rock"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Dave Weckl's signature style to a pattern.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Weckl's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_weckl"

        # 1. Apply linear playing concepts
        styled_pattern = self._apply_linear_playing(styled_pattern)

        # 2. Add sophisticated hand-foot coordination
        styled_pattern = self._add_coordination_patterns(styled_pattern)

        # 3. Apply fusion ghost note vocabulary
        styled_pattern = self._add_fusion_ghost_notes(styled_pattern)

        # 4. Add dynamic control and musicality
        styled_pattern = self._apply_dynamic_control(styled_pattern)

        # 5. Insert Weckl's signature linear fills
        styled_pattern = self._add_weckl_linear_fills(styled_pattern)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Dave Weckl's signature fill patterns."""
        fills = []

        # Famous "Weckl 9" pattern
        weckl_9_fill = Fill(
            pattern=self._create_weckl_9_pattern(),
            trigger_probability=0.9,
            section_position="end",
        )
        fills.append(weckl_9_fill)

        # Linear fusion fill
        linear_fill = Fill(
            pattern=self._create_linear_fusion_fill(),
            trigger_probability=0.8,
            section_position="middle",
        )
        fills.append(linear_fill)

        # Sophisticated ghost note pattern
        ghost_pattern_fill = Fill(
            pattern=self._create_sophisticated_ghost_pattern(),
            trigger_probability=0.7,
            section_position="start",
        )
        fills.append(ghost_pattern_fill)

        # Complex coordination showcase
        coordination_fill = Fill(
            pattern=self._create_coordination_showcase(),
            trigger_probability=0.6,
            section_position="end",
        )
        fills.append(coordination_fill)

        return fills

    def _apply_linear_playing(self, pattern: Pattern) -> Pattern:
        """Apply Weckl's linear playing concepts (no simultaneous limbs)."""
        # Reorganize beats to avoid simultaneous hits
        position_groups = {}

        # Group beats by position
        for beat in pattern.beats:
            pos = round(beat.position, 3)  # Round for grouping
            if pos not in position_groups:
                position_groups[pos] = []
            position_groups[pos].append(beat)

        new_beats = []

        for _pos, beats in position_groups.items():
            if len(beats) > 1:
                # Apply linear concept - spread simultaneous hits
                for i, beat in enumerate(beats):
                    # Micro-timing adjustment to create linear flow
                    offset = i * 0.02  # 20ms separation
                    linear_beat = Beat(
                        position=beat.position + offset,
                        instrument=beat.instrument,
                        velocity=beat.velocity,
                        duration=beat.duration,
                    )
                    new_beats.append(linear_beat)
            else:
                new_beats.extend(beats)

        pattern.beats = new_beats
        return pattern

    def _add_coordination_patterns(self, pattern: Pattern) -> Pattern:
        """Add sophisticated hand-foot coordination patterns."""
        new_beats = list(pattern.beats)

        # Add coordination patterns between snare and kick
        coordination_spots = [0.75, 1.75, 2.75]  # Between main beats

        for spot in coordination_spots:
            if random.random() < 0.4:  # 40% chance
                # Hand-foot combination (linear)
                new_beats.append(
                    Beat(
                        position=spot,
                        instrument=DrumInstrument.SNARE,
                        velocity=65,  # Medium accent
                        duration=0.05,
                    )
                )

                new_beats.append(
                    Beat(
                        position=spot + 0.125,  # 32nd note later
                        instrument=DrumInstrument.KICK,
                        velocity=70,
                        duration=0.08,
                    )
                )

        pattern.beats = new_beats
        return pattern

    def _add_fusion_ghost_notes(self, pattern: Pattern) -> Pattern:
        """Add Weckl's sophisticated fusion ghost note vocabulary."""
        new_beats = list(pattern.beats)

        # Add complex ghost note patterns
        ghost_positions = [
            0.125,
            0.1875,
            0.3125,
            0.4375,
            0.5625,
            0.6875,
            0.8125,
            0.9375,
            1.125,
            1.1875,
            1.3125,
            1.4375,
            1.5625,
            1.6875,
            1.8125,
            1.9375,
            2.125,
            2.1875,
            2.3125,
            2.4375,
            2.5625,
            2.6875,
            2.8125,
            2.9375,
            3.125,
            3.1875,
            3.3125,
            3.4375,
            3.5625,
            3.6875,
            3.8125,
            3.9375,
        ]

        for pos in ghost_positions:
            # Check for conflicts
            conflict = any(
                abs(beat.position - pos) < 0.05 for beat in pattern.beats
            )

            if not conflict and random.random() < 0.25:  # 25% chance
                # Sophisticated ghost note with varied dynamics
                velocity = 30 + random.randint(0, 25)
                ghost = Beat(
                    position=pos,
                    instrument=DrumInstrument.SNARE,
                    velocity=velocity,
                    duration=0.03,
                    ghost_note=True,
                )
                new_beats.append(ghost)

        pattern.beats = new_beats
        return pattern

    def _apply_dynamic_control(self, pattern: Pattern) -> Pattern:
        """Apply Weckl's sophisticated dynamic control."""
        # Create dynamic arcs and musical phrasing
        for _i, beat in enumerate(pattern.beats):
            # Apply musical dynamics based on position
            beat_in_measure = beat.position % 4.0

            if beat.instrument == DrumInstrument.SNARE:
                if not beat.ghost_note:
                    # Main snare hits with musical dynamics
                    if beat_in_measure in [1.0, 3.0]:  # Backbeat
                        beat.velocity = min(127, beat.velocity + 10)
                    else:
                        beat.velocity = max(60, beat.velocity - 5)

            elif beat.instrument == DrumInstrument.KICK:
                # Subtle kick dynamics
                beat.velocity = min(115, beat.velocity + random.randint(-5, 8))

        return pattern

    def _add_weckl_linear_fills(self, pattern: Pattern) -> Pattern:
        """Add Weckl's signature linear fill patterns."""
        # Find spots for linear fills
        fill_spots = []

        for beat in pattern.beats:
            if (
                beat.instrument == DrumInstrument.SNARE
                and beat.position % 2.0 == 0  # Strong beats
                and random.random() < 0.2
            ):  # 20% chance
                fill_spots.append(beat.position + 0.5)

        new_beats = list(pattern.beats)

        for spot in fill_spots:
            # Create mini linear fill
            linear_sequence = [
                (0.0, DrumInstrument.SNARE, 85),
                (0.125, DrumInstrument.KICK, 80),
                (0.25, DrumInstrument.MID_TOM, 82),
                (0.375, DrumInstrument.KICK, 78),
            ]

            for offset, instrument, velocity in linear_sequence:
                fill_position = spot + offset
                new_beats.append(
                    Beat(
                        position=fill_position,
                        instrument=instrument,
                        velocity=velocity,
                        duration=0.06,
                    )
                )

        pattern.beats = new_beats
        return pattern

    def _create_weckl_9_pattern(self) -> Pattern:
        """Create the famous 'Weckl 9' linear pattern."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("weckl_9_linear")

        # The Weckl 9: 3 with hands, 2 with feet, 2 with hands, 2 with feet

        # First 3 notes with hands
        builder.snare(0.0, 90)
        builder.pattern.add_beat(0.1, DrumInstrument.MID_TOM, 85)
        builder.snare(0.2, 88)

        # Next 2 notes with feet
        builder.kick(0.3, 85)
        builder.kick(0.4, 82)

        # Next 2 notes with hands
        builder.pattern.add_beat(0.5, DrumInstrument.FLOOR_TOM, 87)
        builder.snare(0.6, 90)

        # Final 2 notes with feet
        builder.kick(0.7, 80)
        builder.kick(0.8, 85)

        return builder.build()

    def _create_linear_fusion_fill(self) -> Pattern:
        """Create sophisticated linear fusion fill."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("weckl_linear_fusion")

        # Complex linear pattern around the kit
        sequence = [
            (0.0, DrumInstrument.SNARE, 95),
            (0.125, DrumInstrument.KICK, 85),
            (0.25, DrumInstrument.MID_TOM, 88),
            (0.375, DrumInstrument.KICK, 82),
            (0.5, DrumInstrument.FLOOR_TOM, 90),
            (0.625, DrumInstrument.SNARE, 75),  # Ghost
            (0.75, DrumInstrument.KICK, 88),
            (0.875, DrumInstrument.MID_TOM, 85),
            (1.0, DrumInstrument.CRASH, 100),  # Resolution
        ]

        for pos, instrument, velocity in sequence:
            builder.pattern.add_beat(pos, instrument, velocity)

        return builder.build()

    def _create_sophisticated_ghost_pattern(self) -> Pattern:
        """Create sophisticated ghost note pattern."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("weckl_ghost_sophistication")

        # Main pattern with complex ghost note interplay
        builder.kick(0.0, 95)
        builder.snare(1.0, 105)  # Strong backbeat

        # Sophisticated ghost note placement
        ghost_positions = [
            0.1875,
            0.4375,
            0.5625,
            0.8125,
            1.1875,
            1.4375,
            1.6875,
        ]
        velocities = [35, 42, 38, 45, 40, 37, 43]

        for pos, vel in zip(ghost_positions, velocities, strict=False):
            builder.pattern.add_beat(pos, DrumInstrument.SNARE, vel)

        return builder.build()

    def _create_coordination_showcase(self) -> Pattern:
        """Create complex hand-foot coordination showcase."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("weckl_coordination")

        # Advanced coordination pattern
        builder.kick(0.0, 90)
        builder.snare(0.1667, 85)  # Triplet feel
        builder.kick(0.3333, 88)
        builder.pattern.add_beat(0.5, DrumInstrument.MID_TOM, 82)
        builder.kick(0.6667, 85)
        builder.snare(0.8333, 90)
        builder.pattern.add_beat(1.0, DrumInstrument.FLOOR_TOM, 95)

        return builder.build()
