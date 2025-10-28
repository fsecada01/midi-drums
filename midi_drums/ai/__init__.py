"""AI integration for MIDI Drums Generator.

This module provides AI-powered features including:
- Natural language pattern generation
- Intelligent pattern evolution
- Adaptive song composition
- Audio-to-MIDI pattern analysis

Architecture:
- Pydantic AI: Type-safe structured outputs and validation
- Langchain: Agent-based composition and NL processing
- Backend Abstraction: Support for multiple AI providers via env vars

Backend Configuration (Environment Variables):
    AI_PROVIDER: anthropic (default), openai, groq, cohere
    AI_MODEL: Model identifier (auto-detected per provider)
    ANTHROPIC_API_KEY: Anthropic API key
    OPENAI_API_KEY: OpenAI API key
    GROQ_API_KEY: Groq API key
    COHERE_API_KEY: Cohere API key

Quick Start:
    >>> from midi_drums.ai import DrumGeneratorAI, AIBackendConfig
    >>>
    >>> # Use environment variables (recommended)
    >>> ai = DrumGeneratorAI()
    >>>
    >>> # Or configure programmatically
    >>> config = AIBackendConfig(provider="openai", model="gpt-4o")
    >>> ai = DrumGeneratorAI(backend_config=config)
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

from midi_drums.ai.agents.pattern_agent_v2 import PatternCompositionAgentV2
from midi_drums.ai.ai_api import DrumGeneratorAI
from midi_drums.ai.backends import AIBackendConfig, AIBackendFactory, AIProvider
from midi_drums.ai.pattern_generator import PydanticPatternGenerator
from midi_drums.ai.schemas import (
    PatternGenerationRequest,
    PatternGenerationResponse,
    SongCompositionRequest,
)

# Alias for backwards compatibility
PatternCompositionAgent = PatternCompositionAgentV2

__all__ = [
    "DrumGeneratorAI",
    "PatternCompositionAgent",
    "PatternCompositionAgentV2",
    "PydanticPatternGenerator",
    "PatternGenerationRequest",
    "PatternGenerationResponse",
    "SongCompositionRequest",
    "AIBackendConfig",
    "AIBackendFactory",
    "AIProvider",
]
