"""Generation parameters value object."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from midi_drums.core.value_objects.riff_accent import RiffAccentMap


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

    # Riff-lock (audio riff -> kick-locked drum pattern, see
    # midi_drums.modifications.riff_lock.RiffLockTransform). Applies to a
    # single generate_pattern() call for exactly one bar - passing this
    # through create_song()'s **kwargs would apply the same one-bar lock to
    # every section, which is not what create_song callers want, so callers
    # that need riff-lock must call generate_pattern() directly per section
    # (see midi_drums.api.cli's `riff` subcommand).
    riff_accents: "RiffAccentMap | None" = None
    riff_lock_strength: float = 1.0  # 0.0-1.0, blend toward riff accents

    # Snare reaction to the same riff accents (see
    # midi_drums.modifications.snare_accent_reaction.SnareAccentReaction).
    # Applied after riff-lock, same single-generate_pattern()-call scope as
    # riff_accents above. "off" means the pipeline hook never constructs
    # SnareAccentReaction at all.
    riff_snare_mode: Literal["off", "reinforce", "stab"] = "off"
    riff_snare_stab_threshold: float = 0.85

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
            ("riff_lock_strength", self.riff_lock_strength),
            ("riff_snare_stab_threshold", self.riff_snare_stab_threshold),
        ]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{param_name} must be between 0.0 and 1.0, got {value}"
                )
