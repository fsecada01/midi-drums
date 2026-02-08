"""Physical feasibility validation for drum patterns.

This module ensures that generated drum patterns are physically playable
by real drummers who have exactly 4 limbs (2 hands, 2 feet).
"""

import logging
from dataclasses import dataclass
from enum import Enum

from midi_drums.models.pattern import DrumInstrument, Pattern

logger = logging.getLogger(__name__)


class LimbAssignment(Enum):
    """Track which limb plays which instrument."""

    RIGHT_HAND = "right_hand"
    LEFT_HAND = "left_hand"
    RIGHT_FOOT = "right_foot"
    LEFT_FOOT = "left_foot"


@dataclass
class Conflict:
    """Represents a physical impossibility in a drum pattern."""

    time: float
    instruments: list[DrumInstrument]
    reason: str
    severity: str = "error"  # error, warning

    def __str__(self) -> str:
        """Human-readable conflict description."""
        inst_names = [i.name for i in self.instruments]
        return f"[{self.severity.upper()}] At beat {self.time:.2f}: {self.reason} (instruments: {', '.join(inst_names)})"


class PhysicalValidator:
    """Validates that drum patterns are physically playable by human drummers.

    A drummer has exactly 4 limbs:
    - Right Hand: Can play any drum or cymbal (ride, hi-hat, crash, snare, toms)
    - Left Hand: Can play any drum or cymbal (snare, hi-hat, toms, crash)
    - Right Foot: Operates kick drum pedal exclusively
    - Left Foot: Controls hi-hat pedal (open/close/chick)

    Physical constraints:
    1. Maximum 2 simultaneous hand strikes
    2. Ride OR hi-hat (hand), not both simultaneously
    3. Hi-hat foot pedal CAN be used while riding on ride cymbal
    4. Kick drum is right foot only
    """

    # Instruments played by hands
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

    # Instruments played by feet
    FOOT_INSTRUMENTS = {
        DrumInstrument.KICK,  # Right foot
        DrumInstrument.PEDAL_HH,  # Left foot
    }

    # Ride cymbal instruments
    RIDE_INSTRUMENTS = {
        DrumInstrument.RIDE,
        DrumInstrument.RIDE_BELL,
    }

    # Hi-hat hand instruments (cannot coexist with ride)
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

    # Hi-hat foot (CAN coexist with ride)
    HIHAT_FOOT = {DrumInstrument.PEDAL_HH}

    def __init__(self, timing_tolerance: float = 0.01):
        """Initialize validator.

        Args:
            timing_tolerance: Time window in beats to consider simultaneous (default 0.01)
        """
        self.timing_tolerance = timing_tolerance

    def validate_pattern(self, pattern: Pattern) -> list[Conflict]:
        """Check pattern for physical impossibilities.

        Args:
            pattern: Pattern to validate

        Returns:
            List of conflicts found (empty if pattern is valid)
        """
        conflicts = []

        # Group beats by timing
        time_groups = self._group_by_time(pattern.beats, self.timing_tolerance)

        for time, beats in time_groups.items():
            # Check hand limit (max 2 simultaneous)
            hand_conflicts = self._check_hand_limit(time, beats)
            conflicts.extend(hand_conflicts)

            # Check ride + hi-hat conflict
            ride_hihat_conflicts = self._check_ride_hihat_conflict(time, beats)
            conflicts.extend(ride_hihat_conflicts)

        if conflicts:
            logger.warning(
                f"Pattern '{pattern.name}' has {len(conflicts)} physical conflicts"
            )
            for conflict in conflicts:
                logger.warning(f"  {conflict}")

        return conflicts

    def is_valid(self, pattern: Pattern) -> bool:
        """Check if pattern is physically valid.

        Args:
            pattern: Pattern to check

        Returns:
            True if pattern is valid, False otherwise
        """
        conflicts = self.validate_pattern(pattern)
        return len(conflicts) == 0

    def _group_by_time(
        self, beats: list, tolerance: float
    ) -> dict[float, list]:
        """Group beats by timing position.

        Args:
            beats: List of Beat objects
            tolerance: Time window to consider simultaneous

        Returns:
            Dictionary mapping time to list of beats at that time
        """
        time_groups = {}

        for beat in beats:
            # Snap to grid based on tolerance
            time_key = round(beat.position / tolerance) * tolerance

            if time_key not in time_groups:
                time_groups[time_key] = []

            time_groups[time_key].append(beat)

        return time_groups

    def _check_hand_limit(self, time: float, beats: list) -> list[Conflict]:
        """Check if more than 2 hand instruments are played simultaneously.

        Args:
            time: Beat position
            beats: Beats at this time

        Returns:
            List of conflicts (empty if valid)
        """
        conflicts = []

        hand_beats = [b for b in beats if b.instrument in self.HAND_INSTRUMENTS]

        if len(hand_beats) > 2:
            conflicts.append(
                Conflict(
                    time=time,
                    instruments=[b.instrument for b in hand_beats],
                    reason=f"Requires {len(hand_beats)} hands, drummer has only 2",
                    severity="error",
                )
            )

        return conflicts

    def _check_ride_hihat_conflict(
        self, time: float, beats: list
    ) -> list[Conflict]:
        """Check for ride cymbal + hi-hat (hand) conflicts.

        Ride and hi-hat hand cannot be played simultaneously.
        Ride and hi-hat foot pedal CAN be played simultaneously.

        Args:
            time: Beat position
            beats: Beats at this time

        Returns:
            List of conflicts (empty if valid)
        """
        conflicts = []

        instruments_at_time = {b.instrument for b in beats}

        # Check if ride is present
        has_ride = bool(instruments_at_time & self.RIDE_INSTRUMENTS)

        # Check if hi-hat hand is present
        has_hihat_hand = bool(instruments_at_time & self.HIHAT_HAND_INSTRUMENTS)

        if has_ride and has_hihat_hand:
            conflicting_instruments = (
                instruments_at_time & self.RIDE_INSTRUMENTS
            ) | (instruments_at_time & self.HIHAT_HAND_INSTRUMENTS)

            conflicts.append(
                Conflict(
                    time=time,
                    instruments=list(conflicting_instruments),
                    reason="Ride cymbal and hi-hat (hand) cannot be played simultaneously",
                    severity="error",
                )
            )

        return conflicts

    def get_statistics(self, pattern: Pattern) -> dict:
        """Get validation statistics for a pattern.

        Args:
            pattern: Pattern to analyze

        Returns:
            Dictionary with statistics
        """
        conflicts = self.validate_pattern(pattern)

        return {
            "total_beats": len(pattern.beats),
            "total_conflicts": len(conflicts),
            "is_valid": len(conflicts) == 0,
            "error_conflicts": len(
                [c for c in conflicts if c.severity == "error"]
            ),
            "warning_conflicts": len(
                [c for c in conflicts if c.severity == "warning"]
            ),
            "conflict_types": {
                "hand_limit": len(
                    [c for c in conflicts if "hands" in c.reason.lower()]
                ),
                "ride_hihat": len(
                    [c for c in conflicts if "ride" in c.reason.lower()]
                ),
            },
        }
