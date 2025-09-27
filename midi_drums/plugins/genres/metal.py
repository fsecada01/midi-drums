"""Metal genre plugin with various metal substyles."""

from typing import List
import random

from ..base import GenrePlugin
from ...models.pattern import Pattern, Beat, DrumInstrument, TimeSignature, PatternBuilder
from ...models.song import GenerationParameters, Fill


class MetalGenrePlugin(GenrePlugin):
    """Plugin for generating metal drum patterns."""

    @property
    def genre_name(self) -> str:
        return "metal"

    @property
    def supported_styles(self) -> List[str]:
        return ["heavy", "death", "power", "progressive", "thrash", "doom", "breakdown"]

    def generate_pattern(self, section: str, parameters: GenerationParameters) -> Pattern:
        """Generate metal pattern based on section and style."""
        style = parameters.style
        time_sig = TimeSignature(4, 4)  # Most metal is 4/4

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
        elif section in ["outro", "ending"]:
            return self._generate_outro_pattern(style, parameters, time_sig)
        else:
            # Default to verse pattern
            return self._generate_verse_pattern(style, parameters, time_sig)

    def get_common_fills(self) -> List[Fill]:
        """Get common metal fill patterns."""
        fills = []

        # Tom roll fill
        tom_roll = PatternBuilder("metal_tom_roll")
        for i in range(16):  # 16th notes
            pos = i * 0.25
            instrument = DrumInstrument.SNARE if i % 3 == 0 else (
                DrumInstrument.MID_TOM if i % 2 == 0 else DrumInstrument.FLOOR_TOM
            )
            velocity = 100 + random.randint(-10, 15)
            tom_roll.pattern.add_beat(pos, instrument, velocity)
        fills.append(Fill(tom_roll.build(), 0.8))

        # Blast beat fill
        blast_fill = PatternBuilder("metal_blast_fill")
        for i in range(8):  # 8th notes
            pos = i * 0.5
            blast_fill.kick(pos, 110).snare(pos + 0.25, 115)
        fills.append(Fill(blast_fill.build(), 0.6))

        return fills

    def _generate_intro_pattern(self, style: str, params: GenerationParameters,
                               time_sig: TimeSignature) -> Pattern:
        """Generate intro pattern - typically builds energy."""
        builder = PatternBuilder(f"metal_{style}_intro", time_sig)

        # Crash on beat 1
        builder.crash(0.0, 115)

        if style == "death":
            # Double kick quarters with snare on 2 and 4
            for i in [0.0, 1.0, 2.0, 3.0]:
                builder.kick(i, 110)
                builder.kick(i + 0.5, 105)  # Double kick
            builder.snare(1.0, 120).snare(3.0, 120)

        else:
            # Standard heavy intro - kick quarters, snare on 3
            for i in [0.0, 1.0, 2.0, 3.0]:
                builder.kick(i, 110)
            builder.snare(2.0, 115)  # Rimshot effect

        return builder.build()

    def _generate_verse_pattern(self, style: str, params: GenerationParameters,
                               time_sig: TimeSignature) -> Pattern:
        """Generate verse pattern based on style."""
        builder = PatternBuilder(f"metal_{style}_verse", time_sig)

        if style == "death":
            return self._death_metal_verse(builder, params)
        elif style == "power":
            return self._power_metal_verse(builder, params)
        elif style == "doom":
            return self._doom_metal_verse(builder, params)
        elif style == "progressive":
            return self._progressive_metal_verse(builder, params)
        else:
            return self._heavy_metal_verse(builder, params)

    def _generate_chorus_pattern(self, style: str, params: GenerationParameters,
                                time_sig: TimeSignature) -> Pattern:
        """Generate chorus pattern - typically more intense than verse."""
        builder = PatternBuilder(f"metal_{style}_chorus", time_sig)

        if style == "death":
            return self._death_metal_chorus(builder, params)
        elif style == "power":
            return self._power_metal_chorus(builder, params)
        else:
            return self._heavy_metal_chorus(builder, params)

    def _generate_breakdown_pattern(self, style: str, params: GenerationParameters,
                                   time_sig: TimeSignature) -> Pattern:
        """Generate breakdown pattern - syncopated, heavy."""
        builder = PatternBuilder(f"metal_{style}_breakdown", time_sig)

        # Breakdown pattern: kick on 1, 2.5, 3.5
        builder.kick(0.0, 120)
        builder.kick(1.5, 115)
        builder.kick(2.5, 115)

        # Rimshot on 2
        builder.pattern.add_beat(2.0, DrumInstrument.RIM, 115)

        # Toms for groove
        builder.pattern.add_beat(1.0, DrumInstrument.MID_TOM, 105)
        builder.pattern.add_beat(3.0, DrumInstrument.FLOOR_TOM, 105)

        return builder.build()

    def _generate_bridge_pattern(self, style: str, params: GenerationParameters,
                                time_sig: TimeSignature) -> Pattern:
        """Generate bridge pattern - often simpler or different from verse/chorus."""
        # For simplicity, use a modified verse pattern
        pattern = self._generate_verse_pattern(style, params, time_sig)
        pattern.name = f"metal_{style}_bridge"

        # Reduce complexity slightly
        reduced_beats = []
        for beat in pattern.beats:
            if beat.instrument == DrumInstrument.CLOSED_HH:
                # Reduce hi-hat density
                if beat.position % 1.0 == 0:  # Keep only quarter notes
                    reduced_beats.append(beat)
            else:
                reduced_beats.append(beat)

        pattern.beats = reduced_beats
        return pattern

    def _generate_outro_pattern(self, style: str, params: GenerationParameters,
                               time_sig: TimeSignature) -> Pattern:
        """Generate outro pattern."""
        builder = PatternBuilder(f"metal_{style}_outro", time_sig)

        # Descending tom fill pattern
        builder.pattern.add_beat(0.0, DrumInstrument.FLOOR_TOM, 110)
        builder.pattern.add_beat(1.0, DrumInstrument.MID_TOM, 105)
        builder.pattern.add_beat(2.0, DrumInstrument.SNARE, 115)
        builder.pattern.add_beat(3.0, DrumInstrument.FLOOR_TOM, 110)

        # Final crash
        builder.crash(3.75, 120)

        return builder.build()

    # Style-specific implementations
    def _heavy_metal_verse(self, builder: PatternBuilder, params: GenerationParameters) -> Pattern:
        """Classic heavy metal verse pattern."""
        # Kick on 1, 1.75, 3
        builder.kick(0.0, 110)
        builder.kick(0.75, 105)
        builder.kick(2.0, 110)

        # Snare on 2 and 4
        builder.snare(1.0, 115)
        builder.snare(3.0, 115)

        # Hi-hat 8ths
        for i in range(8):
            builder.hihat(i * 0.5, 75 + random.randint(-5, 10))

        return builder.build()

    def _death_metal_verse(self, builder: PatternBuilder, params: GenerationParameters) -> Pattern:
        """Death metal verse with blast beats."""
        # Blast beat pattern - alternating kick/snare on 16ths
        for i in range(8):
            pos = i * 0.5
            builder.kick(pos, 110 + random.randint(-5, 10))
            builder.snare(pos + 0.25, 115 + random.randint(-5, 10))

        # Sparse hi-hat for texture
        for i in [0.0, 2.0]:
            builder.hihat(i, 80, open=(i == 2.0))

        return builder.build()

    def _power_metal_verse(self, builder: PatternBuilder, params: GenerationParameters) -> Pattern:
        """Power metal verse - driving and melodic."""
        # Steady kick quarters
        for i in [0.0, 1.0, 2.0, 3.0]:
            builder.kick(i, 105)

        # Snare on 2 and 4 with some ghost notes
        builder.snare(1.0, 115)
        builder.snare(3.0, 115)
        builder.snare(1.5, 60)  # Ghost note

        # Ride cymbal for driving feel
        for i in range(4):
            builder.ride(i, 80)

        return builder.build()

    def _doom_metal_verse(self, builder: PatternBuilder, params: GenerationParameters) -> Pattern:
        """Doom metal verse - slow and heavy."""
        # Simple but heavy kick pattern
        builder.kick(0.0, 120)
        builder.kick(2.0, 120)

        # Powerful snare on 2 and 4
        builder.snare(1.0, 125)
        builder.snare(3.0, 125)

        # Minimal hi-hat
        builder.hihat(0.0, 70)
        builder.hihat(2.0, 70)

        return builder.build()

    def _progressive_metal_verse(self, builder: PatternBuilder, params: GenerationParameters) -> Pattern:
        """Progressive metal verse - complex timing."""
        # Complex kick pattern
        for pos in [0.0, 0.75, 1.5, 2.25, 3.0]:
            builder.kick(pos, 105 + random.randint(-5, 10))

        # Snare on traditional beats plus syncopation
        builder.snare(1.0, 115)
        builder.snare(2.75, 100)  # Syncopated
        builder.snare(3.0, 115)

        # Complex hi-hat pattern
        for i in range(16):
            if i % 3 != 0:  # Skip every 3rd hit for complexity
                builder.hihat(i * 0.25, 70 + random.randint(-10, 15))

        return builder.build()

    def _heavy_metal_chorus(self, builder: PatternBuilder, params: GenerationParameters) -> Pattern:
        """Heavy metal chorus - double kick shuffle."""
        # Double kick pattern
        for beat in range(4):
            base_pos = beat * 1.0
            builder.kick(base_pos, 110)
            builder.kick(base_pos + 0.5, 105)

        # Snare on 2 and 4
        builder.snare(1.0, 120)
        builder.snare(3.0, 120)

        # Ride for power
        for i in range(4):
            builder.ride(i, 85)

        return builder.build()

    def _death_metal_chorus(self, builder: PatternBuilder, params: GenerationParameters) -> Pattern:
        """Death metal chorus - intense blast beats."""
        # Faster blast beat for chorus intensity
        for i in range(16):
            pos = i * 0.25
            if i % 2 == 0:
                builder.kick(pos, 115)
            else:
                builder.snare(pos, 120)

        # Crash accents
        builder.crash(0.0, 120)
        builder.crash(2.0, 115)

        return builder.build()

    def _power_metal_chorus(self, builder: PatternBuilder, params: GenerationParameters) -> Pattern:
        """Power metal chorus - anthemic and driving."""
        # Driving double kick
        for beat in range(4):
            builder.kick(beat, 110)
            if beat < 3:  # Don't double the last beat
                builder.kick(beat + 0.5, 100)

        # Strong snare backbeat
        builder.snare(1.0, 120)
        builder.snare(3.0, 120)

        # Crash on 1 and 3 for power
        builder.crash(0.0, 115)
        builder.crash(2.0, 110)

        # Ride bell for texture
        builder.pattern.add_beat(1.5, DrumInstrument.RIDE_BELL, 90)
        builder.pattern.add_beat(3.5, DrumInstrument.RIDE_BELL, 90)

        return builder.build()