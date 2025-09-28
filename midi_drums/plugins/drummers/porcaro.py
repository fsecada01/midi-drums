"""
Jeff Porcaro drummer plugin.

Implements Jeff Porcaro's signature drumming techniques based on research.
Known for his half-time shuffle, ghost notes mastery, studio precision,
and the famous "Rosanna Shuffle" - combining Bernard Purdie and Bonham.
"""

import random

from midi_drums.models.pattern import Beat, DrumInstrument, Pattern
from midi_drums.models.song import Fill
from midi_drums.plugins.base import DrummerPlugin

# Type annotations use built-in list for Python 3.9+


class PorcaroPlugin(DrummerPlugin):
    """Jeff Porcaro drummer style plugin.

    Characteristics:
    - Half-time shuffle mastery (Rosanna Shuffle)
    - Extensive ghost note vocabulary
    - Studio precision and articulation
    - Hi-hat technique and open/close patterns
    - Musical tasteful playing - music first approach
    - Genre versatility (rock, pop, studio work)
    """

    @property
    def drummer_name(self) -> str:
        return "porcaro"

    @property
    def compatible_genres(self) -> list[str]:
        return ["rock", "pop", "blues", "funk", "jazz"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Jeff Porcaro's signature style to a pattern.

        Args:
            pattern: Base pattern to modify

        Returns:
            Pattern with Porcaro's characteristic modifications
        """
        styled_pattern = pattern.copy()
        styled_pattern.name = f"{pattern.name}_porcaro"

        # 1. Add extensive ghost notes
        styled_pattern = self._add_ghost_notes(styled_pattern)

        # 2. Apply half-time shuffle feel where appropriate
        styled_pattern = self._apply_shuffle_feel(styled_pattern)

        # 3. Enhance hi-hat technique
        styled_pattern = self._enhance_hihat_technique(styled_pattern)

        # 4. Add studio precision and articulation
        styled_pattern = self._apply_studio_precision(styled_pattern)

        # 5. Apply tasteful musical approach
        styled_pattern = self._apply_musical_taste(styled_pattern)

        return styled_pattern

    def get_signature_fills(self) -> list[Fill]:
        """Return Jeff Porcaro's signature fill patterns."""
        fills = []

        # Famous Rosanna Shuffle pattern
        rosanna_fill = Fill(
            pattern=self._create_rosanna_shuffle(),
            trigger_probability=0.95,
            section_position="start",
        )
        fills.append(rosanna_fill)

        # Half-time shuffle variation
        half_time_fill = Fill(
            pattern=self._create_half_time_shuffle(),
            trigger_probability=0.8,
            section_position="middle",
        )
        fills.append(half_time_fill)

        # Ghost note showcase fill
        ghost_fill = Fill(
            pattern=self._create_ghost_note_fill(),
            trigger_probability=0.7,
            section_position="middle",
        )
        fills.append(ghost_fill)

        # Studio precision fill
        studio_fill = Fill(
            pattern=self._create_studio_precision_fill(),
            trigger_probability=0.6,
            section_position="end",
        )
        fills.append(studio_fill)

        return fills

    def _add_ghost_notes(self, pattern: Pattern) -> Pattern:
        """Add Porcaro's extensive ghost note vocabulary."""
        new_beats = list(pattern.beats)

        # Add ghost notes on snare between accents
        ghost_positions = [
            0.125,
            0.375,
            0.625,
            0.875,  # 16th note subdivisions
            1.125,
            1.375,
            1.625,
            1.875,
            2.125,
            2.375,
            2.625,
            2.875,
            3.125,
            3.375,
            3.625,
            3.875,
        ]

        for pos in ghost_positions:
            # Check if position doesn't conflict with existing snare
            conflict = any(
                beat.instrument == DrumInstrument.SNARE
                and abs(beat.position - pos) < 0.1
                for beat in pattern.beats
            )

            if not conflict and random.random() < 0.4:  # 40% chance
                ghost_note = Beat(
                    position=pos,
                    instrument=DrumInstrument.SNARE,
                    velocity=45 + random.randint(0, 15),  # Very soft ghost
                    duration=0.05,
                    ghost_note=True,
                )
                new_beats.append(ghost_note)

        pattern.beats = new_beats
        return pattern

    def _apply_shuffle_feel(self, pattern: Pattern) -> Pattern:
        """Apply half-time shuffle feel to appropriate patterns."""
        # Convert straight patterns to shuffle feel
        shuffle_beats = []

        for beat in pattern.beats:
            if beat.instrument == DrumInstrument.SNARE:
                # Half-time shuffle: strong snare only on beat 3
                if abs(beat.position - 2.0) < 0.1:  # Beat 3
                    # Keep the main backbeat strong
                    shuffle_beat = Beat(
                        position=beat.position,
                        instrument=beat.instrument,
                        velocity=min(127, beat.velocity + 10),
                        duration=beat.duration,
                    )
                    shuffle_beats.append(shuffle_beat)
                elif beat.position % 1.0 == 0:  # Other downbeats
                    # Make other snares lighter (ghost notes)
                    shuffle_beat = Beat(
                        position=beat.position,
                        instrument=beat.instrument,
                        velocity=max(30, beat.velocity - 40),
                        duration=beat.duration,
                        ghost_note=True,
                    )
                    shuffle_beats.append(shuffle_beat)
                else:
                    shuffle_beats.append(beat)
            else:
                shuffle_beats.append(beat)

        pattern.beats = shuffle_beats
        return pattern

    def _enhance_hihat_technique(self, pattern: Pattern) -> Pattern:
        """Enhance hi-hat technique with open/close articulation."""
        new_beats = list(pattern.beats)

        # Add sophisticated hi-hat patterns
        hihat_positions = [
            0.0,
            0.25,
            0.5,
            0.75,  # Quarter notes
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
            3.25,
            3.5,
            3.75,
        ]

        for i, pos in enumerate(hihat_positions):
            # Vary between closed and open hi-hat
            is_open = (i % 4 == 1 or i % 4 == 3) and random.random() < 0.3

            # Check for conflicts with existing hi-hat
            conflict = any(
                beat.instrument
                in [DrumInstrument.CLOSED_HH, DrumInstrument.OPEN_HH]
                and abs(beat.position - pos) < 0.1
                for beat in pattern.beats
            )

            if not conflict:
                instrument = (
                    DrumInstrument.OPEN_HH
                    if is_open
                    else DrumInstrument.CLOSED_HH
                )
                velocity = 70 + random.randint(-5, 10)

                new_beats.append(
                    Beat(
                        position=pos,
                        instrument=instrument,
                        velocity=velocity,
                        duration=0.1 if is_open else 0.05,
                    )
                )

        pattern.beats = new_beats
        return pattern

    def _apply_studio_precision(self, pattern: Pattern) -> Pattern:
        """Apply studio precision and articulation."""
        # Quantize timing for studio precision
        for beat in pattern.beats:
            # Slightly quantize but keep some human feel
            quantized_position = (
                round(beat.position * 16) / 16
            )  # 16th note grid

            # Add tiny bit of humanization (much less than live playing)
            humanization = random.uniform(-0.005, 0.005)
            beat.position = quantized_position + humanization

            # Consistent velocity for studio precision
            if beat.instrument == DrumInstrument.KICK:
                beat.velocity = min(127, beat.velocity + 5)  # Solid kick
            elif (
                beat.instrument == DrumInstrument.SNARE and not beat.ghost_note
            ):
                beat.velocity = min(127, beat.velocity + 8)  # Clear backbeat

        return pattern

    def _apply_musical_taste(self, pattern: Pattern) -> Pattern:
        """Apply Porcaro's musical taste - serve the song."""
        # Remove excessive fills - keep it musical
        fill_beats = [
            beat
            for beat in pattern.beats
            if beat.instrument
            in [DrumInstrument.MID_TOM, DrumInstrument.FLOOR_TOM]
        ]

        # Reduce tom fills by 30% for tasteful approach
        if len(fill_beats) > 2:
            beats_to_remove = random.sample(fill_beats, len(fill_beats) // 3)
            pattern.beats = [
                beat for beat in pattern.beats if beat not in beats_to_remove
            ]

        return pattern

    def _create_rosanna_shuffle(self) -> Pattern:
        """Create the famous Rosanna Shuffle pattern."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("porcaro_rosanna_shuffle")

        # Kick pattern with light pulse
        builder.kick(0.0, 100)
        builder.kick(2.0, 105)  # Slightly stronger on 3

        # Main snare backbeat on 3 (half-time feel)
        builder.snare(2.0, 110)

        # Ghost notes on triplet subdivisions
        ghost_positions = [0.33, 0.66, 1.33, 1.66, 2.33, 2.66, 3.33, 3.66]
        for pos in ghost_positions:
            if random.random() < 0.7:  # Not all ghosts present
                builder.pattern.add_beat(pos, DrumInstrument.SNARE, 45)

        # Hi-hat pattern with open/close articulation
        builder.hihat(0.0, 75)
        builder.hihat(0.5, 70, open=True)
        builder.hihat(1.0, 75)
        builder.hihat(1.5, 70, open=True)
        builder.hihat(2.0, 80)  # Accent with snare
        builder.hihat(2.5, 70, open=True)
        builder.hihat(3.0, 75)
        builder.hihat(3.5, 70, open=True)

        return builder.build()

    def _create_half_time_shuffle(self) -> Pattern:
        """Create half-time shuffle variation."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("porcaro_half_time_shuffle")

        # Basic half-time pattern
        builder.kick(0.0, 100)
        builder.snare(2.0, 110)  # Only one strong snare per bar

        # Shuffle feel with triplet subdivisions
        builder.kick(1.33, 95)  # Triplet feel

        # Ghost notes for groove
        ghost_positions = [0.5, 1.0, 1.5, 2.5, 3.0, 3.5]
        for pos in ghost_positions:
            builder.pattern.add_beat(pos, DrumInstrument.SNARE, 40)

        return builder.build()

    def _create_ghost_note_fill(self) -> Pattern:
        """Create ghost note showcase pattern."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("porcaro_ghost_notes")

        # Main pattern with extensive ghost notes
        builder.kick(0.0, 100)
        builder.snare(1.0, 110)  # Main accent
        builder.kick(2.0, 100)
        builder.snare(3.0, 110)  # Main accent

        # Dense ghost note pattern
        for i in range(16):  # 16th note subdivisions
            pos = i * 0.25
            if pos not in [0.0, 1.0, 2.0, 3.0]:  # Avoid main beats
                velocity = 35 + random.randint(0, 15)
                builder.pattern.add_beat(pos, DrumInstrument.SNARE, velocity)

        return builder.build()

    def _create_studio_precision_fill(self) -> Pattern:
        """Create precision studio fill pattern."""
        from midi_drums.models.pattern import PatternBuilder

        builder = PatternBuilder("porcaro_studio_precision")

        # Clean, articulate fill
        builder.snare(0.0, 105)
        builder.pattern.add_beat(0.25, DrumInstrument.MID_TOM, 100)
        builder.pattern.add_beat(0.5, DrumInstrument.MID_TOM, 102)
        builder.pattern.add_beat(0.75, DrumInstrument.FLOOR_TOM, 108)

        builder.kick(1.0, 110)  # Strong resolution

        return builder.build()
