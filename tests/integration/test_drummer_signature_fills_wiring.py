"""Regression tests for issue #32.

``DrummerPlugin.get_signature_fills()`` is implemented by every drummer
plugin, but prior to this fix nothing in the generation pipeline ever
called it: ``DrumGenerator._generate_fills()`` only consulted
``GenrePlugin.get_common_fills()``. A drummer's signature fills were dead
code from the perspective of actual song generation.

These tests prove:
  1. When a drummer with signature fills is requested, that request is
     treated as a drummer-inspired performance: fills are drawn
     exclusively from the drummer's candidates, not diluted by the
     genre's stock fills.
  2. Drummers with no signature fills (the pre-Peart default) fall back
     to the genre's common fill pool unchanged.
  3. With no drummer set at all, fills come from the genre pool only
     (unchanged baseline behavior).
  4. A drummer's signature fill can actually be selected and rendered into
     the generated MIDI output for a full song generation call - not just
     that ``get_signature_fills()`` returns data in isolation.
"""

from unittest.mock import patch

from midi_drums import DrumGenerator
from midi_drums.core.value_objects.drum_instrument import DrumInstrument

PEART_FILL_PATTERN_NAMES = {
    "peart_quintuplet_toms",
    "peart_linear_precision",
    "peart_china_punctuation",
}


class TestDrummerSignatureFillsWiredIntoGeneration:
    def test_drummer_with_signature_fills_uses_only_drummer_fills(self):
        """A drummer-inspired performance draws fills exclusively from
        that drummer's candidates - genre common fills are not diluting
        the performance's identity."""
        generator = DrumGenerator()
        song = generator.create_song(
            genre="rock",
            style="classic",
            drummer="peart",
            structure=[("verse", 1)],
        )

        section = song.sections[0]
        fill_pattern_names = {fill.pattern.name for fill in section.fills}

        assert fill_pattern_names == PEART_FILL_PATTERN_NAMES, (
            "expected section.fills to contain exactly Peart's signature "
            f"fills, got {fill_pattern_names}"
        )

    def test_no_drummer_only_uses_genre_common_fills(self):
        """Baseline: with no drummer set, section.fills is genre-only."""
        generator = DrumGenerator()
        song = generator.create_song(
            genre="rock",
            style="classic",
            structure=[("verse", 1)],
        )

        section = song.sections[0]
        fill_pattern_names = {fill.pattern.name for fill in section.fills}
        assert not (fill_pattern_names & PEART_FILL_PATTERN_NAMES)
        assert len(fill_pattern_names) == 3

    def test_drummer_with_no_signature_fills_falls_back_to_genre_pool(self):
        """A drummer whose get_signature_fills() returns [] (e.g. Bonham,
        the currently-registered default) falls back to the genre's
        common fills rather than leaving section.fills empty."""
        generator = DrumGenerator()
        song = generator.create_song(
            genre="rock",
            style="classic",
            drummer="bonham",
            structure=[("verse", 1)],
        )

        section = song.sections[0]
        fill_pattern_names = {fill.pattern.name for fill in section.fills}
        assert not (fill_pattern_names & PEART_FILL_PATTERN_NAMES)
        assert len(fill_pattern_names) == 3

    def test_peart_signature_fill_actually_rendered_in_midi_output(self):
        """Force fill selection deterministically and prove a Peart
        signature fill's notes reach the generated MIDI output."""
        generator = DrumGenerator()

        # Section.should_add_fill() calls random.random() twice per bar:
        # once to decide whether a fill happens at all (must be less than
        # fill_frequency) and once for the trigger_probability-weighted
        # pick among section.fills. Returning a value just below 1.0 for
        # both, with fill_frequency=1.0, deterministically selects the
        # *last* fill in Peart's exclusive candidate list -
        # peart_china_punctuation.
        with patch("random.random", return_value=0.999999):
            song = generator.create_song(
                genre="rock",
                style="classic",
                drummer="peart",
                fill_frequency=1.0,
                structure=[("verse", 1)],
            )
            midi = generator.midi_engine.song_to_midi(song)

        china_note = generator.drum_kit.get_midi_note(DrumInstrument.CHINA)

        note_ons = [
            event
            for track in midi.tracks
            for event in track.eventList
            if type(event).__name__ == "NoteOn"
        ]
        china_notes = [e for e in note_ons if e.pitch == china_note]

        assert china_notes, (
            "expected Peart's china_punctuation signature fill to render "
            "a china cymbal NoteOn event into the generated MIDI output"
        )
