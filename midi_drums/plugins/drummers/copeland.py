"""Stewart Copeland drummer plugin.

Implements Stewart Copeland's (The Police) signature drumming techniques:
reggae/ska-influenced off-beat hi-hat work, cross-stick snare, and
unconventional accent placement. Built using the composable
DrummerModification system, matching the pattern established by the
other drummer plugins.
"""

from midi_drums.config import TIMING, VELOCITY
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.models.song import Fill
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.generation.builders.pattern_builder import PatternBuilder
from midi_drums.modifications import (
    GhostNoteLayer,
    PocketStretching,
    TwistedAccents,
)
from midi_drums.plugins.interfaces.drummer_plugin import DrummerPlugin


class CopelandPlugin(DrummerPlugin):
    """Stewart Copeland drummer style plugin.

    Characteristics:
    - Reggae/ska-influenced off-beat hi-hat emphasis
    - Cross-stick (rim click) snare texture in signature fills, rather than
      a full backbeat hit
    - Unconventional, displaced accent placement

    Implemented using composable modifications:
    - TwistedAccents: displaces accents off the expected beat
    - PocketStretching: elastic, syncopated groove tension
    - GhostNoteLayer: subtle ghost-note snare texture underlying the groove
      (cross-stick rim texture itself is added directly in the signature
      fills, via DrumInstrument.RIM)
    """

    def __init__(self):
        self.twisted_accents = TwistedAccents(displacement=0.45)
        self.pocket_stretch = PocketStretching(variation_ms=8.0)
        self.ghost_notes = GhostNoteLayer(density=0.4)

    @property
    def drummer_name(self) -> str:
        return "copeland"

    @property
    def compatible_genres(self) -> list[str]:
        return ["rock", "funk"]

    def apply_style(self, pattern: Pattern) -> Pattern:
        """Apply Stewart Copeland's signature style to a pattern."""
        styled = pattern.copy()
        styled.name = f"{pattern.name}_copeland"

        styled = self.ghost_notes.apply(styled, intensity=0.5)
        styled = self.pocket_stretch.apply(styled, intensity=0.7)
        styled = self.twisted_accents.apply(styled, intensity=0.8)

        return styled

    def get_signature_fills(self) -> list[Fill]:
        """Return Stewart Copeland's signature fill patterns."""
        return [
            Fill(
                pattern=self._create_skank_hihat_fill(),
                trigger_probability=0.6,
                section_position="middle",
            ),
            Fill(
                pattern=self._create_displaced_accent_fill(),
                trigger_probability=0.7,
                section_position="middle",
            ),
            Fill(
                pattern=self._create_syncopated_tom_skip_fill(),
                trigger_probability=0.6,
                section_position="end",
            ),
        ]

    def _create_skank_hihat_fill(self) -> Pattern:
        """Off-beat hi-hat 'skank' pattern with cross-stick punctuation.

        Alternates a cross-stick rim click with open hi-hat on the upbeats,
        the reggae/ska-derived off-beat emphasis Copeland brought into rock.
        """
        builder = PatternBuilder("copeland_skank_hihat")
        builder.pattern.add_beat(0.0, DrumInstrument.RIM, VELOCITY.SNARE_LIGHT)
        builder.pattern.add_beat(
            TIMING.SIXTEENTH, DrumInstrument.OPEN_HH_1, VELOCITY.HIHAT_ACCENT
        )
        builder.pattern.add_beat(
            TIMING.SIXTEENTH * 2, DrumInstrument.RIM, VELOCITY.SNARE_LIGHT
        )
        builder.pattern.add_beat(
            TIMING.SIXTEENTH * 3,
            DrumInstrument.OPEN_HH_1,
            VELOCITY.HIHAT_ACCENT,
        )
        return builder.build()

    def _create_displaced_accent_fill(self) -> Pattern:
        """Snare/rim/kick pattern with the accent on an unexpected subdivision.

        Fills render only the portion of their pattern before beat 1.0
        (see midi_drums/export/midi/engine.py's fill-rendering gate), so
        the displacement is packed into a single beat via 16th-note
        subdivision.
        """
        builder = PatternBuilder("copeland_displaced_accent")
        builder.pattern.add_beat(0.0, DrumInstrument.RIM, VELOCITY.SNARE_LIGHT)
        builder.pattern.add_beat(
            TIMING.SIXTEENTH, DrumInstrument.RIM, VELOCITY.SNARE_NORMAL
        )
        builder.pattern.add_beat(
            TIMING.SIXTEENTH * 2,
            DrumInstrument.SNARE,
            VELOCITY.SNARE_ACCENT,
            accent=True,
        )
        builder.kick(TIMING.SIXTEENTH * 3, VELOCITY.KICK_NORMAL)
        return builder.build()

    def _create_syncopated_tom_skip_fill(self) -> Pattern:
        """Hesitating tom pattern ending in a cross-stick punctuation.

        Kept entirely within beat 1.0 (see midi_drums/export/midi/engine.py's
        fill-rendering gate) - the closing rim click sits at 0.75, not
        exactly at 1.0, so it isn't silently dropped by the rendering
        boundary check.
        """
        builder = PatternBuilder("copeland_syncopated_tom_skip")
        builder.pattern.add_beat(
            0.0, DrumInstrument.MID_TOM, VELOCITY.TOM_ACCENT
        )
        builder.pattern.add_beat(
            TIMING.DOTTED_SIXTEENTH,
            DrumInstrument.FLOOR_TOM,
            VELOCITY.TOM_HEAVY,
        )
        builder.pattern.add_beat(
            TIMING.DOTTED_EIGHTH, DrumInstrument.RIM, VELOCITY.SNARE_ACCENT
        )
        return builder.build()
