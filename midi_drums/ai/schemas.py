"""Pydantic AI schemas for type-safe pattern generation and validation.

These schemas ensure AI-generated outputs are structured, validated, and
compatible with the existing MIDI Drums Generator architecture.
"""

from typing import Literal

from pydantic import BaseModel, Field


class PatternGenerationRequest(BaseModel):
    """Request schema for natural language pattern generation.

    Examples:
        "create an aggressive metal breakdown with double bass"
        "jazz swing pattern in the style of Dave Weckl"
        "funky groove with ghost notes and syncopation"
    """

    description: str = Field(
        ...,
        description="Natural language description of desired pattern",
        min_length=5,
        max_length=500,
    )

    section: Literal[
        "verse", "chorus", "bridge", "breakdown", "intro", "outro", "fill"
    ] = Field(
        default="verse",
        description="Song section for the pattern",
    )

    tempo: int = Field(
        default=120,
        ge=40,
        le=300,
        description="Tempo in BPM",
    )

    bars: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Number of bars in the pattern",
    )

    complexity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Pattern complexity (0=simple, 1=complex)",
    )

    drummer_style: str | None = Field(
        default=None,
        description="Optional drummer style to apply (bonham, porcaro, etc.)",
    )


class PatternCharacteristics(BaseModel):
    """AI-inferred characteristics of a pattern from description."""

    genre: Literal["metal", "rock", "jazz", "funk", "electronic"] = Field(
        ...,
        description="Inferred musical genre",
    )

    style: str = Field(
        ...,
        description="Specific style within genre (e.g., 'death', 'swing')",
    )

    intensity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Pattern intensity/aggression level",
    )

    use_double_bass: bool = Field(
        default=False,
        description="Whether to use double bass pedal patterns",
    )

    use_ghost_notes: bool = Field(
        default=False,
        description="Whether to incorporate ghost notes",
    )

    use_syncopation: bool = Field(
        default=False,
        description="Whether to use syncopated rhythms",
    )

    primary_cymbal: Literal["hihat", "ride", "crash"] = Field(
        default="hihat",
        description="Primary cymbal to use",
    )

    reasoning: str = Field(
        ...,
        description="AI's reasoning for these characteristics",
        max_length=500,
    )


class PatternGenerationResponse(BaseModel):
    """Response schema for pattern generation with metadata."""

    pattern_name: str = Field(
        ...,
        description="Generated pattern name",
    )

    characteristics: PatternCharacteristics = Field(
        ...,
        description="AI-inferred pattern characteristics",
    )

    templates_used: list[str] = Field(
        default_factory=list,
        description="Pattern templates used in generation",
    )

    modifications_applied: list[str] = Field(
        default_factory=list,
        description="Drummer modifications applied",
    )

    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="AI confidence in pattern generation",
    )

    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggestions for alternative patterns or improvements",
    )


class SongStructureSection(BaseModel):
    """Single section in a song structure."""

    section_type: Literal[
        "verse", "chorus", "bridge", "breakdown", "intro", "outro"
    ]
    bars: int = Field(ge=1, le=32)
    style: str | None = None
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)


class SongCompositionRequest(BaseModel):
    """Request schema for AI-driven song composition.

    Examples:
        "compose a progressive metal song with dynamic sections"
        "create a jazz fusion piece with complex time signatures"
        "build an energetic punk rock track"
    """

    description: str = Field(
        ...,
        description="Natural language description of desired song",
        min_length=10,
        max_length=1000,
    )

    target_duration_seconds: int | None = Field(
        default=None,
        ge=30,
        le=600,
        description="Target song duration in seconds (optional)",
    )

    tempo: int = Field(
        default=120,
        ge=40,
        le=300,
        description="Base tempo in BPM",
    )

    complexity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Overall song complexity",
    )

    drummer_style: str | None = Field(
        default=None,
        description="Optional drummer style for entire song",
    )

    allow_tempo_changes: bool = Field(
        default=False,
        description="Allow tempo changes between sections",
    )


class SongCompositionResponse(BaseModel):
    """Response schema for AI song composition."""

    song_title: str = Field(
        ...,
        description="AI-generated song title",
    )

    genre: str = Field(
        ...,
        description="Primary genre",
    )

    structure: list[SongStructureSection] = Field(
        ...,
        description="Complete song structure with sections",
    )

    total_bars: int = Field(
        ...,
        description="Total number of bars in composition",
    )

    estimated_duration_seconds: float = Field(
        ...,
        description="Estimated duration based on tempo and structure",
    )

    creative_notes: str = Field(
        ...,
        description="AI's creative notes and composition rationale",
        max_length=1000,
    )

    alternative_structures: list[str] = Field(
        default_factory=list,
        description="Suggested alternative arrangements",
    )


class AudioAnalysisRequest(BaseModel):
    """Request schema for audio-to-MIDI pattern analysis."""

    audio_file_path: str = Field(
        ...,
        description="Path to WAV/MP3 audio file",
    )

    target_section: Literal[
        "verse", "chorus", "bridge", "breakdown", "intro", "outro"
    ] = Field(
        default="verse",
        description="What section type this audio represents",
    )

    genre_hint: str | None = Field(
        default=None,
        description="Optional genre hint to guide analysis",
    )

    extract_tempo: bool = Field(
        default=True,
        description="Whether to extract tempo from audio",
    )


class AudioAnalysisResponse(BaseModel):
    """Response schema for audio analysis."""

    detected_tempo: float | None = Field(
        default=None,
        description="Detected tempo in BPM",
    )

    detected_time_signature: str = Field(
        default="4/4",
        description="Detected time signature",
    )

    onset_times: list[float] = Field(
        default_factory=list,
        description="Detected onset times in seconds",
    )

    pattern_description: str = Field(
        ...,
        description="AI description of detected pattern",
        max_length=500,
    )

    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence in analysis",
    )

    recommended_templates: list[str] = Field(
        default_factory=list,
        description="Recommended pattern templates based on analysis",
    )
