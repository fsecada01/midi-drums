"""Build Patterns from an additive rhythmic-grouping spec.

Standalone builder for the additive-rhythm-grouping spike (see
claudedocs/design_additive_rhythm_grouping.md) - not a genre-plugin
method, since no genre plugin supports non-4/4 generation today. Each
bar gets a minimal, deliberately un-styled kick+hihat skeleton: a kick
accent at every group's start, and a closed hi-hat on every grid unit as
a plain timekeeping layer.
"""

from midi_drums.config import VELOCITY
from midi_drums.core.models.pattern import Pattern
from midi_drums.core.value_objects.rhythmic_grouping import (
    GroupedBar,
    resolve_grouping,
)
from midi_drums.generation.builders.pattern_builder import PatternBuilder


def _unit_beats(grid_denominator: int) -> float:
    """Beats (quarter notes) per grid unit - e.g. 0.25 for a 16th grid."""
    return 4.0 / grid_denominator


def build_pattern_for_bar(
    bar: GroupedBar, grid_denominator: int, bar_index: int
) -> Pattern:
    """Build one bar's Pattern: kick per group start, hihat per grid unit."""
    unit_beats = _unit_beats(grid_denominator)
    builder = PatternBuilder(
        f"additive_bar_{bar_index}", time_signature=bar.time_signature
    )

    total_units = sum(bar.groups)
    for unit in range(total_units):
        builder.hihat(unit * unit_beats, VELOCITY.HIHAT_LIGHT)

    cursor = 0
    for group in bar.groups:
        builder.kick(cursor * unit_beats, VELOCITY.KICK_ACCENT)
        cursor += group

    return builder.build()


def build_additive_rhythm_bars(
    spec: str, grid_denominator: int
) -> list[Pattern]:
    """Parse `spec` and build one Pattern per resolved bar.

    See `midi_drums.core.value_objects.rhythmic_grouping.resolve_grouping`
    for the grouping spec syntax (auto-split runs vs. explicit `|` bars).
    """
    grouped_bars = resolve_grouping(spec, grid_denominator)
    return [
        build_pattern_for_bar(bar, grid_denominator, i)
        for i, bar in enumerate(grouped_bars)
    ]
