"""
Dennis Chambers drummer plugin.

Implements Dennis Chambers' signature drumming techniques based on research.
Known for funk mastery with Parliament-Funkadelic, incredible fast chops,
jaw-dropping technical prowess, and the ability to play in the pocket
while executing complex passages. The ultimate funk drummer with versatility.
"""

import random

from midi_drums.models.pattern import Beat, DrumInstrument, Pattern
from midi_drums.models.song import Fill
from midi_drums.plugins.base import DrummerPlugin

# Type annotations use built-in list for Python 3.9+


class ChambersPlugin(DrummerPlugin):
    """Dennis Chambers drummer style plugin.

    Characteristics:
    - Ultimate funk pocket and groove
    - Incredible fast chops and triplets on bass drum
    - Ability to stretch in and out of pocket
    - Parliament-Funkadelic groove foundation
    - Jaw-dropping technical prowess with musicality
    - Rapid-fire double bass with machine precision
    - Versatility across funk, fusion, jazz, rock
    - Infectious groove that enhances any music
    """

    @property
    def drummer_name(self) -> str:
        return "chambers"

    @property
    def compatible_genres(self) -> list[str]:
        return ["funk", "jazz", "fusion", "rock", "r&b"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Dennis Chambers' signature style to a pattern.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Chambers' characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_chambers"

        # 1. Apply deep funk pocket groove
        styled_pattern = self._apply_funk_pocket(styled_pattern)

        # 2. Add fast chops and bass drum triplets
        styled_pattern = self._add_fast_chops_triplets(styled_pattern)

        # 3. Apply in/out of pocket stretching
        styled_pattern = self._apply_pocket_stretching(styled_pattern)

        # 4. Add Parliament-Funkadelic groove elements
        styled_pattern = self._add_pfunk_elements(styled_pattern)

        # 5. Insert technical prowess showcases
        styled_pattern = self._add_technical_showcases(styled_pattern)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Dennis Chambers' signature fill patterns."""
        fills = []

        # Parliament-Funkadelic groove showcase
        pfunk_fill = Fill(
            pattern=self._create_pfunk_groove(),
            trigger_probability=0.95,
            section_position="start",
        )
        fills.append(pfunk_fill)

        # Fast chops and triplets showcase
        chops_fill = Fill(
            pattern=self._create_fast_chops_showcase(),
            trigger_probability=0.9,
            section_position="middle",
        )
        fills.append(chops_fill)

        # In/out of pocket demonstration
        pocket_fill = Fill(
            pattern=self._create_pocket_stretch_demo(),
            trigger_probability=0.8,
            section_position="end",
        )
        fills.append(pocket_fill)

        # Technical fusion showcase
        fusion_fill = Fill(
            pattern=self._create_fusion_technical_showcase(),
            trigger_probability=0.7,
            section_position="middle",
        )
        fills.append(fusion_fill)

        return fills

    def _apply_funk_pocket(self, pattern: Pattern) -> Pattern:
        """Apply Chambers' deep funk pocket groove."""
        # Adjust timing for deep pocket feel
        pocket_offset = 0.01  # Slight behind-beat feel for funk

        for beat in pattern.beats:
            if beat.instrument == DrumInstrument.SNARE:
                # Snare slightly behind for funk pocket
                beat.position += pocket_offset
                # Add funkiness to backbeat
                beat.velocity = min(127, beat.velocity + 8)

            elif beat.instrument == DrumInstrument.KICK:
                # Kick drum drives the pocket
                beat.velocity = min(127, beat.velocity + 12)
                # Slightly ahead to drive (but don't go negative)
                beat.position = max(0.0, beat.position - pocket_offset * 0.5)

        return pattern

    def _add_fast_chops_triplets(self, pattern: Pattern) -> Pattern:
        """Add Chambers' fast chops and bass drum triplets."""
        new_beats = list(pattern.beats)

        # Add bass drum triplets (his specialty)
        triplet_spots = []
        for beat in pattern.beats:
            if (
                beat.instrument == DrumInstrument.KICK and random.random() < 0.3
            ):  # 30% chance
                triplet_spots.append(beat.position)

        for spot in triplet_spots:
            # Add rapid-fire triplet pattern
            triplet_subdivision = 1.0 / 3.0
            base_velocity = 100

            for i in range(3):
                triplet_position = spot + (
                    i * triplet_subdivision * 0.25
                )  # Fast triplets
                triplet_kick = Beat(
                    position=triplet_position,
                    instrument=DrumInstrument.KICK,
                    velocity=base_velocity + random.randint(-5, 10),
                    duration=0.05,
                )
                new_beats.append(triplet_kick)

        # Add hand chops (fast hands)
        chop_positions = [0.875, 1.875, 2.875]  # Just before beats
        for pos in chop_positions:
            if random.random() < 0.4:  # 40% chance
                # Fast hand pattern
                for i in range(4):  # 32nd note chops
                    chop_pos = pos + (i * 0.0625)
                    chop_velocity = 85 + random.randint(-10, 15)

                    chop_beat = Beat(
                        position=chop_pos,
                        instrument=DrumInstrument.SNARE,
                        velocity=chop_velocity,
                        duration=0.03,
                    )
                    new_beats.append(chop_beat)

        pattern.beats = new_beats
        return pattern

    def _apply_pocket_stretching(self, pattern: Pattern) -> Pattern:
        """Apply Chambers' ability to stretch in/out of pocket."""
        # Vary timing to demonstrate pocket stretching
        stretch_factor = random.uniform(0.98, 1.02)  # Subtle tempo variation

        for i, beat in enumerate(pattern.beats):
            # Apply stretching - some beats ahead, some behind
            stretch_direction = 1 if i % 3 == 0 else -1
            stretch_amount = 0.008 * stretch_direction * stretch_factor

            beat.position += stretch_amount

            # Keep it musical - don't let it drift too far
            beat.position = max(0.0, min(4.0, beat.position))

        return pattern

    def _add_pfunk_elements(self, pattern: Pattern) -> Pattern:
        """Add Parliament-Funkadelic groove elements."""
        new_beats = list(pattern.beats)

        # Add P-Funk signature elements
        # 1. "The One" emphasis (heavy downbeat)
        downbeat_positions = [0.0, 2.0]
        for pos in downbeat_positions:
            # Check for existing kick
            has_kick = any(
                beat.position == pos and beat.instrument == DrumInstrument.KICK
                for beat in pattern.beats
            )

            if has_kick:
                # Enhance existing kick for "The One"
                for beat in pattern.beats:
                    if (
                        beat.position == pos
                        and beat.instrument == DrumInstrument.KICK
                    ):
                        beat.velocity = min(127, beat.velocity + 15)
            else:
                # Add "The One" kick
                one_kick = Beat(
                    position=pos,
                    instrument=DrumInstrument.KICK,
                    velocity=120,
                    duration=0.15,
                )
                new_beats.append(one_kick)

        # 2. Funk hi-hat patterns
        hihat_funk_positions = [0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75]
        for i, pos in enumerate(hihat_funk_positions):
            if random.random() < 0.6:  # 60% chance
                # Alternate between closed and open for funk feel
                is_open = i % 4 in [1, 3]
                instrument = (
                    DrumInstrument.OPEN_HH
                    if is_open
                    else DrumInstrument.CLOSED_HH
                )
                velocity = 75 + random.randint(-5, 10)

                funk_hihat = Beat(
                    position=pos,
                    instrument=instrument,
                    velocity=velocity,
                    duration=0.08 if not is_open else 0.12,
                )
                new_beats.append(funk_hihat)

        pattern.beats = new_beats
        return pattern

    def _add_technical_showcases(self, pattern: Pattern) -> Pattern:
        """Add technical prowess showcases while maintaining groove."""
        new_beats = list(pattern.beats)

        # Add technical elements that don't sacrifice groove
        tech_positions = [1.5, 3.5]  # Between main beats

        for pos in tech_positions:
            if random.random() < 0.25:  # 25% chance - sparingly used
                # Technical but musical fill
                tech_sequence = [
                    (0.0, DrumInstrument.SNARE, 85),
                    (0.0625, DrumInstrument.KICK, 90),
                    (0.125, DrumInstrument.MID_TOM, 88),
                    (0.1875, DrumInstrument.KICK, 85),
                ]

                for offset, instrument, velocity in tech_sequence:
                    tech_beat = Beat(
                        position=pos + offset,
                        instrument=instrument,
                        velocity=velocity,
                        duration=0.05,
                    )
                    new_beats.append(tech_beat)

        pattern.beats = new_beats
        return pattern

    def _create_pfunk_groove(self) -> Pattern:
        """Create Parliament-Funkadelic signature groove."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("chambers_pfunk_groove")

        # "The One" - heavy emphasis on downbeat
        builder.kick(0.0, 125)  # Maximum emphasis
        builder.snare(1.0, 110)  # Backbeat

        # Funk kick pattern
        builder.kick(0.75, 105)
        builder.kick(1.5, 100)
        builder.kick(2.25, 108)

        # Funk hi-hat pattern
        hihat_pattern = [
            0.25,
            0.5,
            0.75,
            1.25,
            1.5,
            1.75,
            2.25,
            2.5,
            2.75,
            3.25,
            3.5,
            3.75,
        ]
        for i, pos in enumerate(hihat_pattern):
            is_open = i % 4 in [1, 3]
            velocity = 75 + random.randint(-5, 8)
            builder.hihat(pos, velocity, open=is_open)

        return builder.build()

    def _create_fast_chops_showcase(self) -> Pattern:
        """Create fast chops and triplets showcase."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("chambers_fast_chops")

        # Main groove foundation
        builder.kick(0.0, 115)
        builder.snare(1.0, 110)

        # Fast bass drum triplets
        triplet_base = 0.5
        triplet_subdivision = 1.0 / 3.0
        for i in range(3):
            pos = triplet_base + (i * triplet_subdivision * 0.5)
            velocity = 95 + (i * 3)
            builder.kick(pos, velocity)

        # Fast hand chops leading into beat 2
        chop_base = 0.75
        for i in range(4):  # 32nd note chops
            pos = chop_base + (i * 0.0625)
            velocity = 80 + random.randint(0, 15)
            builder.snare(pos, velocity)

        return builder.build()

    def _create_pocket_stretch_demo(self) -> Pattern:
        """Create in/out of pocket demonstration."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("chambers_pocket_stretch")

        # Base groove that stretches the pocket
        builder.kick(0.0, 110)
        builder.snare(1.02, 108)  # Slightly late (out of pocket)

        builder.kick(1.5, 105)
        builder.snare(2.98, 112)  # Slightly early (ahead of pocket)

        # Hi-hat maintains steady reference
        for i in range(8):
            pos = i * 0.5
            builder.hihat(pos, 70)

        return builder.build()

    def _create_fusion_technical_showcase(self) -> Pattern:
        """Create fusion technical showcase."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("chambers_fusion_technical")

        # Technical fusion pattern maintaining musicality
        builder.kick(0.0, 100)
        builder.snare(0.1667, 85)  # Triplet
        builder.kick(0.3333, 95)
        builder.snare(0.5, 110)  # Strong accent

        # Complex but musical fill
        builder.pattern.add_beat(0.6667, DrumInstrument.MID_TOM, 88)
        builder.kick(0.75, 90)
        builder.pattern.add_beat(0.8333, DrumInstrument.FLOOR_TOM, 92)
        builder.snare(1.0, 115)  # Resolution

        return builder.build()
