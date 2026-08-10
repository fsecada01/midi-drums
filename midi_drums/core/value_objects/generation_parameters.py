"""Generation parameters value object."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GenerationParameters:
    """Parameters controlling pattern generation."""

    genre: str
    style: str = "default"
    drummer: str | None = None
    complexity: float = 0.5  # 0.0-1.0, affects fill density and variation
    dynamics: float = 0.5  # 0.0-1.0, affects volume variation
    humanization: float = 0.3  # 0.0-1.0, affects timing/velocity variation
    fill_frequency: float = 0.2  # 0.0-1.0, how often fills occur
    swing_ratio: float = 0.0  # 0.0-1.0, swing feel
    ride_threshold: float = 0.9  # 0.0-1.0, complexity above which a
    # section switches from hi-hat to ride cymbal timekeeping regardless
    # of section name. High by default so section name (chorus/bridge)
    # stays the primary trigger; existing patterns commonly run
    # complexity 0.7-0.8 for busy-but-still-hihat verses, so this only
    # fires as a deliberate high-complexity override.

    # Genre context adaptation (NEW)
    song_genre_context: str | None = None  # Overall song genre for adaptation
    context_blend: float = 0.0  # 0.0-1.0, how much to blend with context

    custom_parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate parameters."""
        for param_name, value in [
            ("complexity", self.complexity),
            ("dynamics", self.dynamics),
            ("humanization", self.humanization),
            ("fill_frequency", self.fill_frequency),
            ("swing_ratio", self.swing_ratio),
            ("ride_threshold", self.ride_threshold),
            ("context_blend", self.context_blend),
        ]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{param_name} must be between 0.0 and 1.0, got {value}"
                )
