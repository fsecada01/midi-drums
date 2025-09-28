"""
Jason Roeder drummer plugin.

Implements Jason Roeder's signature drumming techniques based on research.
Known for atmospheric sludge metal, post-metal soundscapes, creative use
of minimal kit, and the crushing, cinematic drumming of Neurosis and Sleep.
"""

import random

from midi_drums.models.pattern import Beat, DrumInstrument, Pattern
from midi_drums.models.song import Fill
from midi_drums.plugins.base import DrummerPlugin

# Type annotations use built-in list for Python 3.9+


class RoederPlugin(DrummerPlugin):
    """Jason Roeder drummer style plugin.

    Characteristics:
    - Atmospheric and cinematic approach
    - Creative use of minimal kit setup
    - Crushing weight and purposeful hits
    - Labyrinthine patterns and complex rhythms
    - Evolution from punk to sophisticated metal
    - Tom-heavy patterns for atmospheric effect
    - Emphasis on mood and tension building
    """

    @property
    def drummer_name(self) -> str:
        return "roeder"

    @property
    def compatible_genres(self) -> list[str]:
        return ["metal", "sludge", "post_metal", "doom", "atmospheric"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Jason Roeder's signature style to a pattern.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Roeder's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_roeder"

        # 1. Apply atmospheric weight and space
        styled_pattern = self._apply_atmospheric_weight(styled_pattern)

        # 2. Add tom-heavy patterns for mood
        styled_pattern = self._add_tom_heavy_patterns(styled_pattern)

        # 3. Create labyrinthine rhythmic complexity
        styled_pattern = self._add_labyrinthine_patterns(styled_pattern)

        # 4. Apply crushing, purposeful dynamics
        styled_pattern = self._apply_crushing_dynamics(styled_pattern)

        # 5. Add post-metal atmospheric elements
        styled_pattern = self._add_post_metal_elements(styled_pattern)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Jason Roeder's signature fill patterns."""
        fills = []

        # Atmospheric tom roll
        atmospheric_fill = Fill(
            pattern=self._create_atmospheric_tom_roll(),
            trigger_probability=0.9,
            section_position="end",
        )
        fills.append(atmospheric_fill)

        # Labyrinthine complexity fill
        complex_fill = Fill(
            pattern=self._create_labyrinthine_fill(),
            trigger_probability=0.8,
            section_position="middle",
        )
        fills.append(complex_fill)

        # Crushing weight pattern
        crushing_fill = Fill(
            pattern=self._create_crushing_pattern(),
            trigger_probability=0.7,
            section_position="start",
        )
        fills.append(crushing_fill)

        # Minimal kit creativity showcase
        minimal_fill = Fill(
            pattern=self._create_minimal_kit_showcase(),
            trigger_probability=0.6,
            section_position="end",
        )
        fills.append(minimal_fill)

        return fills

    def _apply_atmospheric_weight(self, pattern: Pattern) -> Pattern:
        """Apply Roeder's atmospheric weight and purposeful spacing."""
        # Add space between hits for atmospheric effect
        weighted_beats = []

        for beat in pattern.beats:
            # Every hit is purposeful - increase impact
            if beat.instrument == DrumInstrument.KICK:
                weighted_beat = Beat(
                    position=beat.position,
                    instrument=beat.instrument,
                    velocity=min(127, beat.velocity + 20),  # Crushing kick
                    duration=beat.duration * 1.5,  # Longer sustain
                )
                weighted_beats.append(weighted_beat)

            elif beat.instrument == DrumInstrument.SNARE:
                weighted_beat = Beat(
                    position=beat.position,
                    instrument=beat.instrument,
                    velocity=min(127, beat.velocity + 15),  # Heavy snare
                    duration=beat.duration * 1.2,
                )
                weighted_beats.append(weighted_beat)

                # Add atmospheric reverb-like echo (ghost hit)
                if random.random() < 0.3:  # 30% chance
                    echo_beat = Beat(
                        position=beat.position + 0.125,
                        instrument=beat.instrument,
                        velocity=max(30, beat.velocity - 40),
                        duration=beat.duration * 0.8,
                        ghost_note=True,
                    )
                    weighted_beats.append(echo_beat)

            else:
                weighted_beats.append(beat)

        pattern.beats = weighted_beats
        return pattern

    def _add_tom_heavy_patterns(self, pattern: Pattern) -> Pattern:
        """Add tom-heavy patterns for atmospheric effect."""
        new_beats = list(pattern.beats)

        # Add floor tom "portents of war" style patterns
        tom_positions = [0.5, 1.5, 2.5, 3.5]  # Between main beats

        for pos in tom_positions:
            if random.random() < 0.4:  # 40% chance
                # Floor tom for deep atmospheric effect
                atmospheric_tom = Beat(
                    position=pos,
                    instrument=DrumInstrument.FLOOR_TOM,
                    velocity=90 + random.randint(-10, 15),
                    duration=0.3,  # Long sustain
                )
                new_beats.append(atmospheric_tom)

                # Sometimes add mid tom for texture
                if random.random() < 0.5:
                    mid_tom = Beat(
                        position=pos + 0.125,
                        instrument=DrumInstrument.MID_TOM,
                        velocity=85 + random.randint(-5, 10),
                        duration=0.2,
                    )
                    new_beats.append(mid_tom)

        pattern.beats = new_beats
        return pattern

    def _add_labyrinthine_patterns(self, pattern: Pattern) -> Pattern:
        """Create Roeder's labyrinthine rhythmic complexity."""
        new_beats = list(pattern.beats)

        # Add complex, winding patterns that deviate from punk simplicity
        complex_positions = [
            0.25,
            0.375,
            0.75,
            0.875,  # Off-beat complexity
            1.25,
            1.625,
            1.875,
            2.125,
            2.375,
            2.625,
            3.125,
            3.375,
            3.75,
        ]

        for pos in complex_positions:
            if random.random() < 0.25:  # 25% chance for complexity
                # Choose instrument based on atmospheric needs
                instruments = [
                    DrumInstrument.FLOOR_TOM,
                    DrumInstrument.MID_TOM,
                    DrumInstrument.KICK,
                    DrumInstrument.SNARE,
                ]

                instrument = random.choice(instruments)
                velocity = 70 + random.randint(0, 25)

                complex_beat = Beat(
                    position=pos,
                    instrument=instrument,
                    velocity=velocity,
                    duration=0.15,
                )
                new_beats.append(complex_beat)

        pattern.beats = new_beats
        return pattern

    def _apply_crushing_dynamics(self, pattern: Pattern) -> Pattern:
        """Apply crushing, weighty dynamics."""
        for beat in pattern.beats:
            if beat.instrument == DrumInstrument.KICK:
                # Crushing kick drum foundation
                beat.velocity = min(127, beat.velocity + 25)
                beat.duration = max(0.2, beat.duration * 1.5)

            elif beat.instrument == DrumInstrument.SNARE:
                # Powerful, crushing snare
                beat.velocity = min(127, beat.velocity + 18)

            elif beat.instrument in [
                DrumInstrument.FLOOR_TOM,
                DrumInstrument.MID_TOM,
            ]:
                # Atmospheric tom power
                beat.velocity = min(127, beat.velocity + 12)
                beat.duration = max(0.15, beat.duration * 1.3)

        return pattern

    def _add_post_metal_elements(self, pattern: Pattern) -> Pattern:
        """Add post-metal atmospheric and cinematic elements."""
        new_beats = list(pattern.beats)

        # Add suspended cymbals for atmosphere
        cymbal_positions = [0.0, 2.0]  # Strong beats for emphasis

        for pos in cymbal_positions:
            if random.random() < 0.3:  # 30% chance
                # Atmospheric crash or china
                instrument = (
                    DrumInstrument.CHINA
                    if random.random() < 0.4
                    else DrumInstrument.CRASH
                )

                atmospheric_cymbal = Beat(
                    position=pos,
                    instrument=instrument,
                    velocity=95 + random.randint(-10, 15),
                    duration=1.0,  # Long sustain for atmosphere
                )
                new_beats.append(atmospheric_cymbal)

        # Add ride bell for piercing atmospheric accents
        bell_positions = [1.0, 3.0]
        for pos in bell_positions:
            if random.random() < 0.2:  # 20% chance
                bell = Beat(
                    position=pos,
                    instrument=DrumInstrument.RIDE_BELL,
                    velocity=100 + random.randint(-5, 10),
                    duration=0.5,
                )
                new_beats.append(bell)

        pattern.beats = new_beats
        return pattern

    def _create_atmospheric_tom_roll(self) -> Pattern:
        """Create atmospheric tom roll pattern."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("roeder_atmospheric_toms")

        # Floor tom foundation (portent of war style)
        builder.pattern.add_beat(0.0, DrumInstrument.FLOOR_TOM, 100)
        builder.pattern.add_beat(0.5, DrumInstrument.FLOOR_TOM, 95)
        builder.pattern.add_beat(1.0, DrumInstrument.FLOOR_TOM, 105)

        # Add mid tom texture
        builder.pattern.add_beat(0.25, DrumInstrument.MID_TOM, 85)
        builder.pattern.add_beat(0.75, DrumInstrument.MID_TOM, 88)
        builder.pattern.add_beat(1.25, DrumInstrument.MID_TOM, 90)

        # Crushing finish
        builder.kick(1.5, 120)
        builder.crash(1.5, 110)

        return builder.build()

    def _create_labyrinthine_fill(self) -> Pattern:
        """Create complex, winding labyrinthine fill."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("roeder_labyrinthine")

        # Complex winding pattern
        sequence = [
            (0.0, DrumInstrument.FLOOR_TOM, 95),
            (0.1875, DrumInstrument.SNARE, 85),
            (0.375, DrumInstrument.MID_TOM, 90),
            (0.5625, DrumInstrument.KICK, 100),
            (0.75, DrumInstrument.FLOOR_TOM, 88),
            (0.9375, DrumInstrument.SNARE, 78),
            (1.125, DrumInstrument.MID_TOM, 92),
            (1.25, DrumInstrument.KICK, 95),
            (1.375, DrumInstrument.FLOOR_TOM, 98),
            (1.5, DrumInstrument.CHINA, 105),  # Atmospheric accent
        ]

        for pos, instrument, velocity in sequence:
            builder.pattern.add_beat(pos, instrument, velocity)

        return builder.build()

    def _create_crushing_pattern(self) -> Pattern:
        """Create crushing, weighty pattern."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("roeder_crushing")

        # Crushing foundation
        builder.kick(0.0, 127)  # Maximum power
        builder.snare(1.0, 120)

        # Add weight with floor tom
        builder.pattern.add_beat(0.5, DrumInstrument.FLOOR_TOM, 110)
        builder.pattern.add_beat(1.5, DrumInstrument.FLOOR_TOM, 115)

        # Atmospheric crash
        builder.crash(2.0, 105)

        return builder.build()

    def _create_minimal_kit_showcase(self) -> Pattern:
        """Create pattern showcasing creativity with minimal kit."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("roeder_minimal_creativity")

        # Creative use of limited pieces (rack tom + floor tom only)
        # Since age 12, Roeder used minimal kit - force creativity

        # Primary pattern using just kick, snare, and toms
        builder.kick(0.0, 110)
        builder.pattern.add_beat(0.25, DrumInstrument.MID_TOM, 85)  # Rack tom
        builder.snare(0.5, 105)
        builder.pattern.add_beat(0.75, DrumInstrument.FLOOR_TOM, 95)

        builder.kick(1.0, 108)
        builder.pattern.add_beat(1.25, DrumInstrument.FLOOR_TOM, 90)
        builder.snare(1.5, 110)
        builder.pattern.add_beat(1.75, DrumInstrument.MID_TOM, 88)

        return builder.build()
