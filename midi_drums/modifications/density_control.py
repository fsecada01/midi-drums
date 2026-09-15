"""Amount/density control for the Step Editor's per-lane +/- knob (ADR 0010).

Not a reproduction of Toontrack's undisclosed EZDrummer 3 Amount algorithm
- no public technical description of it exists (see
claudedocs/research_ezdrummer3_editplaystyle_20260914.md's evidence-gap
note). This is an original, deliberately simple heuristic: positive
`amount` inserts additional hits at open grid slots (ghost-velocity for
`kind="ghost"`, mirroring GhostNoteLayer's random-gated insertion in
drummer_mods.py without depending on its Pattern/Beat machinery, since this
module operates on the Step Editor's flat single-lane note-dict shape);
negative `amount` removes existing hits, weighted toward the
lowest-velocity ones first (accent state isn't part of this flat shape, so
velocity is the only signal available for "least load-bearing hit").

Operates on the same flat per-note dict shape reaper/midi_drums/step_editor.lua
uses for `lane.notes` (`bar`, `step`, `velocity`, `off_grid`, `_idx`) so the
CLI round-trip (adjust-density, cli.py) needs no field translation in
either direction. `ppqpos` is deliberately absent from both input and
output here: it's REAPER-take-specific (this module has no way to compute
real tick positions), so newly inserted notes carry only `bar`/`step` -
resolving that to a real `ppqpos` is the Lua-side caller's job when it
merges the result back into `data.lanes[lane]` and commits.
"""

from __future__ import annotations

import random
from typing import Any

from midi_drums.config.constants import VELOCITY

# Mirrors reaper/midi_drums/step_editor.lua's STEPS_PER_QUARTER table and
# the same "8th"/"16th"/"32nd"/"8th_triplet"/"16th_triplet" grid vocabulary
# used by the `riff` command's --grid choices - the fixed set shared across
# the Lua<->Python bridge (not plugin-discovered data).
STEPS_PER_QUARTER: dict[str, int] = {
    "8th": 2,
    "16th": 4,
    "32nd": 8,
    "8th_triplet": 3,
    "16th_triplet": 6,
}

GHOST_VELOCITY: int = VELOCITY.SNARE_GHOST
DEFAULT_MAIN_VELOCITY: int = 100

Note = dict[str, Any]


def steps_per_bar(grid_resolution: str, ts_num: int, ts_denom: int) -> int:
    """Steps per bar for a grid resolution + time signature.

    Mirrors step_editor.lua's `M.steps_per_bar` exactly (same rounding),
    so Python and Lua agree on step counts for the same inputs.
    """
    steps_per_quarter = STEPS_PER_QUARTER.get(grid_resolution)
    if steps_per_quarter is None:
        raise ValueError(f"Unknown grid_resolution: {grid_resolution!r}")
    qn_per_bar = ts_num * (4.0 / ts_denom)
    return round(qn_per_bar * steps_per_quarter)


def _estimate_main_velocity(notes: list[Note]) -> int:
    if not notes:
        return DEFAULT_MAIN_VELOCITY
    return round(sum(n["velocity"] for n in notes) / len(notes))


def _insert_hits(
    notes: list[Note],
    amount: float,
    kind: str,
    steps_per_bar_n: int,
    bars: int,
    complexity: float,
    rng: random.Random,
) -> list[Note]:
    occupied = {(n["bar"], n["step"]) for n in notes}
    velocity = (
        GHOST_VELOCITY if kind == "ghost" else _estimate_main_velocity(notes)
    )
    # complexity biases how readily open slots fill in, without letting a
    # low-complexity context zero out amount entirely (0.5 floor).
    probability = min(1.0, amount) * (0.5 + 0.5 * complexity)

    result = list(notes)
    for bar in range(bars):
        for step in range(steps_per_bar_n):
            if (bar, step) in occupied:
                continue
            if rng.random() < probability:
                result.append(
                    {
                        "bar": bar,
                        "step": step,
                        "velocity": velocity,
                        "off_grid": False,
                        "_idx": None,
                    }
                )
    return result


def _remove_hits(notes: list[Note], amount: float) -> list[Note]:
    if not notes:
        return []
    probability = min(1.0, -amount)
    ordered = sorted(notes, key=lambda n: n["velocity"])
    remove_count = round(len(ordered) * probability)
    to_remove = {id(n) for n in ordered[:remove_count]}
    return [n for n in notes if id(n) not in to_remove]


def adjust_density(
    notes: list[Note],
    amount: float,
    kind: str,
    grid_resolution: str,
    ts_num: int = 4,
    ts_denom: int = 4,
    bars: int = 1,
    context: dict[str, Any] | None = None,
) -> list[Note]:
    """Add or remove hits in one lane's notes, biased by `amount`.

    `amount` in [-1.0, 1.0]: positive inserts plausible new hits at open
    grid slots (probability-gated per slot, biased up by `context`'s
    `complexity` when given); negative removes existing hits starting
    from the lowest-velocity ones. `amount == 0.0` is a no-op. `context`
    (genre/style/drummer/complexity, ADR 0009's provenance metadata) is
    optional - only `complexity` currently affects the heuristic, and its
    absence must not raise, per ADR 0010's decision that this degrades to
    a context-free heuristic rather than failing.
    """
    if not -1.0 <= amount <= 1.0:
        raise ValueError(f"amount must be between -1.0 and 1.0, got {amount}")
    if kind not in ("main", "ghost"):
        raise ValueError(f"Unknown kind: {kind!r} (expected 'main' or 'ghost')")
    if bars < 1:
        raise ValueError(f"bars must be >= 1, got {bars}")

    spb = steps_per_bar(grid_resolution, ts_num, ts_denom)

    if amount == 0.0:
        return list(notes)

    if amount > 0:
        complexity = 1.0
        if context and context.get("complexity") is not None:
            complexity = max(0.0, min(1.0, float(context["complexity"])))
        return _insert_hits(
            notes, amount, kind, spb, bars, complexity, random.Random()
        )

    return _remove_hits(notes, amount)
