"""Funk genre plugin with various funk substyles.

Based on research of James Brown, Parliament-Funkadelic, Bernard Purdie
shuffle, and classic funk patterns.
Emphasizes "the one", ghost notes, syncopated patterns, and deep pocket.
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


class FunkGenrePlugin(GenrePlugin):
    """Plugin for generating funk drum patterns."""

    @property
    def genre_name(self) -> str:
        return "funk"

    @property
    def supported_styles(self) -> list[str]:
        return [
            "classic",  # Classic James Brown style funk
            "pfunk",  # Parliament-Funkadelic P-Funk
            "shuffle",  # Bernard Purdie shuffle funk
            "new_orleans",  # New Orleans funk (Meters style)
            "fusion",  # Funk fusion with jazz elements
            "minimal",  # Minimal funk with space
            "heavy",  # Heavy, dense funk patterns
        ]

    def generate_pattern(
        self, section: str, parameters: GenerationParameters
    ) -> Pattern:
        """Generate funk pattern based on section and style."""
        style = parameters.style
        time_sig = TimeSignature(4, 4)  # Funk is typically 4/4

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
        """Get common funk fill patterns."""
        fills = []

        # "Funky Drummer" inspired fill
        funky_drummer_fill = Fill(
            pattern=self._create_funky_drummer_fill(),
            trigger_probability=0.9,
            section_position="end",
        )
        fills.append(funky_drummer_fill)

        # Ghost note showcase fill
        ghost_note_fill = Fill(
            pattern=self._create_ghost_note_fill(),
            trigger_probability=0.7,
            section_position="middle",
        )
        fills.append(ghost_note_fill)

        # P-Funk breakdown fill
        pfunk_fill = Fill(
            pattern=self._create_pfunk_breakdown_fill(),
            trigger_probability=0.8,
            section_position="start",
        )
        fills.append(pfunk_fill)

        return fills

    def _generate_intro_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate intro pattern for specified funk style."""
        if style == "classic":
            return self._classic_funk_intro(parameters, time_sig)
        elif style == "pfunk":
            return self._pfunk_intro(parameters, time_sig)
        elif style == "shuffle":
            return self._shuffle_funk_intro(parameters, time_sig)
        else:
            return self._classic_funk_intro(parameters, time_sig)

    def _generate_verse_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate verse pattern for specified funk style."""
        if style == "classic":
            return self._classic_funk_verse(parameters, time_sig)
        elif style == "pfunk":
            return self._pfunk_verse(parameters, time_sig)
        elif style == "shuffle":
            return self._shuffle_funk_verse(parameters, time_sig)
        elif style == "new_orleans":
            return self._new_orleans_funk_verse(parameters, time_sig)
        elif style == "fusion":
            return self._funk_fusion_verse(parameters, time_sig)
        elif style == "minimal":
            return self._minimal_funk_verse(parameters, time_sig)
        elif style == "heavy":
            return self._heavy_funk_verse(parameters, time_sig)
        else:
            return self._classic_funk_verse(parameters, time_sig)

    def _generate_chorus_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate chorus pattern - more intense with emphasis on 'the one'."""
        base_pattern = self._generate_verse_pattern(style, parameters, time_sig)
        base_pattern.name = base_pattern.name.replace("verse", "chorus")

        # Emphasize "the one" for chorus
        self._emphasize_the_one(base_pattern)

        return base_pattern

    def _generate_breakdown_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate breakdown pattern - stripped down to essentials."""
        builder = PatternBuilder(f"funk_{style}_breakdown")

        if style == "pfunk":
            # P-Funk breakdown with "the one"
            builder.kick(0.0, 127)  # Maximum emphasis on "the one"
            builder.snare(1.0, 110)  # Strong backbeat

            # Minimal hi-hat
            builder.hihat(0.5, 70).hihat(1.5, 70).hihat(2.5, 70).hihat(3.5, 70)
        else:
            # Classic funk breakdown
            builder.kick(0.0, 120)  # "The one"
            builder.snare(1.0, 105).snare(3.0, 105)

            # Single hi-hat pattern
            for i in range(8):
                builder.hihat(i * 0.5, 75)

        return builder.build()

    def _generate_bridge_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate bridge pattern - often more syncopated."""
        builder = PatternBuilder(f"funk_{style}_bridge")

        # Syncopated kick pattern
        builder.kick(0.0, 110).kick(0.75, 95).kick(2.25, 100).kick(3.5, 90)
        builder.snare(1.0, 105).snare(3.0, 105)

        # Syncopated hi-hat with opens
        hi_hat_pattern = [0.0, 0.25, 0.75, 1.25, 1.75, 2.0, 2.75, 3.25, 3.75]
        for i, pos in enumerate(hi_hat_pattern):
            open_hihat = i % 3 == 2  # Every third hit is open
            velocity = 80 + random.randint(-5, 5)
            builder.hihat(pos, velocity, open=open_hihat)

        return builder.build()

    def _generate_outro_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate outro pattern."""
        if style == "minimal":
            # Minimal outro
            builder = PatternBuilder(f"funk_{style}_outro")
            builder.kick(0.0, 100)  # Just "the one"
            return builder.build()
        else:
            # Use verse pattern with final accent
            base_pattern = self._generate_verse_pattern(
                style, parameters, time_sig
            )
            base_pattern.name = base_pattern.name.replace("verse", "outro")

            # Add final emphasis
            if base_pattern.beats:
                final_accent = Beat(
                    position=3.75,
                    instrument=DrumInstrument.CRASH,
                    velocity=115,
                    duration=0.5,
                )
                base_pattern.beats.append(final_accent)

            return base_pattern

    # Style-specific pattern implementations

    def _classic_funk_intro(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Classic James Brown style funk intro."""
        builder = PatternBuilder("funk_classic_intro")

        # Build up to "the one"
        builder.snare(2.0, 90).snare(2.5, 95).snare(3.0, 100).snare(3.5, 105)

        # Hi-hat pattern
        for i in range(8):
            velocity = 70 + (i * 2)  # Building intensity
            builder.hihat(i * 0.5, min(127, velocity))

        return builder.build()

    def _classic_funk_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Classic funk verse based on Clyde Stubblefield's "Funky Drummer"."""
        builder = PatternBuilder("funk_classic_verse")

        # "The one" - emphasis on beat 1
        builder.kick(0.0, 115)

        # Syncopated kick pattern
        builder.kick(0.75, 90).kick(3.25, 95)  # 16th note syncopation

        # Snare backbeat with ghost notes
        builder.snare(1.0, 110)  # Strong backbeat
        builder.snare(3.0, 110)  # Strong backbeat

        # Ghost notes (crucial for funk feel)
        ghost_positions = [0.25, 0.5, 1.25, 1.75, 2.25, 2.5, 2.75, 3.75]
        for pos in ghost_positions:
            if random.random() < 0.7:  # 70% chance for each ghost note
                velocity = 45 + random.randint(-10, 15)  # Very quiet
                builder.pattern.add_beat(
                    pos,
                    DrumInstrument.SNARE,
                    max(30, velocity),
                    ghost_note=True,
                )

        # 16th note hi-hat pattern with opens
        for i in range(16):
            pos = i * 0.25
            # Open hi-hat on 'e' of beats 2 and 4 (Stubblefield signature)
            open_hihat = pos in [1.25, 3.25]
            velocity = 75 + random.randint(-3, 7)

            if open_hihat:
                velocity += 5  # Slightly louder for opens

            builder.hihat(pos, velocity, open=open_hihat)

        return builder.build()

    def _pfunk_intro(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Parliament-Funkadelic P-Funk intro."""
        builder = PatternBuilder("funk_pfunk_intro")

        # P-Funk often starts with "the one"
        builder.kick(0.0, 120)
        builder.snare(0.0, 100)  # Snare with kick for emphasis

        # Sparse pattern building to full groove
        builder.hihat(0.5, 60).hihat(1.5, 65).hihat(2.5, 70)

        return builder.build()

    def _pfunk_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Parliament-Funkadelic P-Funk verse."""
        builder = PatternBuilder("funk_pfunk_verse")

        # Maximum emphasis on "the one"
        builder.kick(0.0, 120)  # "The one" is everything
        builder.snare(0.0, 100)  # Reinforce with snare

        # Complex syncopated kick pattern
        p_funk_kicks = [0.75, 1.5, 2.25, 3.5]
        for pos in p_funk_kicks:
            velocity = 95 + random.randint(-5, 10)
            builder.kick(pos, velocity)

        # Snare pattern
        builder.snare(1.0, 105).snare(3.0, 105)
        builder.snare(2.75, 85)  # Syncopated snare

        # Intricate hi-hat work
        hi_hat_pattern = [0.25, 0.5, 1.25, 1.75, 2.0, 2.5, 3.25, 3.75]
        for i, pos in enumerate(hi_hat_pattern):
            open_hihat = i % 4 == 1  # Pattern of opens
            velocity = 78 + random.randint(-5, 8)
            builder.hihat(pos, velocity, open=open_hihat)

        return builder.build()

    def _shuffle_funk_intro(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Bernard Purdie shuffle funk intro."""
        builder = PatternBuilder("funk_shuffle_intro")

        # Purdie shuffle setup
        builder.kick(0.0, 100)
        builder.snare(1.0, 95)

        # Shuffle hi-hat
        shuffle_positions = [0.0, 0.67, 1.0, 1.67, 2.0, 2.67, 3.0, 3.67]
        for pos in shuffle_positions:
            builder.hihat(pos, 70)

        return builder.build()

    def _shuffle_funk_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Bernard Purdie shuffle funk verse."""
        builder = PatternBuilder("funk_shuffle_verse")

        # The Purdie Shuffle kick pattern
        builder.kick(0.0, 110)  # Strong "the one"
        builder.kick(2.5, 95)  # Shuffle kick

        # Linear snare pattern (Purdie signature)
        builder.snare(1.0, 105)
        builder.snare(2.0, 100)  # Linear approach
        builder.snare(3.0, 105)

        # Shuffle ghost notes
        ghost_positions = [0.33, 1.33, 2.33, 3.33]  # Triplet feel ghosts
        for pos in ghost_positions:
            velocity = 50 + random.randint(-10, 10)
            builder.pattern.add_beat(
                pos, DrumInstrument.SNARE, velocity, ghost_note=True
            )

        # Shuffle hi-hat pattern
        shuffle_hi_hat = [0.0, 0.67, 1.0, 1.67, 2.0, 2.67, 3.0, 3.67]
        for i, pos in enumerate(shuffle_hi_hat):
            velocity = 75 + random.randint(-3, 7)
            # Accent pattern for shuffle
            if i % 2 == 0:
                velocity += 5
            builder.hihat(pos, velocity)

        return builder.build()

    def _new_orleans_funk_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """New Orleans funk verse (Meters style)."""
        builder = PatternBuilder("funk_new_orleans_verse")

        # Second line influenced kick pattern
        builder.kick(0.0, 110).kick(2.0, 105)
        builder.kick(1.75, 90).kick(3.5, 95)  # Syncopated kicks

        # Snare with cross-stick feel
        builder.snare(1.0, 100).snare(3.0, 100)
        builder.snare(0.5, 75).snare(2.5, 80)  # Additional snares

        # Relaxed hi-hat
        for i in range(8):
            pos = i * 0.5
            velocity = 70 + random.randint(-5, 5)
            builder.hihat(pos, velocity)

        return builder.build()

    def _funk_fusion_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Funk fusion verse with jazz elements."""
        builder = PatternBuilder("funk_fusion_verse")

        # Fusion kick pattern
        builder.kick(0.0, 110).kick(0.75, 95).kick(2.25, 100)

        # Jazz-influenced snare with linear concepts
        builder.snare(1.0, 105).snare(2.5, 85).snare(3.0, 105)

        # 16th note hi-hat with fusion feel
        for i in range(16):
            pos = i * 0.25
            velocity = 72 + random.randint(-3, 8)
            # Fusion accent pattern
            if i % 4 == 0:
                velocity += 8
            builder.hihat(pos, min(127, velocity))

        return builder.build()

    def _minimal_funk_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Minimal funk verse with lots of space."""
        builder = PatternBuilder("funk_minimal_verse")

        # Just the essentials
        builder.kick(0.0, 115)  # "The one"
        builder.snare(1.0, 105).snare(3.0, 105)  # Backbeat

        # Sparse hi-hat
        builder.hihat(0.5, 70).hihat(1.5, 70).hihat(2.5, 70).hihat(3.5, 70)

        # Single ghost note for feel
        builder.pattern.add_beat(
            2.25, DrumInstrument.SNARE, 55, ghost_note=True
        )

        return builder.build()

    def _heavy_funk_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Heavy, dense funk verse."""
        builder = PatternBuilder("funk_heavy_verse")

        # Dense kick pattern
        heavy_kicks = [0.0, 0.5, 0.75, 1.5, 2.0, 2.25, 2.75, 3.25, 3.75]
        for pos in heavy_kicks:
            velocity = 105 + random.randint(-5, 10)
            builder.kick(pos, velocity)

        # Aggressive snare with many ghosts
        builder.snare(1.0, 115).snare(3.0, 115)

        # Dense ghost note pattern
        ghost_positions = [
            0.25,
            0.75,
            1.25,
            1.5,
            1.75,
            2.25,
            2.5,
            2.75,
            3.5,
            3.75,
        ]
        for pos in ghost_positions:
            velocity = 50 + random.randint(-15, 20)
            builder.pattern.add_beat(
                pos, DrumInstrument.SNARE, max(35, velocity), ghost_note=True
            )

        # Constant 16th note hi-hat
        for i in range(16):
            pos = i * 0.25
            velocity = 75 + random.randint(-5, 10)
            builder.hihat(pos, velocity)

        return builder.build()

    def _emphasize_the_one(self, pattern: Pattern) -> None:
        """Emphasize 'the one' in existing pattern."""
        for beat in pattern.beats:
            if beat.position == 0.0:  # Beat 1
                if beat.instrument == DrumInstrument.KICK:
                    beat.velocity = min(127, beat.velocity + 15)
                elif beat.instrument == DrumInstrument.SNARE:
                    beat.velocity = min(127, beat.velocity + 10)

    def _create_funky_drummer_fill(self) -> Pattern:
        """Create 'Funky Drummer' inspired fill."""
        builder = PatternBuilder("funk_funky_drummer_fill")

        # Rapid snare pattern inspired by Stubblefield
        snare_pattern = [0.0, 0.125, 0.25, 0.5, 0.625, 0.75, 0.875]
        for pos in snare_pattern:
            velocity = 85 + random.randint(-5, 15)
            builder.snare(pos, velocity)

        # Hi-hat maintains 16th note feel
        for i in range(8):
            pos = i * 0.125
            builder.hihat(pos, 75)

        return builder.build()

    def _create_ghost_note_fill(self) -> Pattern:
        """Create ghost note showcase fill."""
        builder = PatternBuilder("funk_ghost_note_fill")

        # Main accents
        builder.snare(0.0, 100).snare(0.5, 105).snare(1.0, 110)

        # Surrounding ghost notes
        ghost_positions = [0.125, 0.25, 0.375, 0.625, 0.75, 0.875]
        for pos in ghost_positions:
            velocity = 45 + random.randint(-10, 15)
            builder.pattern.add_beat(
                pos, DrumInstrument.SNARE, max(30, velocity), ghost_note=True
            )

        return builder.build()

    def _create_pfunk_breakdown_fill(self) -> Pattern:
        """Create P-Funk breakdown fill."""
        builder = PatternBuilder("funk_pfunk_breakdown_fill")

        # Emphasis on "the one"
        builder.kick(0.0, 127)
        builder.snare(0.0, 115)

        # Syncopated pattern leading back
        builder.kick(0.75, 100)
        builder.snare(1.5, 90)

        return builder.build()
