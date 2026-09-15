"""Apply Drummer round-trip for the Step Editor (ADR 0011).

Reuses two existing Python operations that were previously only reachable
during initial generation - `PluginManager.apply_drummer_style` (drummer
plugin modifications: BehindBeatTiming, TripletVocabulary, GhostNoteLayer,
etc.) and `Pattern.humanize` (independent timing/velocity jitter) - and
makes them reachable from the Step Editor's "Apply Drummer" control on an
already-loaded pattern.

Unlike ADR 0010's `adjust_density` (single lane, exact grid slots only),
this operates on the *whole* pattern at once and deliberately round-trips
`position_qn` (exact float quarter-notes from pattern start) instead of
integer `bar`/`step`: humanization produces genuinely off-grid timing by
design, and bar/step would silently snap it back onto the grid. `ppqpos`
is still never computed here - resolving `position_qn` to a real
take-local `ppqpos` is the Lua-side merge's job (`step_editor.lua`'s
`M.qn_to_ppq`), same division of responsibility as ADR 0010.

A note whose `instrument` isn't a recognized `DrumInstrument` member (an
"Unmapped (note N)" Step Editor lane) passes through completely
unchanged - drummer plugins have no concept of an unmapped pitch.
"""

from __future__ import annotations

from typing import Any

from midi_drums.core.models.pattern import Beat, Pattern
from midi_drums.core.value_objects.drum_instrument import DrumInstrument
from midi_drums.core.value_objects.time_signature import TimeSignature

Note = dict[str, Any]

_INSTRUMENT_NAMES = {member.name for member in DrumInstrument}


def apply_drummer(
    notes: list[Note],
    drummer: str | None,
    intensity: float,
    timing_variance: float,
    velocity_variance: float,
    ts_num: int = 4,
    ts_denom: int = 4,
    plugin_manager: Any = None,
) -> list[Note]:
    """Apply drummer style and/or humanization to a whole flat note list.

    `notes` is a flat list of per-note dicts, each carrying an
    `instrument` (lane key, e.g. "KICK"/"SNARE") plus `position_qn`,
    `velocity`, and optionally `ghost_note`/`accent`. Notes with an
    unrecognized `instrument` pass through unchanged. `drummer` falsy
    skips style application entirely; `timing_variance == velocity_variance
    == 0.0` skips humanization entirely - both no-ops compose, so passing
    neither performs an identity round-trip (mapped notes still get
    rebuilt through Beat/Pattern, but their values are unchanged).
    """
    if not 0.0 <= intensity <= 1.0:
        raise ValueError(
            f"intensity must be between 0.0 and 1.0, got {intensity}"
        )
    if timing_variance < 0:
        raise ValueError(f"timing_variance must be >= 0, got {timing_variance}")
    if velocity_variance < 0:
        raise ValueError(
            f"velocity_variance must be >= 0, got {velocity_variance}"
        )

    mapped, passthrough = [], []
    for n in notes:
        (
            mapped if n.get("instrument") in _INSTRUMENT_NAMES else passthrough
        ).append(n)

    if not mapped:
        return list(passthrough)

    beats = [
        Beat(
            position=n["position_qn"],
            instrument=DrumInstrument[n["instrument"]],
            velocity=n["velocity"],
            ghost_note=n.get("ghost_note", False),
            accent=n.get("accent", False),
        )
        for n in mapped
    ]
    pattern = Pattern(
        name="step_editor_apply_drummer",
        beats=beats,
        time_signature=TimeSignature(ts_num, ts_denom),
    )

    if drummer:
        if plugin_manager is None:
            from midi_drums.generation.engines.drum_generator import (
                DrumGenerator,
            )

            plugin_manager = DrumGenerator().plugin_manager
        styled = plugin_manager.apply_drummer_style(
            pattern, drummer, intensity=intensity
        )
        pattern = styled if styled is not None else pattern

    if timing_variance > 0.0 or velocity_variance > 0.0:
        # Pattern.humanize's velocity_variance feeds random.randint, which
        # requires int bounds - matches the int(...) cast every other
        # humanize() call site in this codebase already applies
        # (drum_generator.py, cli.py's --humanize path).
        pattern = pattern.humanize(
            timing_variance=timing_variance,
            velocity_variance=int(velocity_variance),
        )

    result = [
        {
            "instrument": beat.instrument.name,
            "position_qn": beat.position,
            "velocity": beat.velocity,
            "ghost_note": beat.ghost_note,
            "accent": beat.accent,
        }
        for beat in pattern.beats
    ]
    return result + passthrough
