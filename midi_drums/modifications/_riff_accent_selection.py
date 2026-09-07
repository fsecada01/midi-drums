"""Shared accent-selection math for riff-driven modifications.

Extracted from :mod:`midi_drums.modifications.riff_lock` so
:class:`midi_drums.modifications.snare_accent_reaction.SnareAccentReaction`
doesn't re-derive the same greedy strength-descending + circular-spacing
selection logic a second time - in particular the bar-boundary wraparound
case (``circular_distance``), which is the single most likely place to get
this wrong twice.

Private module (leading underscore): not part of the package's public
surface, imported directly by the two modification modules that need it.
"""

from typing import Protocol

from midi_drums.core.value_objects.riff_accent import RiffAccent, RiffAccentMap


class _HasPosition(Protocol):
    position: float


def circular_distance(a: float, b: float, period: float) -> float:
    """Shortest distance between two positions on a period-``period`` ring.

    E.g. with period=4.0, positions 3.875 and 0.0 are 0.125 apart, not
    3.875 apart - this is the wraparound case that must be handled at a bar
    boundary.
    """
    diff = abs(a - b) % period
    return min(diff, period - diff)


def select_accents(
    riff_accents: RiffAccentMap,
    threshold: float,
    max_count: int,
    min_spacing_beats: float,
) -> list[RiffAccent]:
    """Greedily pick strong accents respecting spacing/count budgets.

    Candidates come out of :meth:`RiffAccentMap.strong_accents` already
    sorted strongest-first; this keeps the strongest accents and skips any
    candidate that would land within ``min_spacing_beats`` (circular) of an
    already-kept accent, stopping once ``max_count`` are kept.
    """
    candidates = riff_accents.strong_accents(threshold)
    beats_per_bar = riff_accents.beats_per_bar

    selected: list[RiffAccent] = []
    for accent in candidates:
        if len(selected) >= max_count:
            break
        if all(
            circular_distance(accent.position, kept.position, beats_per_bar)
            >= min_spacing_beats
            for kept in selected
        ):
            selected.append(accent)
    return selected


def nearest_within(
    position: float,
    candidates: list,
    period: float,
    tolerance: float,
    exclude_ids: frozenset = frozenset(),
) -> _HasPosition | None:
    """Nearest of ``candidates`` (anything with a ``.position``) to
    ``position`` within ``tolerance`` (circular), or ``None``.

    ``exclude_ids`` (a set of ``id(candidate)`` values) lets callers rule
    out candidates already matched to a different accent in the same pass
    - e.g. so two accents can't both claim the same kick (see
    ``RiffLockTransform.apply``'s ``matched_kick_ids``).
    """
    best = None
    best_distance = None
    for candidate in candidates:
        if id(candidate) in exclude_ids:
            continue
        distance = circular_distance(position, candidate.position, period)
        if distance <= tolerance and (
            best_distance is None or distance < best_distance
        ):
            best = candidate
            best_distance = distance
    return best
