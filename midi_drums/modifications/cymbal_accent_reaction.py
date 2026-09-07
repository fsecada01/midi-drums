"""Cymbal-accent-reaction modification - reacts hi-hat/crash/ride/china to
riff accents.

Generalizes the same reinforce/stab reaction that
:class:`midi_drums.modifications.snare_accent_reaction.SnareAccentReaction`
applies to the snare, onto four timekeeping/accent cymbals: hi-hat, crash,
ride, and china. A separate, sibling class rather than a mode bolted onto
the snare version - see ``claudedocs/design_riff_snare_accents.md``'s own
Non-goals section, which flagged "hi-hat/cymbal reactions" as the
anticipated next increment of this same feature family.

Two independent, opt-in modes per kit piece (never both at once - see
``mode``), identical semantics to the snare version:

- ``"reinforce"``: existing beats of the target kit piece that already
  fall near a strong accent get a velocity boost toward the pattern's own
  accented ceiling for that instrument. No beats added or removed, no
  positions changed.
- ``"stab"``: at very strong accents where a kick was actually locked (by
  ``RiffLockTransform``) but no beat of the target kit piece is nearby,
  insert a new unison hit at the kick's exact position. A candidate that
  lands near an existing beat of that kit piece instead collapses into a
  reinforce, same dedup rule as the snare version.

Each of the four kit pieces (hi-hat, crash, ride, china) is applied
independently via its own ``CymbalAccentReaction`` instance - hi-hat and
ride can react while crash/china stay off, etc. Not registered in
``MODIFICATION_REGISTRY`` (requires a non-zero-arg ``riff_accents``) -
construct and call directly (see
``midi_drums.plugins.registry.plugin_registry.PluginManager.apply_riff_cymbal_accents``).
"""

from dataclasses import dataclass
from typing import Literal

from midi_drums.config import VELOCITY
from midi_drums.core.models.pattern import Beat, Pattern
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.riff_accent import RiffAccent, RiffAccentMap
from midi_drums.modifications._riff_accent_selection import (
    circular_distance,
    select_accents,
)
from midi_drums.modifications.drummer_mods import DrummerModification

KitPiece = Literal["hihat", "crash", "ride", "china"]

# Every instrument variant that counts as "this kit piece" for reinforce
# matching - over-inclusive on purpose, so a promoted or EZDrummer-specific
# hi-hat/ride note is still reinforceable.
_MATCH_INSTRUMENTS: dict[KitPiece, frozenset[DrumInstrument]] = {
    "hihat": frozenset(
        {
            DrumInstrument.CLOSED_HH,
            DrumInstrument.CLOSED_HH_EDGE,
            DrumInstrument.CLOSED_HH_TIP,
            DrumInstrument.TIGHT_HH_EDGE,
            DrumInstrument.TIGHT_HH_TIP,
            DrumInstrument.PEDAL_HH,
            DrumInstrument.OPEN_HH,
            DrumInstrument.OPEN_HH_1,
            DrumInstrument.OPEN_HH_2,
            DrumInstrument.OPEN_HH_3,
            DrumInstrument.OPEN_HH_MAX,
        }
    ),
    "crash": frozenset({DrumInstrument.CRASH}),
    "ride": frozenset({DrumInstrument.RIDE, DrumInstrument.RIDE_BELL}),
    "china": frozenset({DrumInstrument.CHINA}),
}

# The single instrument a "stab" insert actually places - the canonical,
# most-common note for that kit piece (closed hi-hat rather than an
# open/pedal variant; the ride's body rather than its bell).
_INSERT_INSTRUMENT: dict[KitPiece, DrumInstrument] = {
    "hihat": DrumInstrument.CLOSED_HH,
    "crash": DrumInstrument.CRASH,
    "ride": DrumInstrument.RIDE,
    "china": DrumInstrument.CHINA,
}

# Fallback velocity used only when the incoming pattern has no beats of
# this kit piece at all to derive a ceiling from.
_DEFAULT_VELOCITY: dict[KitPiece, int] = {
    "hihat": VELOCITY.HIHAT_ACCENT,
    "crash": VELOCITY.CRASH_ACCENT,
    "ride": VELOCITY.RIDE_ACCENT,
    "china": VELOCITY.CHINA_ACCENT,
}


def _is_reinforceable(beat: Beat, kit_piece: KitPiece) -> bool:
    """Non-ghost beats of the target kit piece only - mirrors the snare
    version's ghost-note exclusion (a strong accent reinforcing a ghost
    hit into a loud one would change the pattern's character more than
    intended)."""
    return (
        beat.instrument in _MATCH_INSTRUMENTS[kit_piece] and not beat.ghost_note
    )


def _accent_velocity_ceiling(pattern: Pattern, kit_piece: KitPiece) -> int:
    """The velocity a "fully accented" hit of this kit piece should top
    out at.

    Prefers the loudest already-accented hit of that kit piece (the genre
    plugin's own idea of "this hit is emphasized"); falls back to the
    loudest hit of any kind, then to a fixed default for a pattern with no
    beats of this kit piece at all.
    """
    accented = [
        b.velocity
        for b in pattern.beats
        if _is_reinforceable(b, kit_piece) and b.accent
    ]
    if accented:
        return max(accented)
    plain = [
        b.velocity for b in pattern.beats if _is_reinforceable(b, kit_piece)
    ]
    if plain:
        return max(plain)
    return _DEFAULT_VELOCITY[kit_piece]


def _blend_velocity(
    current: int, ceiling: int, strength: float, intensity: float
) -> int:
    """Blend ``current`` toward ``ceiling``, never decreasing it."""
    if ceiling <= current:
        return current
    boosted = current + round((ceiling - current) * strength * intensity)
    return min(127, max(current, boosted))


def _nearest_within(position, candidates, period, tolerance):
    """Nearest of ``candidates`` (anything with a ``.position``) to
    ``position`` within ``tolerance`` (circular), or ``None``."""
    best = None
    best_distance = None
    for candidate in candidates:
        distance = circular_distance(position, candidate.position, period)
        if distance <= tolerance and (
            best_distance is None or distance < best_distance
        ):
            best = candidate
            best_distance = distance
    return best


def _reinforced_beat(beat: Beat, new_velocity: int) -> Beat:
    return Beat(
        position=beat.position,
        instrument=beat.instrument,
        velocity=new_velocity,
        duration=beat.duration,
        ghost_note=beat.ghost_note,
        accent=True,
        instrument_promoted=beat.instrument_promoted,
    )


@dataclass
class CymbalAccentReaction(DrummerModification):
    """React a hi-hat, crash, or ride pattern to a riff's rhythmic accents.

    Example:
        CymbalAccentReaction(
            riff_accents=accent_map, kit_piece="crash", mode="stab"
        ).apply(pattern, intensity=0.8)
    """

    riff_accents: RiffAccentMap
    kit_piece: KitPiece
    mode: Literal["reinforce", "stab"] = "reinforce"

    # reinforce
    strong_threshold: float = 0.6
    reinforce_tolerance_beats: float = 0.125

    # stab
    stab_threshold: float = 0.85
    max_stabs_per_bar: int = 2
    min_stab_spacing_beats: float = 0.5
    stab_collapse_tolerance_beats: float = 0.125
    stab_kick_tolerance_beats: float = 0.125

    def __post_init__(self) -> None:
        if self.mode not in ("reinforce", "stab"):
            raise ValueError(
                f"mode must be 'reinforce' or 'stab', got {self.mode!r} - "
                "'off' means this class isn't invoked at all, see "
                "PluginManager.apply_riff_cymbal_accents"
            )
        if self.kit_piece not in _MATCH_INSTRUMENTS:
            raise ValueError(
                f"kit_piece must be one of {sorted(_MATCH_INSTRUMENTS)}, "
                f"got {self.kit_piece!r}"
            )

    @property
    def name(self) -> str:
        return f"{self.kit_piece}_accent_{self.mode}"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Apply the configured reaction mode to ``pattern``'s beats of
        ``self.kit_piece``.

        Args:
            pattern: Input pattern to modify. Expected to already have had
                ``RiffLockTransform`` applied when ``mode="stab"``, so
                locked kicks exist to unison-match against.
            intensity: 0.0-1.0 blend strength for velocity boosts (both
                modes) - does not affect whether a stab is inserted, only
                how hard reinforce/collapse boosts land.

        Returns:
            New Pattern with the reaction applied.
        """
        if not self.riff_accents.accents:
            return pattern.copy()
        if self.mode == "reinforce":
            return self._apply_reinforce(pattern, intensity)
        return self._apply_stab(pattern, intensity)

    def _apply_reinforce(self, pattern: Pattern, intensity: float) -> Pattern:
        beats_per_bar = self.riff_accents.beats_per_bar
        ceiling = _accent_velocity_ceiling(pattern, self.kit_piece)
        strong = self.riff_accents.strong_accents(self.strong_threshold)

        new_beats: list[Beat] = []
        for beat in pattern.beats:
            nearest = (
                _nearest_within(
                    beat.position,
                    strong,
                    beats_per_bar,
                    self.reinforce_tolerance_beats,
                )
                if _is_reinforceable(beat, self.kit_piece)
                else None
            )
            if nearest is not None:
                new_velocity = _blend_velocity(
                    beat.velocity, ceiling, nearest.strength, intensity
                )
                new_beats.append(_reinforced_beat(beat, new_velocity))
            else:
                new_beats.append(beat)

        return Pattern(
            name=f"{pattern.name}_{self.kit_piece}_reinforced",
            beats=new_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )

    def _apply_stab(self, pattern: Pattern, intensity: float) -> Pattern:
        beats_per_bar = self.riff_accents.beats_per_bar
        stab_accents: list[RiffAccent] = select_accents(
            self.riff_accents,
            self.stab_threshold,
            self.max_stabs_per_bar,
            self.min_stab_spacing_beats,
        )
        if not stab_accents:
            return pattern.copy()

        ceiling = _accent_velocity_ceiling(pattern, self.kit_piece)
        insert_instrument = _INSERT_INSTRUMENT[self.kit_piece]

        existing_matches = [
            b for b in pattern.beats if _is_reinforceable(b, self.kit_piece)
        ]
        existing_kicks = [
            b for b in pattern.beats if b.instrument == DrumInstrument.KICK
        ]

        reinforced_velocities: dict[int, int] = {}
        new_stab_beats: list[Beat] = []

        for accent in stab_accents:
            collapse_target = _nearest_within(
                accent.position,
                existing_matches,
                beats_per_bar,
                self.stab_collapse_tolerance_beats,
            )
            if collapse_target is not None:
                reinforced_velocities[id(collapse_target)] = _blend_velocity(
                    collapse_target.velocity,
                    ceiling,
                    accent.strength,
                    intensity,
                )
                continue

            matched_kick = _nearest_within(
                accent.position,
                existing_kicks,
                beats_per_bar,
                self.stab_kick_tolerance_beats,
            )
            if matched_kick is None:
                # No kick landed here - not a unison stab, skip (same
                # rationale as SnareAccentReaction._apply_stab).
                continue

            new_stab_beats.append(
                Beat(
                    position=matched_kick.position,
                    instrument=insert_instrument,
                    velocity=matched_kick.velocity,
                    duration=0.25,
                    ghost_note=False,
                    accent=True,
                    instrument_promoted=False,
                )
            )

        new_beats: list[Beat] = []
        for beat in pattern.beats:
            new_velocity = reinforced_velocities.get(id(beat))
            if new_velocity is not None:
                new_beats.append(_reinforced_beat(beat, new_velocity))
            else:
                new_beats.append(beat)
        new_beats.extend(new_stab_beats)
        new_beats.sort(key=lambda b: b.position)

        return Pattern(
            name=f"{pattern.name}_{self.kit_piece}_stabbed",
            beats=new_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )
