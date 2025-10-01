"""Song structure and generation parameter models."""

from dataclasses import dataclass, field
from typing import Any

from midi_drums.models.pattern import Pattern, TimeSignature


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
            ("context_blend", self.context_blend),
        ]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{param_name} must be between 0.0 and 1.0, got {value}"
                )


@dataclass
class Fill:
    """A drum fill pattern."""

    pattern: Pattern
    trigger_probability: float = 1.0  # Probability this fill will be used
    section_position: str = "end"  # "start", "middle", "end"


@dataclass
class PatternVariation:
    """Variation of a base pattern."""

    pattern: Pattern
    probability: float = (
        0.3  # Chance this variation will be used instead of base
    )
    bars: list[int] | None = (
        None  # Specific bars to apply variation, None = any
    )


@dataclass
class Section:
    """Song section (verse, chorus, etc.) with pattern and variations."""

    name: str  # "verse", "chorus", "bridge", "breakdown", "intro", "outro"
    pattern: Pattern
    bars: int = 4
    variations: list[PatternVariation] = field(default_factory=list)
    fills: list[Fill] = field(default_factory=list)
    section_parameters: dict[str, Any] = field(default_factory=dict)

    def get_effective_pattern(self, bar_number: int) -> Pattern:
        """Get the pattern for a specific bar, considering variations."""
        # Check if any variations should apply to this bar
        for variation in self.variations:
            if variation.bars is None or bar_number in variation.bars:
                import random

                if random.random() < variation.probability:
                    return variation.pattern
        return self.pattern

    def should_add_fill(
        self, bar_number: int, fill_frequency: float
    ) -> Fill | None:
        """Determine if a fill should be added at this bar."""
        import random

        if random.random() < fill_frequency and self.fills:
            # Choose fill based on probabilities
            total_prob = sum(fill.trigger_probability for fill in self.fills)
            if total_prob > 0:
                rand_val = random.random() * total_prob
                current_sum = 0
                for fill in self.fills:
                    current_sum += fill.trigger_probability
                    if rand_val <= current_sum:
                        return fill
        return None


@dataclass
class Song:
    """Complete song structure with sections and global parameters."""

    name: str
    tempo: int = 120  # BPM
    time_signature: TimeSignature = field(default_factory=TimeSignature)
    sections: list[Section] = field(default_factory=list)
    global_parameters: GenerationParameters | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate song parameters."""
        if not 60 <= self.tempo <= 300:
            raise ValueError(
                f"Tempo must be between 60-300 BPM, got {self.tempo}"
            )

    def add_section(self, section: Section) -> "Song":
        """Add a section to the song."""
        self.sections.append(section)
        return self

    def total_bars(self) -> int:
        """Calculate total number of bars in the song."""
        return sum(section.bars for section in self.sections)

    def total_duration_seconds(self) -> float:
        """Calculate total song duration in seconds."""
        total_beats = self.total_bars() * self.time_signature.beats_per_bar
        beats_per_second = self.tempo / 60.0
        return total_beats / beats_per_second

    def get_section_by_name(self, name: str) -> Section | None:
        """Find first section with the given name."""
        for section in self.sections:
            if section.name == name:
                return section
        return None

    def get_sections_by_name(self, name: str) -> list[Section]:
        """Find all sections with the given name."""
        return [section for section in self.sections if section.name == name]

    @classmethod
    def create_simple_structure(
        cls,
        name: str,
        tempo: int = 120,
        genre: str = "rock",
        style: str = "default",
    ) -> "Song":
        """Create a song with basic verse-chorus structure."""
        from midi_drums.models.pattern import (
            Pattern,  # Import here to avoid circular imports
        )

        # Create placeholder patterns (will be generated by plugins)
        verse_pattern = Pattern(f"{genre}_{style}_verse")
        chorus_pattern = Pattern(f"{genre}_{style}_chorus")

        song = cls(name=name, tempo=tempo)
        song.global_parameters = GenerationParameters(genre=genre, style=style)

        # Standard pop/rock structure
        song.add_section(Section("intro", verse_pattern, bars=4))
        song.add_section(Section("verse", verse_pattern, bars=8))
        song.add_section(Section("chorus", chorus_pattern, bars=8))
        song.add_section(Section("verse", verse_pattern, bars=8))
        song.add_section(Section("chorus", chorus_pattern, bars=8))
        song.add_section(Section("bridge", verse_pattern, bars=4))
        song.add_section(Section("chorus", chorus_pattern, bars=8))
        song.add_section(Section("outro", chorus_pattern, bars=4))

        return song
