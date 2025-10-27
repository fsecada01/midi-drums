"""AI integration for MIDI Drums Generator.

This module provides AI-powered features including:
- Natural language pattern generation
- Intelligent pattern evolution
- Adaptive song composition
- Audio-to-MIDI pattern analysis

Architecture:
- Pydantic AI: Type-safe structured outputs and validation
- Langchain: Agent-based composition and NL processing

Quick Start:
    >>> from midi_drums.ai import DrumGeneratorAI
    >>> ai = DrumGeneratorAI(api_key="your-anthropic-key")
    >>>
    >>> # Type-safe pattern generation
    >>> pattern, info = await ai.generate_pattern_from_text(
    ...     "aggressive metal breakdown with double bass"
    ... )
    >>>
    >>> # Agent-based composition
    >>> result = ai.compose_with_agent(
    ...     "create a progressive rock song with bonham style"
    ... )
    >>>
    >>> # Export to MIDI
    >>> ai.export_pattern(pattern, "breakdown.mid", tempo=180)
"""

from midi_drums.ai.agents.pattern_agent import PatternCompositionAgent
from midi_drums.ai.ai_api import DrumGeneratorAI
from midi_drums.ai.pattern_generator import PydanticPatternGenerator
from midi_drums.ai.schemas import (
    PatternGenerationRequest,
    PatternGenerationResponse,
    SongCompositionRequest,
)

__all__ = [
    "DrumGeneratorAI",
    "PatternCompositionAgent",
    "PydanticPatternGenerator",
    "PatternGenerationRequest",
    "PatternGenerationResponse",
    "SongCompositionRequest",
]
