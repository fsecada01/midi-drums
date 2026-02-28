"""Utilities for automatically fixing physical conflicts in drum patterns.

This module provides tools to resolve physical impossibilities while
preserving musical intent.
"""

import logging
from collections import defaultdict

from midi_drums.models.pattern import DrumInstrument, Pattern

logger = logging.getLogger(__name__)


class PatternFixer:
    """Automatically fixes physical conflicts in drum patterns."""

    # Ride cymbal instruments
    RIDE_INSTRUMENTS = {
        DrumInstrument.RIDE,
        DrumInstrument.RIDE_BELL,
    }

    # Hi-hat hand instruments that conflict with ride
    HIHAT_HAND_INSTRUMENTS = {
        DrumInstrument.CLOSED_HH,
        DrumInstrument.CLOSED_HH_EDGE,
        DrumInstrument.CLOSED_HH_TIP,
        DrumInstrument.TIGHT_HH_EDGE,
        DrumInstrument.TIGHT_HH_TIP,
        DrumInstrument.OPEN_HH,
        DrumInstrument.OPEN_HH_1,
        DrumInstrument.OPEN_HH_2,
        DrumInstrument.OPEN_HH_3,
        DrumInstrument.OPEN_HH_MAX,
    }

    # All hand instruments (mirrors PhysicalValidator.HAND_INSTRUMENTS)
    HAND_INSTRUMENTS = {
        DrumInstrument.RIDE,
        DrumInstrument.RIDE_BELL,
        DrumInstrument.CLOSED_HH,
        DrumInstrument.CLOSED_HH_EDGE,
        DrumInstrument.CLOSED_HH_TIP,
        DrumInstrument.TIGHT_HH_EDGE,
        DrumInstrument.TIGHT_HH_TIP,
        DrumInstrument.OPEN_HH,
        DrumInstrument.OPEN_HH_1,
        DrumInstrument.OPEN_HH_2,
        DrumInstrument.OPEN_HH_3,
        DrumInstrument.OPEN_HH_MAX,
        DrumInstrument.SNARE,
        DrumInstrument.RIM,
        DrumInstrument.MID_TOM,
        DrumInstrument.FLOOR_TOM,
        DrumInstrument.CRASH,
        DrumInstrument.SPLASH,
        DrumInstrument.CHINA,
    }

    # Priority for retaining hand instruments when > 2 are simultaneous.
    # Higher number = keep this first.  Cymbals (crash/splash/china) are
    # lowest priority because they are the most dispensable ornaments.
    HAND_PRIORITY: dict = {
        DrumInstrument.SNARE: 10,
        DrumInstrument.CLOSED_HH: 9,
        DrumInstrument.CLOSED_HH_EDGE: 9,
        DrumInstrument.CLOSED_HH_TIP: 9,
        DrumInstrument.OPEN_HH: 8,
        DrumInstrument.OPEN_HH_1: 8,
        DrumInstrument.OPEN_HH_2: 8,
        DrumInstrument.OPEN_HH_3: 8,
        DrumInstrument.OPEN_HH_MAX: 8,
        DrumInstrument.TIGHT_HH_EDGE: 8,
        DrumInstrument.TIGHT_HH_TIP: 8,
        DrumInstrument.RIDE: 7,
        DrumInstrument.RIDE_BELL: 7,
        DrumInstrument.RIM: 6,
        DrumInstrument.FLOOR_TOM: 5,
        DrumInstrument.MID_TOM: 5,
        DrumInstrument.CRASH: 4,
        DrumInstrument.SPLASH: 3,
        DrumInstrument.CHINA: 3,
    }

    def __init__(self, timing_tolerance: float = 0.01):
        """Initialize pattern fixer.

        Args:
            timing_tolerance: Time window to consider simultaneous beats
        """
        self.timing_tolerance = timing_tolerance
        self.fixes_applied = []

    def fix_pattern(self, pattern: Pattern) -> Pattern:
        """Apply all automatic fixes to a pattern.

        Args:
            pattern: Pattern to fix

        Returns:
            Fixed pattern (new copy)
        """
        fixed_pattern = pattern.copy()
        self.fixes_applied = []

        # Remove duplicate beats (same position + instrument) first
        fixed_pattern = self.remove_duplicate_beats(fixed_pattern)

        # Remove simultaneous conflicting hi-hat states (e.g. CLOSED_HH + OPEN_HH)
        fixed_pattern = self.remove_simultaneous_hihat_conflicts(fixed_pattern)

        # Fix ride + hi-hat conflicts
        fixed_pattern = self.remove_ride_hihat_conflicts(fixed_pattern)

        # Fix "too many hands" — >2 hand instruments at the same time
        fixed_pattern = self.remove_too_many_hand_instruments(fixed_pattern)

        if self.fixes_applied:
            logger.info(
                f"Applied {len(self.fixes_applied)} fixes to pattern '{pattern.name}'"
            )
            for fix in self.fixes_applied:
                logger.info(f"  - {fix}")

        return fixed_pattern

    def remove_duplicate_beats(self, pattern: Pattern) -> Pattern:
        """Remove duplicate beats at the same position with the same instrument.

        When multiple drummer modifications are layered, the same instrument
        can end up with multiple beats at identical positions. These duplicates
        are musically redundant and cause spurious physical-constraint violations
        (e.g. "requires 3 hands" when two of them are the same cymbal).

        Strategy: keep only the loudest beat when duplicates exist at the
        same (position, instrument) key.

        Args:
            pattern: Pattern to deduplicate

        Returns:
            Fixed pattern (new copy)
        """
        fixed_pattern = pattern.copy()
        seen: dict[tuple, object] = {}

        for beat in fixed_pattern.beats:
            key = (round(beat.position, 4), beat.instrument)
            if key not in seen or beat.velocity > seen[key].velocity:  # type: ignore[attr-defined]
                seen[key] = beat

        original_count = len(fixed_pattern.beats)
        fixed_pattern.beats = sorted(seen.values(), key=lambda b: b.position)
        removed = original_count - len(fixed_pattern.beats)
        if removed:
            self.fixes_applied.append(f"Removed {removed} duplicate beat(s)")

        return fixed_pattern

    def remove_simultaneous_hihat_conflicts(self, pattern: Pattern) -> Pattern:
        """Remove cases where multiple hi-hat hand instruments are simultaneous.

        A drummer's right hand can only be in one hi-hat position at a time.
        When layered modifications produce e.g. CLOSED_HH + OPEN_HH at the same
        position, that requires two hands for the hi-hat alone, which is
        physically impossible.

        Strategy: keep only the loudest hi-hat hand instrument at each position.

        Args:
            pattern: Pattern to fix

        Returns:
            Fixed pattern (new copy)
        """
        fixed_pattern = pattern.copy()

        time_groups = self._group_by_time(
            fixed_pattern.beats, self.timing_tolerance
        )

        beats_to_remove = []

        for _time, beats in time_groups.items():
            hihat_beats = [
                b for b in beats if b.instrument in self.HIHAT_HAND_INSTRUMENTS
            ]
            if len(hihat_beats) > 1:
                # Keep only the loudest; remove the rest
                hihat_beats.sort(key=lambda b: b.velocity, reverse=True)
                to_remove = hihat_beats[1:]
                beats_to_remove.extend(to_remove)

        if beats_to_remove:
            removed_names = ", ".join(
                b.instrument.name for b in beats_to_remove
            )
            fixed_pattern.beats = [
                b for b in fixed_pattern.beats if b not in beats_to_remove
            ]
            fixed_pattern.beats.sort(key=lambda b: b.position)
            self.fixes_applied.append(
                f"Removed {len(beats_to_remove)} simultaneous hi-hat "
                f"conflict(s): {removed_names}"
            )

        return fixed_pattern

    def remove_ride_hihat_conflicts(self, pattern: Pattern) -> Pattern:
        """Remove ride + hi-hat (hand) conflicts.

        Strategy:
        1. Find times where both ride and hi-hat (hand) are present
        2. Remove hi-hat hand hits at those times
        3. Optionally add hi-hat foot pedal for texture

        Args:
            pattern: Pattern to fix

        Returns:
            Fixed pattern (new copy)
        """
        fixed_pattern = pattern.copy()

        # Group beats by time
        time_groups = self._group_by_time(
            fixed_pattern.beats, self.timing_tolerance
        )

        # Find and resolve conflicts
        beats_to_remove = []
        beats_to_add = []

        for time, beats in time_groups.items():
            instruments = {b.instrument for b in beats}

            # Check for ride + hi-hat conflict
            has_ride = bool(instruments & self.RIDE_INSTRUMENTS)
            has_hihat_hand = bool(instruments & self.HIHAT_HAND_INSTRUMENTS)

            if has_ride and has_hihat_hand:
                # Find hi-hat hand beats to remove
                hihat_beats = [
                    b
                    for b in beats
                    if b.instrument in self.HIHAT_HAND_INSTRUMENTS
                ]

                # Mark for removal
                beats_to_remove.extend(hihat_beats)

                # Calculate average hi-hat velocity for foot pedal
                avg_velocity = (
                    sum(b.velocity for b in hihat_beats) // len(hihat_beats)
                    if hihat_beats
                    else 65
                )

                # Add foot pedal as replacement (softer than hand)
                foot_velocity = max(50, avg_velocity - 20)

                # Create foot pedal beat
                # Use the first hi-hat beat's position for timing
                if hihat_beats:
                    from midi_drums.models.pattern import Beat

                    foot_beat = Beat(
                        position=hihat_beats[0].position,
                        instrument=DrumInstrument.PEDAL_HH,
                        velocity=foot_velocity,
                        duration=0.25,
                    )
                    beats_to_add.append(foot_beat)

                    # Log the fix
                    removed_instruments = ", ".join(
                        [b.instrument.name for b in hihat_beats]
                    )
                    self.fixes_applied.append(
                        f"At beat {time:.2f}: Removed {removed_instruments}, "
                        f"added PEDAL_HH (velocity {foot_velocity})"
                    )

        # Apply removals
        fixed_pattern.beats = [
            b for b in fixed_pattern.beats if b not in beats_to_remove
        ]

        # Apply additions
        fixed_pattern.beats.extend(beats_to_add)

        # Sort beats by position
        fixed_pattern.beats.sort(key=lambda b: b.position)

        return fixed_pattern

    def remove_too_many_hand_instruments(self, pattern: Pattern) -> Pattern:
        """Remove excess hand instruments when more than 2 are simultaneous.

        A drummer has only 2 hands.  When layered modifications produce 3+
        hand instruments at the same position the lowest-priority ones are
        dropped so the pattern remains physically playable.

        Priority (highest kept first): snare > hi-hat variants > ride >
        rim/toms > crash > splash/china.  Velocity is the tiebreaker within
        the same priority level.

        Args:
            pattern: Pattern to fix

        Returns:
            Fixed pattern (new copy)
        """
        fixed_pattern = pattern.copy()

        time_groups = self._group_by_time(
            fixed_pattern.beats, self.timing_tolerance
        )

        beats_to_remove = []

        for _time, beats in time_groups.items():
            hand_beats = [
                b for b in beats if b.instrument in self.HAND_INSTRUMENTS
            ]
            if len(hand_beats) <= 2:
                continue

            # Sort: highest priority first, then loudest as tiebreaker
            hand_beats.sort(
                key=lambda b: (
                    self.HAND_PRIORITY.get(b.instrument, 0),
                    b.velocity,
                ),
                reverse=True,
            )
            # Remove everything beyond the first 2
            to_remove = hand_beats[2:]
            beats_to_remove.extend(to_remove)

        if beats_to_remove:
            removed_names = ", ".join(
                b.instrument.name for b in beats_to_remove
            )
            fixed_pattern.beats = [
                b for b in fixed_pattern.beats if b not in beats_to_remove
            ]
            fixed_pattern.beats.sort(key=lambda b: b.position)
            self.fixes_applied.append(
                f"Removed {len(beats_to_remove)} excess hand instrument(s) "
                f"to satisfy 2-hand limit: {removed_names}"
            )

        return fixed_pattern

    def _group_by_time(self, beats: list, tolerance: float) -> dict:
        """Group beats by timing position.

        Args:
            beats: List of Beat objects
            tolerance: Time window to consider simultaneous

        Returns:
            Dictionary mapping time to list of beats
        """
        time_groups = defaultdict(list)

        for beat in beats:
            # Snap to grid based on tolerance
            time_key = round(beat.position / tolerance) * tolerance
            time_groups[time_key].append(beat)

        return dict(time_groups)


# Convenience function for quick fixes
def remove_ride_hihat_conflicts(pattern: Pattern) -> Pattern:
    """Quick fix: Remove ride + hi-hat conflicts from a pattern.

    This is a convenience function that creates a PatternFixer
    and applies ride/hi-hat conflict resolution.

    Args:
        pattern: Pattern to fix

    Returns:
        Fixed pattern (new copy)

    Example:
        >>> from midi_drums.utils.pattern_fixer import remove_ride_hihat_conflicts
        >>> fixed_pattern = remove_ride_hihat_conflicts(my_pattern)
    """
    fixer = PatternFixer()
    return fixer.remove_ride_hihat_conflicts(pattern)
