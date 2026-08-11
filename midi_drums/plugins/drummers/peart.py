"""Neil Peart drummer plugin.

Implements Neil Peart's (Rush) signature drumming techniques: extreme
timing precision, linear limb independence, and an extensive polyrhythmic
fill vocabulary spanning the full kit. Built using the composable
DrummerModification system, matching the pattern established by the
other seven drummer plugins.
"""

from midi_drums.config import TIMING, VELOCITY
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Fill
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.generation.builders.pattern_builder import PatternBuilder
from midi_drums.modifications import (
    LinearCoordination,
    SpeedPrecision,
    TripletVocabulary,
)
from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin


class PeartPlugin(DrummerPlugin):
    """Neil Peart drummer style plugin.

    Characteristics:
    - Extreme timing precision, metronomic yet musical
    - Linear coordination - sophisticated limb independence
    - Extensive polyrhythmic/triplet fill vocabulary across the full kit
    - Dramatic, full-kit fills punctuated by china cymbal

    Implemented using composable modifications:
    - LinearCoordination: Sophisticated limb independence, no muddy overlaps
    - SpeedPrecision: Metronomic consistency required by Rush's arrangements
    - TripletVocabulary: Extensive triplet/polyrhythmic fill vocabulary
    """

    def __init__(self):
        self.linear = LinearCoordination()
        self.precision = SpeedPrecision(consistency=0.85)
        self.triplets = TripletVocabulary(triplet_probability=0.35)

    @property
    def drummer_name(self) -> str:
        return "peart"

    @property
    def compatible_genres(self) -> list[str]:
        return ["rock", "progressive", "metal"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Neil Peart's signature style to a pattern."""
        styled = pattern.copy()
        styled.name = f"{pattern.name}_peart"

        styled = self.linear.apply(styled, intensity=0.7)
        styled = self.precision.apply(styled, intensity=0.9)
        styled = self.triplets.apply(styled, intensity=0.6)

        return styled

    def get_signature_fills(self) -> list[Fill]:
        """Return Neil Peart's signature fill patterns."""
        return [
            Fill(
                pattern=self._create_quintuplet_tom_fill(),
                trigger_probability=0.7,
                section_position="middle",
            ),
            Fill(
                pattern=self._create_linear_precision_fill(),
                trigger_probability=0.6,
                section_position="middle",
            ),
            Fill(
                pattern=self._create_china_punctuation_fill(),
                trigger_probability=0.8,
                section_position="end",
            ),
        ]

    def _create_quintuplet_tom_fill(self) -> Pattern:
        """Quintuplet tom cascade reflecting Peart's polyrhythmic vocabulary."""
        builder = PatternBuilder("peart_quintuplet_toms")
        instruments = [
            DrumInstrument.MID_TOM,
            DrumInstrument.MID_TOM,
            DrumInstrument.FLOOR_TOM,
            DrumInstrument.FLOOR_TOM,
            DrumInstrument.KICK,
        ]
        for i, instrument in enumerate(instruments):
            position = i * TIMING.SIXTEENTH_QUINTUPLET
            velocity = (
                VELOCITY.KICK_HEAVY
                if instrument == DrumInstrument.KICK
                else VELOCITY.TOM_HEAVY
            )
            builder.pattern.add_beat(position, instrument, velocity)
        return builder.build()

    def _create_linear_precision_fill(self) -> Pattern:
        """Alternating kick/snare 32nds - no overlap, linear coordination.

        Fills render only the portion of their pattern before beat 1.0
        (see midi_drums/export/midi/engine.py's fill-rendering gate), so
        all 8 hits are packed into a single beat via 32nd-note subdivision
        rather than spanning two beats of 16ths.
        """
        builder = PatternBuilder("peart_linear_precision")
        for i in range(8):
            position = i * TIMING.THIRTY_SECOND
            if i % 2 == 0:
                builder.kick(position, VELOCITY.KICK_HEAVY)
            else:
                builder.snare(position, VELOCITY.SNARE_HEAVY)
        return builder.build()

    def _create_china_punctuation_fill(self) -> Pattern:
        """Descending toms into a dramatic china cymbal punctuation.

        Kept entirely within beat 1.0 (see midi_drums/export/midi/engine.py's
        fill-rendering gate) - the climactic hit sits at 0.75, not exactly at
        1.0, so it isn't silently dropped by the rendering boundary check.
        """
        builder = PatternBuilder("peart_china_punctuation")
        builder.pattern.add_beat(
            0.0, DrumInstrument.MID_TOM, VELOCITY.TOM_HEAVY
        )
        builder.pattern.add_beat(
            TIMING.SIXTEENTH, DrumInstrument.FLOOR_TOM, VELOCITY.TOM_ACCENT
        )
        builder.kick(TIMING.DOTTED_EIGHTH, VELOCITY.KICK_ACCENT)
        builder.pattern.add_beat(
            TIMING.DOTTED_EIGHTH, DrumInstrument.CHINA, VELOCITY.CHINA_ACCENT
        )
        return builder.build()
