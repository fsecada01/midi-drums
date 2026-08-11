"""Buddy Rich drummer plugin.

Implements Buddy Rich's (big band/swing) signature drumming techniques:
virtuosic single-stroke speed, dramatic dynamic contrast (whisper-soft
ghost notes to thunderous accents), and showmanship-driven fill vocabulary.
Built using the composable DrummerModification system, matching the
pattern established by the other drummer plugins.
"""

from midi_drums.config import TIMING, VELOCITY
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Fill
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.generation.builders.pattern_builder import PatternBuilder
from midi_drums.modifications import (
    FastChopsTriplets,
    GhostNoteLayer,
    HeavyAccents,
)
from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin


class RichPlugin(DrummerPlugin):
    """Buddy Rich drummer style plugin.

    Characteristics:
    - Virtuosic single-stroke speed across fast fill passages
    - Extreme dynamic contrast, whisper-soft ghost notes to thunderous
      accents
    - Showmanship-driven, full-kit fills that build and release tension

    Implemented using composable modifications:
    - FastChopsTriplets: rapid technical fill vocabulary
    - GhostNoteLayer: soft ghost notes providing the "whisper" end of the
      dynamic range
    - HeavyAccents: sharp accent contrast providing the "thunder" end of
      the dynamic range
    """

    def __init__(self):
        self.fast_chops = FastChopsTriplets(probability=0.35)
        self.ghost_notes = GhostNoteLayer(density=0.5)
        self.accents = HeavyAccents(accent_boost=18)

    @property
    def drummer_name(self) -> str:
        return "rich"

    @property
    def compatible_genres(self) -> list[str]:
        return ["jazz", "rock"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Buddy Rich's signature style to a pattern."""
        styled = pattern.copy()
        styled.name = f"{pattern.name}_rich"

        styled = self.ghost_notes.apply(styled, intensity=0.6)
        styled = self.fast_chops.apply(styled, intensity=0.7)
        styled = self.accents.apply(styled, intensity=0.9)

        return styled

    def get_signature_fills(self) -> list[Fill]:
        """Return Buddy Rich's signature fill patterns."""
        return [
            Fill(
                pattern=self._create_single_stroke_roll_fill(),
                trigger_probability=0.7,
                section_position="middle",
            ),
            Fill(
                pattern=self._create_dynamic_cascade_fill(),
                trigger_probability=0.6,
                section_position="middle",
            ),
            Fill(
                pattern=self._create_showman_crash_fill(),
                trigger_probability=0.8,
                section_position="end",
            ),
        ]

    def _create_single_stroke_roll_fill(self) -> Pattern:
        """Rapid single-stroke snare roll with a rising dynamic curve.

        8 evenly spaced 32nd-note snare hits crescendo from a ghost-note
        whisper to a full accent, showcasing single-stroke speed and
        dynamic control in one breath.
        """
        builder = PatternBuilder("rich_single_stroke_roll")
        velocities = [
            VELOCITY.SNARE_GHOST,
            VELOCITY.SNARE_GHOST,
            VELOCITY.SNARE_LIGHT,
            VELOCITY.SNARE_LIGHT,
            VELOCITY.SNARE_NORMAL,
            VELOCITY.SNARE_NORMAL,
            VELOCITY.SNARE_HEAVY,
            VELOCITY.SNARE_ACCENT,
        ]
        for i, velocity in enumerate(velocities):
            position = i * TIMING.THIRTY_SECOND
            builder.snare(position, velocity)
        return builder.build()

    def _create_dynamic_cascade_fill(self) -> Pattern:
        """Descending snare-to-tom cascade with a soft-loud-soft-LOUD swing.

        Fills render only the portion of their pattern before beat 1.0
        (see midi_drums/export/midi/engine.py's fill-rendering gate), so
        the full cascade is packed into a single beat via 16th-note
        subdivision.
        """
        builder = PatternBuilder("rich_dynamic_cascade")
        builder.pattern.add_beat(
            0.0, DrumInstrument.SNARE, VELOCITY.SNARE_LIGHT
        )
        builder.pattern.add_beat(
            TIMING.SIXTEENTH, DrumInstrument.MID_TOM, VELOCITY.TOM_ACCENT
        )
        builder.pattern.add_beat(
            TIMING.SIXTEENTH * 2, DrumInstrument.FLOOR_TOM, VELOCITY.TOM_HEAVY
        )
        builder.kick(TIMING.SIXTEENTH * 3, VELOCITY.KICK_ACCENT)
        return builder.build()

    def _create_showman_crash_fill(self) -> Pattern:
        """Fast triplet buildup punctuated by a dramatic crash accent.

        Kept entirely within beat 1.0 (see midi_drums/export/midi/engine.py's
        fill-rendering gate) - the climactic crash sits at 0.75, not exactly
        at 1.0, so it isn't silently dropped by the rendering boundary check.
        """
        builder = PatternBuilder("rich_showman_crash")
        builder.snare(0.0, VELOCITY.SNARE_NORMAL)
        builder.snare(TIMING.SIXTEENTH_TRIPLET, VELOCITY.SNARE_HEAVY)
        builder.snare(TIMING.SIXTEENTH_TRIPLET * 2, VELOCITY.SNARE_ACCENT)
        builder.kick(TIMING.DOTTED_EIGHTH, VELOCITY.KICK_ACCENT)
        builder.pattern.add_beat(
            TIMING.DOTTED_EIGHTH, DrumInstrument.CRASH, VELOCITY.CRASH_ACCENT
        )
        return builder.build()
