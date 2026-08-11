"""Time signature value object."""

from dataclasses import dataclass


@dataclass
class TimeSignature:
    """Time signature representation."""

    numerator: int = 4
    denominator: int = 4

    @property
    def beats_per_bar(self) -> float:
        return self.numerator * (4.0 / self.denominator)

    def __str__(self) -> str:
        return f"{self.numerator}/{self.denominator}"
