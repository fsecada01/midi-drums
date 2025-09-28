"""
Mikkey Dee drummer plugin.

Implements Mikkey Dee's signature drumming techniques based on research.
Known for speed and precision from King Diamond era, power and groove
from Motörhead, and the versatility spanning horror metal to speed metal.
"""

import random

from midi_drums.models.pattern import Beat, DrumInstrument, Pattern
from midi_drums.models.song import Fill
from midi_drums.plugins.base import DrummerPlugin

# Type annotations use built-in list for Python 3.9+


class DeePlugin(DrummerPlugin):
    """Mikkey Dee drummer style plugin.

    Characteristics:
    - Speed and precision (King Diamond technical demands)
    - Power and groove (Motörhead driving rhythm)
    - Fast double-kick patterns with control
    - Versatility across multiple genres
    - "Twisted" backbeats and rhythmic turns
    - Long, theatrical drum solos
    - Balance of force and restraint
    """

    @property
    def drummer_name(self) -> str:
        return "dee"

    @property
    def compatible_genres(self) -> list[str]:
        return ["metal", "speed_metal", "punk", "hard_rock", "horror_metal"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Mikkey Dee's signature style to a pattern.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Dee's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_dee"

        # 1. Apply speed and precision elements
        styled_pattern = self._apply_speed_precision(styled_pattern)

        # 2. Add double-kick patterns with control
        styled_pattern = self._add_controlled_double_kicks(styled_pattern)

        # 3. Insert twisted backbeats and rhythmic turns
        styled_pattern = self._add_twisted_backbeats(styled_pattern)

        # 4. Apply power with restraint balance
        styled_pattern = self._apply_power_restraint_balance(styled_pattern)

        # 5. Add genre-spanning versatility elements
        styled_pattern = self._add_versatility_elements(styled_pattern)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Mikkey Dee's signature fill patterns."""
        fills = []

        # King Diamond technical complexity fill
        king_diamond_fill = Fill(
            pattern=self._create_king_diamond_technical_fill(),
            trigger_probability=0.9,
            section_position="end",
        )
        fills.append(king_diamond_fill)

        # Motörhead driving power fill
        motorhead_fill = Fill(
            pattern=self._create_motorhead_power_fill(),
            trigger_probability=0.8,
            section_position="middle",
        )
        fills.append(motorhead_fill)

        # Speed metal precision showcase
        speed_fill = Fill(
            pattern=self._create_speed_metal_showcase(),
            trigger_probability=0.7,
            section_position="start",
        )
        fills.append(speed_fill)

        # Twisted backbeat pattern
        twisted_fill = Fill(
            pattern=self._create_twisted_backbeat_fill(),
            trigger_probability=0.6,
            section_position="middle",
        )
        fills.append(twisted_fill)

        return fills

    def _apply_speed_precision(self, pattern: Pattern) -> Pattern:
        """Apply Dee's speed and precision from King Diamond era."""
        # Tighten timing for precision
        for beat in pattern.beats:
            # Quantize more precisely than typical
            precise_position = (
                round(beat.position * 32) / 32
            )  # 32nd note precision
            beat.position = precise_position

            # Add slight velocity consistency for machine-like precision
            if beat.instrument == DrumInstrument.KICK:
                beat.velocity = min(
                    127, max(95, beat.velocity)
                )  # Consistent range
            elif beat.instrument == DrumInstrument.SNARE:
                beat.velocity = min(127, max(100, beat.velocity))

        return pattern

    def _add_controlled_double_kicks(self, pattern: Pattern) -> Pattern:
        """Add fast double-kick patterns with precise control."""
        new_beats = list(pattern.beats)

        # Find spots for double-kick patterns
        kick_spots = []
        for beat in pattern.beats:
            if (
                beat.instrument == DrumInstrument.KICK and random.random() < 0.3
            ):  # 30% chance
                kick_spots.append(beat.position)

        for spot in kick_spots:
            # Add controlled double-kick (not just speed, but control)
            second_kick = Beat(
                position=spot + 0.125,  # 32nd note later
                instrument=DrumInstrument.KICK,
                velocity=random.randint(90, 105),  # Controlled power
                duration=0.08,
            )
            new_beats.append(second_kick)

            # Sometimes add third kick for King Diamond complexity
            if random.random() < 0.4:  # 40% chance
                third_kick = Beat(
                    position=spot + 0.25,  # 16th note later
                    instrument=DrumInstrument.KICK,
                    velocity=random.randint(85, 100),
                    duration=0.08,
                )
                new_beats.append(third_kick)

        pattern.beats = new_beats
        return pattern

    def _add_twisted_backbeats(self, pattern: Pattern) -> Pattern:
        """Add Dee's signature 'twisted' backbeats and rhythmic turns."""
        new_beats = list(pattern.beats)

        # Add "twisted" elements - backbeats turned around twice
        twist_positions = [1.5, 3.5]  # Between main backbeats

        for pos in twist_positions:
            if random.random() < 0.4:  # 40% chance
                # First twist
                twist_snare_1 = Beat(
                    position=pos,
                    instrument=DrumInstrument.SNARE,
                    velocity=85 + random.randint(-5, 10),
                    duration=0.08,
                )
                new_beats.append(twist_snare_1)

                # Second twist (turn around)
                twist_snare_2 = Beat(
                    position=pos + 0.125,
                    instrument=DrumInstrument.SNARE,
                    velocity=90 + random.randint(-5, 10),
                    duration=0.08,
                )
                new_beats.append(twist_snare_2)

        pattern.beats = new_beats
        return pattern

    def _apply_power_restraint_balance(self, pattern: Pattern) -> Pattern:
        """Apply Dee's balance of power and restraint."""
        # He pulls tone from drums rather than just hitting them
        for beat in pattern.beats:
            if beat.instrument == DrumInstrument.KICK:
                # Powerful but controlled kick
                beat.velocity = min(
                    120, beat.velocity + 8
                )  # Power with ceiling
                beat.duration = max(0.1, beat.duration)  # Good sustain

            elif beat.instrument == DrumInstrument.SNARE:
                # Shift between power and restraint
                if beat.position % 1.0 == 0:  # On downbeats - more power
                    beat.velocity = min(125, beat.velocity + 12)
                else:  # Off beats - more restraint
                    beat.velocity = max(70, beat.velocity - 5)

        return pattern

    def _add_versatility_elements(self, pattern: Pattern) -> Pattern:
        """Add elements showing Dee's genre versatility."""
        new_beats = list(pattern.beats)

        # Add elements from different genres he's played
        versatility_positions = [0.75, 2.75]

        for pos in versatility_positions:
            if random.random() < 0.3:  # 30% chance
                # Choose element based on genre versatility
                genre_element = random.choice(
                    [
                        "king_diamond_complex",
                        "motorhead_drive",
                        "fusion_touch",
                        "punk_simplicity",
                    ]
                )

                if genre_element == "king_diamond_complex":
                    # Complex technical element
                    new_beats.append(
                        Beat(
                            position=pos,
                            instrument=DrumInstrument.MID_TOM,
                            velocity=88,
                            duration=0.06,
                        )
                    )
                    new_beats.append(
                        Beat(
                            position=pos + 0.0625,
                            instrument=DrumInstrument.FLOOR_TOM,
                            velocity=92,
                            duration=0.06,
                        )
                    )

                elif genre_element == "motorhead_drive":
                    # Driving punk-metal element
                    new_beats.append(
                        Beat(
                            position=pos,
                            instrument=DrumInstrument.KICK,
                            velocity=110,
                            duration=0.1,
                        )
                    )

                elif genre_element == "fusion_touch":
                    # Subtle fusion influence (he loves fusion)
                    new_beats.append(
                        Beat(
                            position=pos,
                            instrument=DrumInstrument.SNARE,
                            velocity=60,  # Ghost note
                            duration=0.05,
                            ghost_note=True,
                        )
                    )

        pattern.beats = new_beats
        return pattern

    def _create_king_diamond_technical_fill(self) -> Pattern:
        """Create King Diamond era technical complexity fill."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("dee_king_diamond_technical")

        # Complex technical pattern inspired by horror metal demands
        sequence = [
            (0.0, DrumInstrument.KICK, 105),
            (0.0625, DrumInstrument.SNARE, 95),
            (0.125, DrumInstrument.MID_TOM, 90),
            (0.1875, DrumInstrument.KICK, 100),
            (0.25, DrumInstrument.FLOOR_TOM, 95),
            (0.3125, DrumInstrument.SNARE, 105),
            (0.375, DrumInstrument.KICK, 98),
            (0.4375, DrumInstrument.MID_TOM, 92),
            (0.5, DrumInstrument.CRASH, 110),
            (0.5, DrumInstrument.KICK, 108),  # Crash + kick
        ]

        for pos, instrument, velocity in sequence:
            builder.pattern.add_beat(pos, instrument, velocity)

        return builder.build()

    def _create_motorhead_power_fill(self) -> Pattern:
        """Create Motörhead era driving power fill."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("dee_motorhead_power")

        # Fast, driving pattern that bridges punk and metal
        builder.kick(0.0, 115)
        builder.snare(0.25, 110)
        builder.kick(0.5, 112)
        builder.kick(0.625, 108)  # Double kick
        builder.snare(0.75, 115)
        builder.kick(1.0, 118)

        # Add the "something twisted" element
        builder.snare(1.125, 95)  # Twisted backbeat
        builder.snare(1.25, 100)  # Turn around

        return builder.build()

    def _create_speed_metal_showcase(self) -> Pattern:
        """Create speed metal precision showcase."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("dee_speed_metal")

        # Fast, precise pattern showcasing speed with control
        # 16th note kick pattern
        for i in range(8):  # 16th notes in half measure
            pos = i * 0.25
            velocity = 95 + random.randint(-3, 8)
            builder.kick(pos, velocity)

        # Accented snares on 2 and 4
        builder.snare(1.0, 120)
        builder.snare(3.0, 120)

        return builder.build()

    def _create_twisted_backbeat_fill(self) -> Pattern:
        """Create twisted backbeat pattern."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("dee_twisted_backbeat")

        # The "drummiest" Motörhead pattern - backbeats turned around twice
        builder.kick(0.0, 110)
        builder.snare(1.0, 115)  # Main backbeat

        # First twist
        builder.snare(1.5, 95)
        builder.kick(1.625, 100)

        # Turn around (second twist)
        builder.snare(1.75, 100)
        builder.kick(1.875, 105)

        # Resolution
        builder.snare(2.0, 120)

        return builder.build()
