"""Snare-accent-reaction modification - reacts the snare to riff accents.

Post-processes a genre-plugin pattern that has already been through
:class:`midi_drums.modifications.riff_lock.RiffLockTransform` (kick already
locked to the riff's accents) so the snare can optionally react to those
same accents too, without repositioning the backbeat. See
``claudedocs/design_riff_snare_accents.md`` for the full design rationale.

Two independent, opt-in modes (never both at once - see ``mode``):

- ``"reinforce"``: existing (non-ghost) snare beats that already fall near
  a strong accent get a velocity boost toward the pattern's own accented-
  snare ceiling. No beats are added or removed, no positions change.
- ``"stab"``: at very strong accents where a kick was actually locked (by
  ``RiffLockTransform``) but no snare is nearby, insert a new unison snare
  hit at the kick's exact position/velocity ("true unison feel"). A stab
  candidate that lands near an *existing* snare instead collapses into a
  reinforce (see ``stab_collapse_tolerance_beats``) rather than stacking a
  second hit on top of it.

Follows the same conventions as ``midi_drums.modifications.drummer_mods``
and ``riff_lock.py``: subclasses ``DrummerModification``, never mutates the
input ``Pattern``, returns a new one. Deliberately **not** registered in
``MODIFICATION_REGISTRY`` (requires a non-zero-arg ``riff_accents``
argument) - construct and call it directly (see
``midi_drums.plugins.registry.plugin_registry.PluginManager.apply_riff_snare_accents``).
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

# Fallback used only when the incoming pattern has no snare beats at all to
# derive a velocity ceiling/duration from (e.g. a snare-less texture bar).
_DEFAULT_SNARE_ACCENT_VELOCITY = VELOCITY.SNARE_ACCENT
_DEFAULT_SNARE_DURATION = 0.25


def _is_reinforceable_snare(beat: Beat) -> bool:
    """Non-ghost snare beats only - ghost notes are excluded from both
    reinforce and stab-collapse targets (Open Question 4)."""
    return beat.instrument == DrumInstrument.SNARE and not beat.ghost_note


def _snare_accent_velocity_ceiling(pattern: Pattern) -> int:
    """The velocity a "fully accented" snare hit should top out at.

    Prefers the loudest already-accented snare hit in the pattern (the
    genre plugin's own idea of "this snare is emphasized"); falls back to
    the loudest snare hit of any kind, then to a fixed default for a
    snare-less pattern.
    """
    accented = [
        b.velocity
        for b in pattern.beats
        if _is_reinforceable_snare(b) and b.accent
    ]
    if accented:
        return max(accented)
    plain = [b.velocity for b in pattern.beats if _is_reinforceable_snare(b)]
    if plain:
        return max(plain)
    return _DEFAULT_SNARE_ACCENT_VELOCITY


def _snare_default_duration(pattern: Pattern) -> float:
    durations = [
        b.duration for b in pattern.beats if _is_reinforceable_snare(b)
    ]
    return durations[0] if durations else _DEFAULT_SNARE_DURATION


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
    ``position`` within ``tolerance`` (circular), or ``None``.

    Generic over both ``RiffAccent`` (reinforce lookups) and ``Beat``
    (stab collapse/kick-match lookups) - both simply expose ``.position``.
    """
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
class SnareAccentReaction(DrummerModification):
    """React the snare to a riff's rhythmic accents.

    Example:
        SnareAccentReaction(riff_accents=accent_map, mode="stab").apply(
            pattern, intensity=0.8
        )
    """

    riff_accents: RiffAccentMap
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
                "PluginManager.apply_riff_snare_accents"
            )

    @property
    def name(self) -> str:
        return f"snare_accent_{self.mode}"

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Apply the configured reaction mode to ``pattern``'s snare beats.

        Args:
            pattern: Input pattern to modify. Expected to already have had
                ``RiffLockTransform`` applied when ``mode="stab"``, so
                locked kicks exist to unison-match against.
            intensity: 0.0-1.0 blend strength for velocity boosts (both
                modes) - does not affect whether a stab is inserted, only
                how hard reinforce/collapse boosts land.

        Returns:
            New Pattern with the snare reaction applied.
        """
        if not self.riff_accents.accents:
            return pattern.copy()
        if self.mode == "reinforce":
            return self._apply_reinforce(pattern, intensity)
        return self._apply_stab(pattern, intensity)

    def _apply_reinforce(self, pattern: Pattern, intensity: float) -> Pattern:
        beats_per_bar = self.riff_accents.beats_per_bar
        ceiling = _snare_accent_velocity_ceiling(pattern)
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
                if _is_reinforceable_snare(beat)
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
            name=f"{pattern.name}_snare_reinforced",
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

        ceiling = _snare_accent_velocity_ceiling(pattern)
        default_duration = _snare_default_duration(pattern)

        existing_snares = [
            b for b in pattern.beats if _is_reinforceable_snare(b)
        ]
        existing_kicks = [
            b for b in pattern.beats if b.instrument == DrumInstrument.KICK
        ]

        reinforced_velocities: dict[int, int] = {}
        new_stab_beats: list[Beat] = []

        for accent in stab_accents:
            collapse_target = _nearest_within(
                accent.position,
                existing_snares,
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
                # No kick landed here - either the accent didn't clear the
                # kick's own strong_threshold, or RiffLockTransform's own
                # max_kicks_per_bar/min_kick_spacing_beats budget rejected
                # it. A "stab" with no kick under it isn't a unison hit,
                # it's just an extra snare note out of nowhere - skip.
                continue

            new_stab_beats.append(
                Beat(
                    position=matched_kick.position,
                    instrument=DrumInstrument.SNARE,
                    velocity=matched_kick.velocity,
                    duration=default_duration,
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
            name=f"{pattern.name}_snare_stabbed",
            beats=new_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )
