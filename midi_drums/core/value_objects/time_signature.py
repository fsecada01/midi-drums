"""Time signature value object."""

from dataclasses import dataclass


@dataclass
class TimeSignature:
    """Time signature representation."""

    numerator: int = 4
    denominator: int = 4

    def __post_init__(self) -> None:
        if self.numerator <= 0:
            raise ValueError(
                f"Time signature numerator must be positive, got "
                f"{self.numerator}"
            )
        if self.denominator <= 0 or (
            self.denominator & (self.denominator - 1) != 0
        ):
            raise ValueError(
                f"Time signature denominator must be a positive power of "
                f"two (1, 2, 4, 8, 16, ...), got {self.denominator}"
            )

    @property
    def beats_per_bar(self) -> float:
        return self.numerator * (4.0 / self.denominator)

    def __str__(self) -> str:
        return f"{self.numerator}/{self.denominator}"
