"""Additive rhythmic-grouping (box notation / TUBS) -> TimeSignature.

Spike converting a prose-friendly additive grouping string (e.g.
"3-3-3-3-2-2" at a 16th-note grid) into one or more bars, each resolved
to a conventionally-labeled TimeSignature plus the accent positions
within it - see claudedocs/design_additive_rhythm_grouping.md for the
full design, including why two different input syntaxes are needed to
disambiguate "a run of repeated pulses" from "one heterogeneous additive
bar" (e.g. a 7/8 Balkan rhythm).
"""

from dataclasses import dataclass

from midi_drums.core.value_objects.time_signature import TimeSignature

_SEPARATORS = ("-", "+", ",")


@dataclass(frozen=True)
class GroupedBar:
    """One bar's worth of additive groups, resolved to a TimeSignature.

    `groups` are counted in grid units (e.g. sixteenth notes) and mark
    where each accent falls - an additive-rhythm pattern accents group
    boundaries, not plain beat boundaries.
    """

    time_signature: TimeSignature
    groups: tuple[int, ...]


def _is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def _canonicalize_run(
    count: int, group_size: int, grid_denominator: int
) -> TimeSignature:
    """Convert `count` repeated `group_size`-unit groups into a TimeSignature.

    See the design doc's "Canonicalization rule" section for the full
    rationale; summary:
    - `group_size` a power of two (simple/duple grouping - the group
      already is a beat): divide it out directly,
      `(count, grid_denominator // group_size)`.
    - Otherwise (compound grouping, e.g. groups of 3): halve numerator
      and denominator once, only if both are even and the halved
      denominator stays >= 8 - preserves the compound-meter signal that
      full reduction to lowest terms would destroy.
    """
    numerator = count * group_size
    denominator = grid_denominator
    if _is_power_of_two(group_size):
        return TimeSignature(count, denominator // group_size)
    if numerator % 2 == 0 and denominator % 2 == 0 and denominator // 2 >= 8:
        return TimeSignature(numerator // 2, denominator // 2)
    return TimeSignature(numerator, denominator)


def _parse_flat_groups(segment: str) -> list[int]:
    cleaned = segment.strip()
    for sep in _SEPARATORS[1:]:
        cleaned = cleaned.replace(sep, _SEPARATORS[0])
    parts = [p.strip() for p in cleaned.split(_SEPARATORS[0]) if p.strip()]
    if not parts:
        raise ValueError(f"No groups found in {segment!r}")
    return [int(p) for p in parts]


def parse_groups(spec: str) -> list[list[int]]:
    """Parse a grouping spec into a list of bars of int groups.

    `|` explicitly marks a bar boundary - each `|`-delimited segment is
    taken as one bar exactly as written, however heterogeneous (classic
    additive notation, e.g. "2+2+3|" for a single 7/8 bar - a trailing or
    otherwise-empty segment is dropped, so a lone `|` is enough to force
    single-explicit-bar reading without a second bar). Without any `|`,
    the whole string is returned as one flat bar; callers doing
    auto-detection should further split it with `split_into_bars`.

    Groups may be separated by "-", "+", or "," (all equivalent).
    """
    if "|" in spec:
        segments = [s for s in spec.split("|") if s.strip()]
        return [_parse_flat_groups(segment) for segment in segments]
    return [_parse_flat_groups(spec)]


def split_into_bars(groups: list[int]) -> list[list[int]]:
    """Split one flat group sequence into bars by runs of identical values.

    Auto-detection heuristic for un-delimited input: each maximal run of
    consecutive, identical group sizes is one bar of that many repeated
    pulses, e.g. [3, 3, 3, 3, 2, 2] -> [[3, 3, 3, 3], [2, 2]]. This
    cannot distinguish that from a single intentionally heterogeneous bar
    like [2, 2, 3] (a 7/8 Balkan bar) - that case needs the explicit `|`
    syntax in `parse_groups` instead.
    """
    if not groups:
        return []
    bars = [[groups[0]]]
    for g in groups[1:]:
        if g == bars[-1][-1]:
            bars[-1].append(g)
        else:
            bars.append([g])
    return bars


def _resolve_bar(groups: list[int], grid_denominator: int) -> GroupedBar:
    """Resolve one bar's groups to a GroupedBar.

    A *uniform* bar (every group the same size - always true of an
    auto-detected run, and true of an explicit `|`-delimited segment
    when the user happened to write one) gets the same repeated-pulse
    canonicalization either way. A genuinely heterogeneous explicit bar
    (e.g. [2, 2, 3]) has no repeated pulse to canonicalize against, so it
    sums directly at the grid's own denominator - classic TUBS notation,
    unmodified.
    """
    if len(set(groups)) == 1:
        ts = _canonicalize_run(len(groups), groups[0], grid_denominator)
    else:
        ts = TimeSignature(sum(groups), grid_denominator)
    return GroupedBar(time_signature=ts, groups=tuple(groups))


def resolve_grouping(spec: str, grid_denominator: int) -> list[GroupedBar]:
    """Parse and resolve a grouping spec into GroupedBars.

    See module docstring / design doc for the two supported syntaxes
    (explicit `|` bars vs. auto-split runs).
    """
    if "|" in spec:
        return [
            _resolve_bar(bar_groups, grid_denominator)
            for bar_groups in parse_groups(spec)
        ]

    (flat,) = parse_groups(spec)
    return [
        _resolve_bar(run, grid_denominator) for run in split_into_bars(flat)
    ]
