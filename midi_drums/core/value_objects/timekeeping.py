"""Shared registry of cymbals that can carry the drum kit's timekeeping role.

Single source of truth for issue #36 item 2. Two consumers need the same
answer to "which cymbals can stand in for the hi-hat as timekeeper":

- ``midi_drums.plugins.interfaces.genre_plugin.GenrePlugin`` validates that
  any ``_high_energy_timekeeper()`` override's return value is a member of
  this set before promoting a hi-hat beat to it.
- ``midi_drums.modifications.drummer_mods`` uses it (together with
  ``Beat.instrument_promoted``) to recognize a promoted beat as "the
  timekeeping cymbal" rather than matching every beat of that instrument
  type, which would also catch genuinely-placed accents (e.g. a
  ``CrashAccents`` hit).

Both ``plugins/`` and ``modifications/`` are permitted to depend on
``core/`` per ``docs/DDD_ARCHITECTURE.md``, so this lives here rather than
in either of them - the alternative (one importing the other) would put the
constant on the wrong side of the dependency graph. A genre plugin that
wants to promote timekeeping to a cymbal not yet listed here must add it in
this one place; every consumer picks up the change automatically.
"""

from midi_drums.core.value_objects.drum_instrument import DrumInstrument

PROMOTABLE_TIMEKEEPING_CYMBALS = frozenset(
    {DrumInstrument.RIDE, DrumInstrument.CRASH, DrumInstrument.CHINA}
)
