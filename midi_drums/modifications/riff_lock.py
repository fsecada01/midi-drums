"""Riff-lock modification - snaps kicks onto an audio riff's accents.

Post-processes a genre-plugin-generated pattern (routed through the normal
pipeline, per the explicit design decision behind issue riff-lock: "route
through genre plugins" rather than a standalone generation strategy) so its
kick drum locks onto the rhythmic accents of a recorded riff, while every
other instrument - snare, hi-hat, cymbals, drummer styling - is left
untouched.

Follows the same conventions as ``midi_drums.modifications.drummer_mods``:
subclasses ``DrummerModification``, never mutates the input ``Pattern``,
returns a new one named ``f"{pattern.name}_riff_locked"``. Deliberately
**not** registered in ``MODIFICATION_REGISTRY`` - that registry requires
zero-arg constructibility, and ``riff_accents`` has no sensible default.
Construct and call it directly (see
``midi_drums.generation.engines.drum_generator.DrumGenerator.generate_pattern``).
"""

from dataclasses import dataclass

from midi_drums.config import VELOCITY
from midi_drums.core.models.pattern import Beat, Pattern
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.riff_accent import RiffAccent, RiffAccentMap
from midi_drums.modifications.drummer_mods import DrummerModification

# Fallback velocity range used only when the incoming pattern has no
# existing kicks to derive a range from (e.g. an ambient/atmospheric
# section with no kick pattern at all).
_DEFAULT_KICK_VELOCITY_RANGE = (VELOCITY.KICK_LIGHT, VELOCITY.KICK_HEAVY)


def _circular_distance(a: float, b: float, period: float) -> float:
    """Shortest distance between two positions on a period-``period`` ring.

    E.g. with period=4.0, positions 3.875 and 0.0 are 0.125 apart, not
    3.875 apart - this is the wraparound case the transform must get right
    at a bar boundary.
    """
    diff = abs(a - b) % period
    return min(diff, period - diff)


@dataclass
class RiffLockTransform(DrummerModification):
    """Lock a pattern's kick drum onto an audio riff's rhythmic accents.

    Example:
        RiffLockTransform(riff_accents=accent_map).apply(pattern, intensity=0.8)
    """

    riff_accents: RiffAccentMap
    kick_tolerance_beats: float = 0.125
    strong_threshold: float = 0.6
    min_kick_spacing_beats: float = 0.125
    max_kicks_per_bar: int = 8
    # Off by default: the goal is "kicks lock to accents", which snap+
    # insert already delivers. Removing unmatched existing kicks is what
    # actually erases the genre plugin's identity, cutting against the
    # "route through genre plugins" decision - opt in explicitly.
    removal_strength: float = 0.0
    preserve_downbeat: bool = True
    max_removal_fraction: float = 0.5

    @property
    def name(self) -> str:
        return "riff_lock"

    def _select_accents(self) -> list[RiffAccent]:
        """Greedily pick strong accents respecting spacing/count budgets."""
        candidates = self.riff_accents.strong_accents(self.strong_threshold)
        beats_per_bar = self.riff_accents.beats_per_bar

        selected: list[RiffAccent] = []
        for accent in candidates:  # already strength-descending
            if len(selected) >= self.max_kicks_per_bar:
                break
            if all(
                _circular_distance(
                    accent.position, kept.position, beats_per_bar
                )
                >= self.min_kick_spacing_beats
                for kept in selected
            ):
                selected.append(accent)
        return selected

    def _kick_velocity_range(self, pattern: Pattern) -> tuple[int, int]:
        kick_velocities = [
            b.velocity
            for b in pattern.beats
            if b.instrument == DrumInstrument.KICK
        ]
        if not kick_velocities:
            return _DEFAULT_KICK_VELOCITY_RANGE
        return min(kick_velocities), max(kick_velocities)

    def apply(self, pattern: Pattern, intensity: float = 1.0) -> Pattern:
        """Snap/insert kicks at riff accent positions.

        Args:
            pattern: Input pattern to modify (single bar - v1 scope).
            intensity: 0.0-1.0 blend strength toward the accent position for
                *matched* kicks (an unmatched-and-inserted kick always lands
                exactly on the accent, same as every other modification's
                intensity semantics - the interpolation only applies where
                there's an existing position to blend from).

        Returns:
            New Pattern with kick beats locked to riff accents.
        """
        if not self.riff_accents.accents:
            return pattern.copy()

        beats_per_bar = self.riff_accents.beats_per_bar
        selected_accents = self._select_accents()
        vel_min, vel_max = self._kick_velocity_range(pattern)

        existing_kicks = [
            b for b in pattern.beats if b.instrument == DrumInstrument.KICK
        ]
        other_beats = [
            b for b in pattern.beats if b.instrument != DrumInstrument.KICK
        ]

        matched_kick_ids: set[int] = set()
        new_kick_beats: list[Beat] = []

        for accent in selected_accents:
            nearest_kick = None
            nearest_distance = None
            for kick in existing_kicks:
                if id(kick) in matched_kick_ids:
                    continue
                distance = _circular_distance(
                    accent.position, kick.position, beats_per_bar
                )
                if distance <= self.kick_tolerance_beats and (
                    nearest_distance is None or distance < nearest_distance
                ):
                    nearest_kick = kick
                    nearest_distance = distance

            if nearest_kick is not None:
                matched_kick_ids.add(id(nearest_kick))
                new_position = self._blend_position(
                    nearest_kick.position,
                    accent.position,
                    beats_per_bar,
                    intensity,
                )
                new_kick_beats.append(
                    Beat(
                        position=new_position,
                        instrument=DrumInstrument.KICK,
                        velocity=nearest_kick.velocity,
                        duration=nearest_kick.duration,
                        ghost_note=False,
                        accent=accent.strength >= self.strong_threshold,
                        instrument_promoted=False,
                    )
                )
            else:
                velocity = vel_min + round(
                    accent.strength * (vel_max - vel_min)
                )
                new_kick_beats.append(
                    Beat(
                        position=accent.position,
                        instrument=DrumInstrument.KICK,
                        velocity=velocity,
                        duration=0.25,
                        ghost_note=False,
                        accent=accent.strength >= self.strong_threshold,
                        instrument_promoted=False,
                    )
                )

        unmatched_kicks = [
            k for k in existing_kicks if id(k) not in matched_kick_ids
        ]
        if self.removal_strength > 0 and unmatched_kicks:
            unmatched_kicks = self._remove_unmatched(unmatched_kicks)

        modified_beats = other_beats + new_kick_beats + unmatched_kicks
        modified_beats.sort(key=lambda b: b.position)

        return Pattern(
            name=f"{pattern.name}_riff_locked",
            beats=modified_beats,
            time_signature=pattern.time_signature,
            subdivision=pattern.subdivision,
            swing_ratio=pattern.swing_ratio,
            metadata={**pattern.metadata, "modification": self.name},
        )

    @staticmethod
    def _blend_position(
        old: float, target: float, period: float, intensity: float
    ) -> float:
        """Interpolate ``old`` toward ``target`` on a period-``period`` ring."""
        diff = (target - old + period / 2) % period - period / 2
        return (old + intensity * diff) % period

    def _remove_unmatched(self, unmatched_kicks: list[Beat]) -> list[Beat]:
        """Deterministically thin unmatched kicks (no randomness).

        Sorts by (velocity ascending, position ascending) so the quietest,
        earliest kicks go first, then removes
        ``floor(n * removal_strength)`` of them, capped by
        ``max_removal_fraction``. A kick at/near beat 0 (the downbeat) is
        protected when ``preserve_downbeat`` is set.
        """
        removable = list(unmatched_kicks)
        if self.preserve_downbeat:
            removable = [k for k in removable if not _is_downbeat(k.position)]
        removable.sort(key=lambda b: (b.velocity, b.position))

        fraction = min(self.removal_strength, self.max_removal_fraction)
        remove_count = int(len(unmatched_kicks) * fraction)
        to_remove_ids = {id(k) for k in removable[:remove_count]}

        return [k for k in unmatched_kicks if id(k) not in to_remove_ids]


def _is_downbeat(position: float, tolerance: float = 0.01) -> bool:
    return abs(position) <= tolerance
