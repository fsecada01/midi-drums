"""Jazz genre plugin with various jazz substyles.

Based on research of swing, bebop, fusion, Latin jazz, and contemporary
jazz patterns.
Emphasizes ride cymbal patterns, swing feel, and sophisticated rhythm
section interplay.
"""

import random

from midi_drums.models.pattern import (
    Beat,
    DrumInstrument,
    Pattern,
    PatternBuilder,
    TimeSignature,
)
from midi_drums.models.song import Fill, GenerationParameters
from midi_drums.plugins.base import GenrePlugin


class JazzGenrePlugin(GenrePlugin):
    """Plugin for generating jazz drum patterns."""

    @property
    def genre_name(self) -> str:
        return "jazz"

    @property
    def supported_styles(self) -> list[str]:
        return [
            "swing",  # Classic swing era patterns
            "bebop",  # Fast, intricate bebop patterns
            "fusion",  # Jazz-rock fusion with power
            "latin",  # Latin jazz (bossa nova, samba)
            "ballad",  # Slow jazz ballads with brushes
            "hard_bop",  # Hard bop with driving feel
            "contemporary",  # Modern jazz patterns
        ]

    @property
    def intensity_profile(self) -> dict[str, float]:
        """Jazz genre intensity characteristics.

        Jazz emphasizes sophistication, dynamics, and space. Lower aggression
        and power, but high complexity. Ride cymbal focus creates lighter touch.
        """
        return {
            "aggression": 0.3,  # Low aggression, conversational
            "speed": 0.7,  # Varies widely (ballad to bebop)
            "density": 0.6,  # Ride pattern creates constant texture
            "power": 0.4,  # Light to moderate touch
            "complexity": 0.85,  # High rhythmic sophistication
            "darkness": 0.3,  # Generally bright, open tonality
        }

    def generate_pattern(
        self, section: str, parameters: GenerationParameters
    ) -> Pattern:
        """Generate jazz pattern based on section and style."""
        style = parameters.style
        time_sig = TimeSignature(4, 4)  # Most jazz is 4/4

        if section == "intro":
            return self._generate_intro_pattern(style, parameters, time_sig)
        elif section == "verse":
            return self._generate_verse_pattern(style, parameters, time_sig)
        elif section == "chorus":
            return self._generate_chorus_pattern(style, parameters, time_sig)
        elif section == "breakdown":
            return self._generate_breakdown_pattern(style, parameters, time_sig)
        elif section in ["bridge", "pre_chorus"]:
            return self._generate_bridge_pattern(style, parameters, time_sig)
        elif section == "outro":
            return self._generate_outro_pattern(style, parameters, time_sig)
        else:
            # Default to verse pattern for unknown sections
            return self._generate_verse_pattern(style, parameters, time_sig)

    def get_common_fills(self) -> list[Fill]:
        """Get common jazz fill patterns."""
        fills = []

        # Brush sweep fill
        brush_fill = Fill(
            pattern=self._create_brush_sweep_fill(),
            trigger_probability=0.7,
            section_position="end",
        )
        fills.append(brush_fill)

        # Bebop "dropping bombs" fill
        bebop_fill = Fill(
            pattern=self._create_bebop_bombs_fill(),
            trigger_probability=0.8,
            section_position="middle",
        )
        fills.append(bebop_fill)

        # Latin percussion fill
        latin_fill = Fill(
            pattern=self._create_latin_percussion_fill(),
            trigger_probability=0.6,
            section_position="start",
        )
        fills.append(latin_fill)

        return fills

    def _generate_intro_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate intro pattern for specified jazz style."""
        if style == "swing":
            return self._swing_intro(parameters, time_sig)
        elif style == "bebop":
            return self._bebop_intro(parameters, time_sig)
        elif style == "latin":
            return self._latin_jazz_intro(parameters, time_sig)
        elif style == "ballad":
            return self._ballad_intro(parameters, time_sig)
        else:
            return self._swing_intro(parameters, time_sig)

    def _generate_verse_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate verse pattern for specified jazz style."""
        if style == "swing":
            return self._swing_verse(parameters, time_sig)
        elif style == "bebop":
            return self._bebop_verse(parameters, time_sig)
        elif style == "fusion":
            return self._fusion_verse(parameters, time_sig)
        elif style == "latin":
            return self._latin_jazz_verse(parameters, time_sig)
        elif style == "ballad":
            return self._ballad_verse(parameters, time_sig)
        elif style == "hard_bop":
            return self._hard_bop_verse(parameters, time_sig)
        elif style == "contemporary":
            return self._contemporary_verse(parameters, time_sig)
        else:
            return self._swing_verse(parameters, time_sig)

    def _generate_chorus_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate chorus pattern - maintains swing feel with complexity."""
        base_pattern = self._generate_verse_pattern(style, parameters, time_sig)
        base_pattern.name = base_pattern.name.replace("verse", "chorus")

        # Add more comping (snare/kick interactions) for chorus
        if style in ["bebop", "hard_bop"]:
            self._add_comping_accents(base_pattern)

        return base_pattern

    def _generate_breakdown_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate breakdown pattern - often features solo drumming."""
        builder = PatternBuilder(f"jazz_{style}_breakdown")

        if style == "fusion":
            # Fusion breakdown with power
            builder.kick(0.0, 110).kick(2.5, 105)
            builder.snare(1.0, 115).snare(3.0, 115)
            # Add ride pattern
            ride_positions = [0.0, 0.67, 1.33, 2.0, 2.67, 3.33]
            for pos in ride_positions:
                builder.ride(pos, 85)
        else:
            # Traditional jazz breakdown - brushes on snare
            brush_positions = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
            for pos in brush_positions:
                velocity = 70 + random.randint(-10, 10)
                builder.snare(pos, velocity)

        return builder.build()

    def _generate_bridge_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate bridge pattern - often more adventurous."""
        builder = PatternBuilder(f"jazz_{style}_bridge")

        # Jazz bridge often features ride bell
        builder.pattern.add_beat(0.0, DrumInstrument.RIDE_BELL, 95)
        builder.pattern.add_beat(2.0, DrumInstrument.RIDE_BELL, 95)

        # Subtle kick and snare
        builder.kick(0.5, 80).kick(2.75, 85)
        builder.snare(1.5, 90).snare(3.25, 85)

        # Hi-hat on 2 and 4
        builder.hihat(1.0, 75).hihat(3.0, 75)

        return builder.build()

    def _generate_outro_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate outro pattern."""
        if style == "ballad":
            builder = PatternBuilder(f"jazz_{style}_outro")
            # Soft brush ending
            builder.snare(0.0, 60)  # Soft brush sweep
            return builder.build()
        else:
            # Use verse pattern with final accent
            base_pattern = self._generate_verse_pattern(
                style, parameters, time_sig
            )
            base_pattern.name = base_pattern.name.replace("verse", "outro")

            # Add final crash
            if base_pattern.beats:
                # Create new beat instead of copying
                final_crash = Beat(
                    position=3.75,  # End of measure
                    instrument=DrumInstrument.CRASH,
                    velocity=100,  # Subtle jazz crash
                )
                base_pattern.beats.append(final_crash)

            return base_pattern

    # Style-specific pattern implementations

    def _swing_intro(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Swing intro with classic ride pattern."""
        builder = PatternBuilder("jazz_swing_intro")

        # Classic swing ride pattern: quarter note + swing eighth notes
        swing_positions = [0.0, 0.67, 1.33, 2.0, 2.67, 3.33]  # Swing feel
        for pos in swing_positions:
            velocity = 80 + random.randint(-3, 7)
            builder.ride(pos, velocity)

        # Hi-hat on 2 and 4
        builder.hihat(1.0, 70).hihat(3.0, 70)

        # Light kick
        builder.kick(0.0, 85)

        return builder.build()

    def _swing_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Classic swing verse pattern."""
        builder = PatternBuilder("jazz_swing_verse")

        # Standard jazz ride pattern with swing feel
        # Pattern: quarter note + swing eighths (triplet-based)
        swing_positions = [0.0, 0.67, 1.0, 1.33, 2.0, 2.67, 3.0, 3.33]
        for _i, pos in enumerate(swing_positions):
            # Accent pattern: strong on 1 and 3, lighter on others
            if pos in [0.0, 2.0]:  # Beats 1 and 3
                velocity = 85
            elif pos in [0.67, 2.67]:  # Swing upbeats
                velocity = 75
            else:  # Beats 2 and 4
                velocity = 80

            builder.ride(pos, velocity)

        # Hi-hat foot on 2 and 4 (crucial for swing feel)
        builder.hihat(1.0, 75).hihat(3.0, 75)

        # Light "feathering" on bass drum
        if random.random() < 0.4:  # 40% chance
            builder.kick(0.0, 70)  # Very light kick on 1

        # Occasional snare comping
        if random.random() < 0.3:  # 30% chance
            comp_pos = random.choice([1.33, 2.67, 3.67])
            builder.snare(comp_pos, 60 + random.randint(-10, 15))

        return builder.build()

    def _bebop_intro(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Bebop intro with fast, intricate patterns."""
        builder = PatternBuilder("jazz_bebop_intro")

        # Fast swing ride pattern
        swing_positions = [
            0.0,
            0.33,
            0.67,
            1.0,
            1.33,
            1.67,
            2.0,
            2.33,
            2.67,
            3.0,
            3.33,
            3.67,
        ]
        for pos in swing_positions:
            velocity = 82 + random.randint(-5, 8)
            builder.ride(pos, velocity)

        # "Dropping bombs" - sporadic kick accents
        bomb_positions = [0.75, 2.25, 3.5]
        for pos in bomb_positions:
            if random.random() < 0.6:  # 60% chance
                builder.kick(pos, 90 + random.randint(-5, 10))

        return builder.build()

    def _bebop_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Bebop verse with complex comping."""
        builder = PatternBuilder("jazz_bebop_verse")

        # Fast swing ride cymbal
        swing_eighth_positions = [
            0.0,
            0.33,
            0.67,
            1.0,
            1.33,
            1.67,
            2.0,
            2.33,
            2.67,
            3.0,
            3.33,
            3.67,
        ]
        for pos in swing_eighth_positions:
            # Accent pattern for bebop ride
            if pos in [0.0, 2.0]:  # Strong on 1 and 3
                velocity = 90
            elif pos in [0.67, 1.67, 2.67, 3.67]:  # Swing upbeats
                velocity = 78
            else:
                velocity = 82

            builder.ride(pos, velocity)

        # Active comping between snare and kick
        comping_patterns = [
            (0.75, DrumInstrument.KICK, 85),
            (1.25, DrumInstrument.SNARE, 75),
            (2.33, DrumInstrument.KICK, 90),
            (3.17, DrumInstrument.SNARE, 80),
        ]

        for pos, instrument, velocity in comping_patterns:
            if random.random() < 0.7:  # 70% chance for each comp
                builder.pattern.add_beat(pos, instrument, velocity)

        # Hi-hat on 2 and 4
        builder.hihat(1.0, 75).hihat(3.0, 75)

        return builder.build()

    def _fusion_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Jazz fusion with rock influence."""
        builder = PatternBuilder("jazz_fusion_verse")

        # Fusion often uses straight eighths instead of swing
        # Ride pattern with more power
        for i in range(8):
            pos = i * 0.5
            velocity = 85 + random.randint(-5, 10)
            if i % 2 == 0:  # Accent on quarters
                velocity += 8
            builder.ride(pos, min(127, velocity))

        # More aggressive kick pattern
        kick_pattern = [0.0, 1.5, 2.25, 3.75]
        for pos in kick_pattern:
            builder.kick(pos, 95 + random.randint(-5, 10))

        # Snare backbeat with ghost notes
        builder.snare(1.0, 105).snare(3.0, 105)
        builder.snare(0.75, 65, ghost_note=True)  # Ghost note
        builder.snare(2.75, 68, ghost_note=True)

        return builder.build()

    def _latin_jazz_intro(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Latin jazz intro with bossa nova feel."""
        builder = PatternBuilder("jazz_latin_intro")

        # Bossa nova kick pattern
        builder.kick(0.0, 85).kick(1.5, 80).kick(2.75, 85)

        # Cross-stick clave pattern
        builder.snare(0.0, 70).snare(0.5, 65).snare(
            2.0, 70
        )  # Cross stick simulation

        # Light hi-hat
        for i in range(8):
            builder.hihat(i * 0.5, 60 + random.randint(-5, 5))

        return builder.build()

    def _latin_jazz_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Latin jazz verse with samba/bossa patterns."""
        builder = PatternBuilder("jazz_latin_verse")

        # Samba-influenced kick pattern
        samba_kicks = [0.0, 0.5, 1.5, 2.0, 2.75, 3.25]
        for pos in samba_kicks:
            velocity = 85 + random.randint(-5, 5)
            builder.kick(pos, velocity)

        # Cross-stick pattern (simulated with snare)
        cross_stick_pattern = [0.0, 0.5, 2.0, 2.5]
        for pos in cross_stick_pattern:
            builder.snare(pos, 75)  # Cross stick sound

        # Brush sweep simulation on snare
        builder.snare(1.0, 60)  # Soft brush sweep
        builder.snare(3.0, 65)

        # Light ride cymbal
        for i in range(4):
            pos = i * 1.0
            builder.ride(pos, 70)

        return builder.build()

    def _ballad_intro(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Ballad intro with brushes."""
        builder = PatternBuilder("jazz_ballad_intro")

        # Soft brush sweeps
        builder.snare(0.0, 50)  # Soft sweep
        builder.snare(2.0, 55)

        # Very light kick
        builder.kick(0.0, 60)

        return builder.build()

    def _ballad_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Ballad verse with brush technique."""
        builder = PatternBuilder("jazz_ballad_verse")

        # Brush sweep pattern (circular motion simulation)
        sweep_positions = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
        for pos in sweep_positions:
            velocity = 55 + random.randint(-5, 10)
            builder.snare(pos, velocity)  # Brush sweep

        # Very subtle kick
        builder.kick(0.0, 65).kick(2.0, 60)

        # Soft hi-hat
        builder.hihat(1.0, 50).hihat(3.0, 50)

        return builder.build()

    def _hard_bop_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Hard bop with driving feel."""
        builder = PatternBuilder("jazz_hard_bop_verse")

        # Driving ride pattern
        swing_positions = [0.0, 0.67, 1.0, 1.33, 2.0, 2.67, 3.0, 3.33]
        for pos in swing_positions:
            velocity = 88 + random.randint(-3, 7)
            builder.ride(pos, velocity)

        # More aggressive comping
        builder.kick(0.75, 90).kick(2.25, 85)
        builder.snare(1.33, 85).snare(3.67, 88)

        # Strong hi-hat on 2 and 4
        builder.hihat(1.0, 80).hihat(3.0, 80)

        return builder.build()

    def _contemporary_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Contemporary jazz with modern elements."""
        builder = PatternBuilder("jazz_contemporary_verse")

        # Mix of swing and straight feels
        if random.random() < 0.5:
            # Swing feel
            positions = [0.0, 0.67, 1.33, 2.0, 2.67, 3.33]
        else:
            # Straight eighths
            positions = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]

        for pos in positions:
            velocity = 82 + random.randint(-5, 8)
            builder.ride(pos, velocity)

        # Modern comping patterns
        builder.kick(0.25, 80).kick(2.75, 85)
        builder.snare(1.17, 75).snare(3.5, 80)

        # Hi-hat on 2 and 4
        builder.hihat(1.0, 75).hihat(3.0, 75)

        return builder.build()

    def _add_comping_accents(self, pattern: Pattern) -> None:
        """Add bebop-style comping accents to existing pattern."""
        new_beats = []

        # Add sporadic snare and kick accents
        accent_positions = [0.75, 1.25, 2.33, 3.17]
        for pos in accent_positions:
            if random.random() < 0.6:  # 60% chance
                instrument = random.choice(
                    [DrumInstrument.KICK, DrumInstrument.SNARE]
                )
                velocity = 75 + random.randint(-10, 15)
                new_beats.append(pattern.beats[0].copy())
                new_beats[-1].position = pos
                new_beats[-1].instrument = instrument
                new_beats[-1].velocity = velocity

        pattern.beats.extend(new_beats)

    def _create_brush_sweep_fill(self) -> Pattern:
        """Create brush sweep fill."""
        builder = PatternBuilder("jazz_brush_sweep")

        # Circular brush sweep simulation
        sweep_positions = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]
        for pos in sweep_positions:
            velocity = 60 + random.randint(-5, 10)
            builder.snare(pos, velocity)

        return builder.build()

    def _create_bebop_bombs_fill(self) -> Pattern:
        """Create bebop 'dropping bombs' fill."""
        builder = PatternBuilder("jazz_bebop_bombs")

        # Sporadic kick "bombs"
        bomb_positions = [0.25, 0.75, 1.5, 2.0, 2.75]
        for pos in bomb_positions:
            velocity = 90 + random.randint(-5, 10)
            builder.kick(pos, velocity)

        # Ride cymbal maintains time
        builder.ride(0.0, 85).ride(0.67, 78).ride(1.33, 85)

        return builder.build()

    def _create_latin_percussion_fill(self) -> Pattern:
        """Create Latin jazz percussion fill."""
        builder = PatternBuilder("jazz_latin_fill")

        # Clave-inspired pattern
        clave_positions = [0.0, 0.5, 2.0, 2.5, 3.25]
        for pos in clave_positions:
            velocity = 80 + random.randint(-5, 5)
            builder.snare(pos, velocity)  # Cross stick simulation

        return builder.build()
