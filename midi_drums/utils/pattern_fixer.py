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

        # Fix ride + hi-hat conflicts
        fixed_pattern = self.remove_ride_hihat_conflicts(fixed_pattern)

        if self.fixes_applied:
            logger.info(
                f"Applied {len(self.fixes_applied)} fixes to pattern '{pattern.name}'"
            )
            for fix in self.fixes_applied:
                logger.info(f"  - {fix}")

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
