"""Rock genre plugin with various rock substyles.

Based on research of classic rock, blues rock, alternative, progressive,
and punk rock patterns.
Emphasizes backbeat snare on 2 and 4, with various kick patterns and
cymbal techniques.
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


class RockGenrePlugin(GenrePlugin):
    """Plugin for generating rock drum patterns."""

    @property
    def genre_name(self) -> str:
        return "rock"

    @property
    def supported_styles(self) -> list[str]:
        return [
            "classic",  # 70s classic rock (Led Zeppelin, Deep Purple)
            "blues",  # Blues rock with shuffles and triplets
            "alternative",  # 90s alternative rock
            "progressive",  # Complex progressive rock patterns
            "punk",  # Fast, aggressive punk rock
            "hard",  # Hard rock with heavy emphasis
            "pop",  # Pop rock with clean patterns
        ]

    def generate_pattern(
        self, section: str, parameters: GenerationParameters
    ) -> Pattern:
        """Generate rock pattern based on section and style."""
        style = parameters.style
        time_sig = TimeSignature(4, 4)  # Most rock is 4/4

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
        """Get common rock fill patterns."""
        fills = []

        # Classic rock tom fill
        classic_fill = Fill(
            pattern=self._create_classic_rock_fill(),
            trigger_probability=0.8,
            section_position="end",
        )
        fills.append(classic_fill)

        # Snare roll fill
        snare_roll_fill = Fill(
            pattern=self._create_snare_roll_fill(),
            trigger_probability=0.7,
            section_position="middle",
        )
        fills.append(snare_roll_fill)

        # Crash accent fill
        crash_fill = Fill(
            pattern=self._create_crash_accent_fill(),
            trigger_probability=0.9,
            section_position="start",
        )
        fills.append(crash_fill)

        return fills

    def _generate_intro_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate intro pattern for specified rock style."""
        if style == "classic":
            return self._classic_rock_intro(parameters, time_sig)
        elif style == "blues":
            return self._blues_rock_intro(parameters, time_sig)
        elif style == "punk":
            return self._punk_rock_intro(parameters, time_sig)
        elif style == "progressive":
            return self._progressive_rock_intro(parameters, time_sig)
        else:
            # Default to classic for unknown styles
            return self._classic_rock_intro(parameters, time_sig)

    def _generate_verse_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate verse pattern for specified rock style."""
        if style == "classic":
            return self._classic_rock_verse(parameters, time_sig)
        elif style == "blues":
            return self._blues_rock_verse(parameters, time_sig)
        elif style == "alternative":
            return self._alternative_rock_verse(parameters, time_sig)
        elif style == "progressive":
            return self._progressive_rock_verse(parameters, time_sig)
        elif style == "punk":
            return self._punk_rock_verse(parameters, time_sig)
        elif style == "hard":
            return self._hard_rock_verse(parameters, time_sig)
        elif style == "pop":
            return self._pop_rock_verse(parameters, time_sig)
        else:
            return self._classic_rock_verse(parameters, time_sig)

    def _generate_chorus_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate chorus pattern - typically more intense than verse."""
        base_pattern = self._generate_verse_pattern(style, parameters, time_sig)
        base_pattern.name = base_pattern.name.replace("verse", "chorus")

        # Make chorus more intense
        for beat in base_pattern.beats:
            if beat.instrument in [DrumInstrument.KICK, DrumInstrument.SNARE]:
                beat.velocity = min(127, beat.velocity + 10)
            elif beat.instrument == DrumInstrument.CRASH:
                beat.velocity = min(127, beat.velocity + 5)

        # Add crashes on strong beats for emphasis
        if random.random() < 0.6 and base_pattern.beats:  # 60% chance
            crash_beat = Beat(
                position=0.0,  # On the downbeat
                instrument=DrumInstrument.CRASH,
                velocity=110,
                duration=0.5,
            )
            base_pattern.beats.append(crash_beat)

        return base_pattern

    def _generate_breakdown_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate breakdown pattern - simplified and heavy."""
        builder = PatternBuilder(f"rock_{style}_breakdown")

        # Simple, heavy breakdown pattern
        builder.kick(0.0, 120).kick(2.0, 120)  # Heavy kicks on 1 and 3
        builder.snare(1.0, 115).snare(3.0, 115)  # Snare on 2 and 4

        # Minimal hi-hat or ride
        if style == "punk":
            # Open hi-hat for punk energy
            for i in range(4):
                builder.hihat(i * 1.0, 90, open=True)
        else:
            # Ride cymbal for other styles
            for i in range(8):
                builder.ride(i * 0.5, 75)

        return builder.build()

    def _generate_bridge_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate bridge pattern - usually different from verse/chorus."""
        builder = PatternBuilder(f"rock_{style}_bridge")

        # Bridge patterns are often more syncopated
        builder.kick(0.0, 100).kick(1.5, 95).kick(3.25, 90)
        builder.snare(1.0, 105).snare(3.0, 105)

        # Use ride cymbal for different texture
        ride_pattern = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
        for pos in ride_pattern:
            builder.ride(pos, 80 + random.randint(-5, 5))

        return builder.build()

    def _generate_outro_pattern(
        self,
        style: str,
        parameters: GenerationParameters,
        time_sig: TimeSignature,
    ) -> Pattern:
        """Generate outro pattern."""
        if style == "punk":
            # Punk outros are often just stops
            builder = PatternBuilder(f"rock_{style}_outro")
            builder.kick(0.0, 127).snare(0.0, 127).crash(0.0, 127)
            return builder.build()
        else:
            # Use verse pattern with crash ending
            base_pattern = self._generate_verse_pattern(
                style, parameters, time_sig
            )
            base_pattern.name = base_pattern.name.replace("verse", "outro")

            # Add final crash
            if base_pattern.beats:
                final_crash = Beat(
                    position=3.75,  # End of measure
                    instrument=DrumInstrument.CRASH,
                    velocity=120,
                    duration=0.5,
                )
                base_pattern.beats.append(final_crash)

            return base_pattern

    # Style-specific pattern implementations

    def _classic_rock_intro(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Classic 70s rock intro pattern."""
        builder = PatternBuilder("rock_classic_intro")

        # Simple build-up pattern
        builder.kick(0.0, 90).kick(2.0, 95)
        builder.snare(1.0, 85).snare(3.0, 90)

        # Hi-hat eighth notes
        for i in range(8):
            builder.hihat(i * 0.5, 70)

        return builder.build()

    def _classic_rock_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Classic rock verse - the foundation pattern."""
        builder = PatternBuilder("rock_classic_verse")

        # The classic rock foundation: kick on 1&3, snare on 2&4
        builder.kick(0.0, 105).kick(2.0, 105)
        builder.snare(1.0, 110).snare(3.0, 110)

        # Hi-hat eighth notes with occasional opens
        for i in range(8):
            velocity = 75 + random.randint(-5, 5)
            open_hihat = (
                i in [3, 7] and random.random() < 0.3
            )  # Occasional opens
            builder.hihat(i * 0.5, velocity, open=open_hihat)

        return builder.build()

    def _blues_rock_intro(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Blues rock intro with shuffle feel."""
        builder = PatternBuilder("rock_blues_intro")

        # Shuffle pattern - swing the eighth notes
        swing_ratio = 0.67  # Swing feel

        # Kick pattern with blues feel
        builder.kick(0.0, 90)
        builder.kick(2.0 + 0.1, 95)  # Slightly behind beat 3

        # Snare on 2 and 4 with ghost notes
        builder.snare(1.0, 85)
        builder.snare(3.0, 90)
        builder.pattern.add_beat(
            1.75, DrumInstrument.SNARE, 50, ghost_note=True
        )  # Ghost note

        # Shuffled hi-hat
        shuffle_positions = [
            0.0,
            swing_ratio,
            1.0,
            1.0 + swing_ratio,
            2.0,
            2.0 + swing_ratio,
            3.0,
            3.0 + swing_ratio,
        ]
        for pos in shuffle_positions:
            builder.hihat(pos, 70)

        return builder.build()

    def _blues_rock_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Blues rock verse with shuffle and triplet feel."""
        builder = PatternBuilder("rock_blues_verse")

        # Basic blues shuffle
        builder.kick(0.0, 100).kick(2.5, 95)
        builder.snare(1.0, 105).snare(3.0, 105)

        # Add ghost notes for blues feel
        # Add ghost notes using add_beat with ghost_note flag
        builder.pattern.add_beat(
            0.75, DrumInstrument.SNARE, 60, ghost_note=True
        )
        builder.pattern.add_beat(
            2.25, DrumInstrument.SNARE, 65, ghost_note=True
        )

        # Shuffle hi-hat pattern
        swing_positions = [0.0, 0.67, 1.0, 1.67, 2.0, 2.67, 3.0, 3.67]
        for i, pos in enumerate(swing_positions):
            velocity = 75 if i % 2 == 0 else 60  # Accent on strong beats
            builder.hihat(pos, velocity)

        return builder.build()

    def _alternative_rock_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """90s alternative rock verse pattern."""
        builder = PatternBuilder("rock_alternative_verse")

        # Alternative rock often uses syncopated kick patterns
        builder.kick(0.0, 100).kick(1.75, 95).kick(2.5, 90)
        builder.snare(1.0, 105).snare(3.0, 105)

        # 16th note hi-hat pattern
        for i in range(16):
            pos = i * 0.25
            velocity = 70 + random.randint(-5, 5)
            # Accent every 4th hit
            if i % 4 == 0:
                velocity += 10
            builder.hihat(pos, min(127, velocity))

        return builder.build()

    def _progressive_rock_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Progressive rock with complex patterns."""
        builder = PatternBuilder("rock_progressive_verse")

        # More complex kick pattern
        kick_pattern = [0.0, 0.75, 1.5, 2.25, 3.0]
        for pos in kick_pattern:
            builder.kick(pos, 100 + random.randint(-5, 5))

        # Snare with variations
        builder.snare(1.0, 110).snare(3.0, 110)
        builder.snare(2.5, 90)  # Additional snare

        # Ride cymbal instead of hi-hat for prog feel
        for i in range(8):
            pos = i * 0.5
            velocity = 80 + random.randint(-3, 7)
            builder.ride(pos, velocity)

        # Add bell accents
        if random.random() < 0.4:
            builder.ride_bell(1.0, 95)

        return builder.build()

    def _punk_rock_intro(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Punk rock intro - simple and aggressive."""
        builder = PatternBuilder("rock_punk_intro")

        # Count-in style
        for i in range(4):
            builder.snare(i * 1.0, 100 + (i * 5))

        return builder.build()

    def _punk_rock_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Punk rock verse - fast and aggressive."""
        builder = PatternBuilder("rock_punk_verse")

        # Fast kick pattern
        builder.kick(0.0, 110).kick(0.5, 105).kick(2.0, 110).kick(2.5, 105)

        # Snare on every beat (punk characteristic)
        builder.snare(1.0, 115).snare(1.5, 110).snare(3.0, 115).snare(3.5, 110)

        # "Sloshy" open hi-hats
        for i in range(8):
            builder.hihat(i * 0.5, 95, open=True)

        return builder.build()

    def _hard_rock_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Hard rock verse with heavy emphasis."""
        builder = PatternBuilder("rock_hard_verse")

        # Powerful kick pattern
        builder.kick(0.0, 115).kick(2.0, 115).kick(3.5, 100)
        builder.snare(1.0, 120).snare(3.0, 120)  # Heavy snare

        # Driving hi-hat
        for i in range(8):
            velocity = 85 + random.randint(-5, 5)
            builder.hihat(i * 0.5, velocity)

        # Add crash accents
        if random.random() < 0.3:
            builder.crash(0.0, 110)

        return builder.build()

    def _pop_rock_verse(
        self, parameters: GenerationParameters, time_sig: TimeSignature
    ) -> Pattern:
        """Pop rock verse - clean and tight."""
        builder = PatternBuilder("rock_pop_verse")

        # Clean, simple pattern
        builder.kick(0.0, 100).kick(2.0, 100)
        builder.snare(1.0, 105).snare(3.0, 105)

        # Tight hi-hat pattern
        for i in range(8):
            velocity = 75
            if i % 2 == 0:  # Accent on beats
                velocity = 85
            builder.hihat(i * 0.5, velocity)

        return builder.build()

    def _create_classic_rock_fill(self) -> Pattern:
        """Create classic rock tom fill."""
        builder = PatternBuilder("rock_classic_fill")

        # Tom-tom cascade
        builder.pattern.add_beat(0.0, DrumInstrument.MID_TOM, 95)
        builder.pattern.add_beat(0.25, DrumInstrument.MID_TOM, 100)
        builder.pattern.add_beat(0.5, DrumInstrument.FLOOR_TOM, 105)
        builder.pattern.add_beat(0.75, DrumInstrument.FLOOR_TOM, 100)

        # Crash to end
        builder.crash(1.0, 110)
        builder.kick(1.0, 110)  # Kick with crash

        return builder.build()

    def _create_snare_roll_fill(self) -> Pattern:
        """Create snare roll fill."""
        builder = PatternBuilder("rock_snare_roll")

        # 32nd note snare roll
        for i in range(8):
            pos = i * 0.125
            velocity = 85 + (i * 2)  # Building intensity
            builder.snare(pos, min(127, velocity))

        return builder.build()

    def _create_crash_accent_fill(self) -> Pattern:
        """Create crash accent fill."""
        builder = PatternBuilder("rock_crash_accent")

        # Simple crash with kick
        builder.crash(0.0, 115)
        builder.kick(0.0, 115)

        return builder.build()
