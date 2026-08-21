"""Riff accent value objects - rhythmic accent data extracted from audio.

These carry the output of :mod:`midi_drums.analysis.audio_analysis` (onset
detection on a rendered riff) into
:class:`midi_drums.modifications.riff_lock.RiffLockTransform`. They are
plain value objects with no audio/DSP dependency of their own, so they can
be constructed directly in tests without librosa installed.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RiffAccent:
    """A single rhythmic accent within one bar.

    Args:
        position: Beat position within the bar (0.0-based, tempo-relative
            beats - same coordinate space as ``Beat.position`` mod
            ``beats_per_bar``). Validated against the owning
            ``RiffAccentMap.beats_per_bar`` at construction, not here,
            since a bare ``RiffAccent`` doesn't know its bar length.
        strength: Onset strength, normalized 0.0-1.0.
    """

    position: float
    strength: float

    def __post_init__(self) -> None:
        if self.position < 0:
            raise ValueError(
                f"position cannot be negative, got {self.position}"
            )
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(
                f"strength must be between 0.0 and 1.0, got {self.strength}"
            )


@dataclass(frozen=True)
class RiffAccentMap:
    """A bar's worth of rhythmic accents extracted from a riff.

    Represents exactly one representative bar (v1 scope - see
    ``midi_drums/modifications/riff_lock.py``). All accent positions are
    expected to fall within ``[0, beats_per_bar)``.
    """

    accents: tuple[RiffAccent, ...] = field(default_factory=tuple)
    beats_per_bar: float = 4.0

    def __post_init__(self) -> None:
        if self.beats_per_bar <= 0:
            raise ValueError(
                f"beats_per_bar must be positive, got {self.beats_per_bar}"
            )
        for accent in self.accents:
            if not 0.0 <= accent.position < self.beats_per_bar:
                raise ValueError(
                    f"accent position {accent.position} out of range "
                    f"[0, {self.beats_per_bar})"
                )

    def __len__(self) -> int:
        return len(self.accents)

    def strong_accents(self, threshold: float = 0.6) -> tuple[RiffAccent, ...]:
        """Accents at or above ``threshold`` strength, strongest first."""
        return tuple(
            sorted(
                (a for a in self.accents if a.strength >= threshold),
                key=lambda a: a.strength,
                reverse=True,
            )
        )

    @classmethod
    def from_positions(
        cls,
        positions_and_strengths: list[tuple[float, float]],
        beats_per_bar: float = 4.0,
    ) -> "RiffAccentMap":
        """Convenience constructor for tests and quick scripting.

        Args:
            positions_and_strengths: List of ``(position, strength)`` pairs.
            beats_per_bar: Bar length in beats.
        """
        return cls(
            accents=tuple(
                RiffAccent(position=p, strength=s)
                for p, s in positions_and_strengths
            ),
            beats_per_bar=beats_per_bar,
        )
