"""Song structure models - Song, Section, Fill, PatternVariation."""

from dataclasses import dataclass, field
from typing import Any

from midi_drums.core.models.pattern import Pattern
from midi_drums.core.value_objects.generation_parameters import (
    GenerationParameters,
)
from midi_drums.core.value_objects.time_signature import TimeSignature


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
class SongSegment:
    """A tempo/time-signature-homogeneous slice within a Section.

    Mirrors the song_creator REAPER tool's region-segment shape
    (``{bars, bpm, num, denom}``) so a Section can contain a mid-section
    tempo or meter change (e.g. an 8-bar 4/4 verse with a 2-bar 7/8 insert)
    instead of being limited to one tempo/meter for its entire span.

    ``tempo``/``time_signature`` of ``None`` means "inherit the parent
    Song's global value" - a segment only needs to specify what it
    overrides.
    """

    bars: int
    tempo: int | None = None
    time_signature: TimeSignature | None = None


@dataclass
class Section:
    """Song section (verse, chorus, etc.) with pattern and variations."""

    name: str  # "verse", "chorus", "bridge", "breakdown", "intro", "outro"
    pattern: Pattern
    bars: int = 4
    variations: list[PatternVariation] = field(default_factory=list)
    fills: list[Fill] = field(default_factory=list)
    section_parameters: dict[str, Any] = field(default_factory=dict)
    segments: list[SongSegment] = field(default_factory=list)

    def __post_init__(self):
        """Validate that segment bars (if any) account for the whole section."""
        if self.segments:
            segment_bars = sum(segment.bars for segment in self.segments)
            if segment_bars != self.bars:
                raise ValueError(
                    f"Section '{self.name}' segments sum to {segment_bars} "
                    f"bars but Section.bars is {self.bars}"
                )

    def segment_for_bar(self, bar_number: int) -> SongSegment | None:
        """Return the segment covering local ``bar_number`` (0-indexed).

        Returns None when this section has no segments - callers should
        treat that as "use the song's global tempo/time signature."
        """
        cursor = 0
        for segment in self.segments:
            if cursor <= bar_number < cursor + segment.bars:
                return segment
            cursor += segment.bars
        return None

    def effective_tempo(self, bar_number: int, song_tempo: int) -> int:
        """Resolve the tempo that applies at ``bar_number``, inheriting
        ``song_tempo`` when this section has no segments or the covering
        segment doesn't override tempo."""
        segment = self.segment_for_bar(bar_number)
        if segment is None or segment.tempo is None:
            return song_tempo
        return segment.tempo

    def effective_time_signature(
        self, bar_number: int, song_time_signature: TimeSignature
    ) -> TimeSignature:
        """Resolve the time signature that applies at ``bar_number``,
        inheriting ``song_time_signature`` when this section has no
        segments or the covering segment doesn't override it."""
        segment = self.segment_for_bar(bar_number)
        if segment is None or segment.time_signature is None:
            return song_time_signature
        return segment.time_signature

    def resolved_bar_specs(
        self, song_tempo: int, song_time_signature: TimeSignature
    ) -> list[tuple[int, int, TimeSignature]]:
        """Return (bars, tempo, time_signature) triples for this section.

        One triple per segment when this section has segments, resolving
        each segment's ``tempo``/``time_signature`` override against the
        given song-level defaults; otherwise a single triple for the
        whole section using those defaults directly. Shared by every
        caller that needs to walk a section's bars accounting for
        per-segment overrides (duration, timeline export, song-map
        export) so segment-resolution semantics live in one place.
        """
        if self.segments:
            return [
                (
                    segment.bars,
                    segment.tempo or song_tempo,
                    segment.time_signature or song_time_signature,
                )
                for segment in self.segments
            ]
        return [(self.bars, song_tempo, song_time_signature)]

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
        """Calculate total song duration in seconds.

        Accounts for per-segment tempo/time-signature overrides (see
        SongSegment) - a section with no segments contributes
        ``bars * time_signature.beats_per_bar / (tempo / 60)`` using the
        song's global values, identical to the pre-segment calculation.
        """
        total_seconds = 0.0
        for section in self.sections:
            for bars, tempo, time_sig in section.resolved_bar_specs(
                self.tempo, self.time_signature
            ):
                beats = bars * time_sig.beats_per_bar
                total_seconds += beats / (tempo / 60.0)
        return total_seconds

    def section_start_times(self) -> list[float]:
        """Return each section's start time in seconds.

        Resolves per-segment tempo/time-signature overrides (see
        SongSegment) the same way :meth:`total_duration_seconds` does, so
        callers that need per-section positions (e.g. REAPER markers)
        stay in sync with segmented songs instead of assuming a single
        global tempo/time signature for the whole song.
        """
        times = []
        elapsed = 0.0
        for section in self.sections:
            times.append(elapsed)
            for bars, tempo, time_sig in section.resolved_bar_specs(
                self.tempo, self.time_signature
            ):
                beats = bars * time_sig.beats_per_bar
                elapsed += beats / (tempo / 60.0)
        return times

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
