"""Data models for Reaper integration."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Marker:
    """Reaper marker representation.

    Attributes:
        position_seconds: Time position in seconds
        name: Marker display name
        color: Marker color (hex string like "#FF5733" or integer)
        marker_id: Unique marker identifier (auto-assigned if not provided)
    """

    position_seconds: float
    name: str
    color: str = "#FF5733"  # Default orange
    marker_id: int | None = None

    def to_rpp_list(self) -> list:
        """Convert to RPP marker list format.

        Returns:
            List in format: ["MARKER", id, position, "name", color, flags]

        Example:
            >>> marker = Marker(8.0, "Verse", marker_id=2)
            >>> marker.to_rpp_list()
            ['MARKER', '2', '8.0', 'Verse', '0', '0']
        """
        # Convert hex color to integer if needed (simplified for now)
        color_int = "0"  # TODO: Convert hex to Reaper format (0x01BBGGRR)

        return [
            "MARKER",
            str(self.marker_id if self.marker_id else "1"),
            f"{self.position_seconds:.6f}",
            self.name,
            color_int,
            "0",  # Flags (0 = regular marker)
        ]

    @classmethod
    def from_rpp_list(cls, rpp_list: list) -> "Marker":
        """Create Marker from RPP list format.

        Args:
            rpp_list: List in format ["MARKER", id, position, name, ...]

        Returns:
            Marker instance

        Example:
            >>> rpp_data = ["MARKER", "2", "8.0", "Verse", "0", "0"]
            >>> marker = Marker.from_rpp_list(rpp_data)
            >>> marker.name
            'Verse'
        """
        if rpp_list[0] != "MARKER":
            raise ValueError(f"Expected 'MARKER' tag, got '{rpp_list[0]}'")

        marker_id = int(rpp_list[1])
        position = float(rpp_list[2])
        name = rpp_list[3]

        return cls(
            position_seconds=position,
            name=name,
            color="#FF5733",  # Default
            marker_id=marker_id,
        )


@dataclass
class ReaperTrack:
    """Reaper track representation.

    Attributes:
        name: Track name
        midi_source: Path to MIDI file (optional)
        volume: Track volume (0.0-1.0, default 1.0)
        pan: Stereo pan (-1.0 to 1.0, default 0.0)
    """

    name: str
    midi_source: str | None = None
    volume: float = 1.0
    pan: float = 0.0

    def __post_init__(self):
        """Validate track parameters."""
        if not 0.0 <= self.volume <= 2.0:
            raise ValueError(f"Volume must be 0.0-2.0, got {self.volume}")
        if not -1.0 <= self.pan <= 1.0:
            raise ValueError(f"Pan must be -1.0 to 1.0, got {self.pan}")
