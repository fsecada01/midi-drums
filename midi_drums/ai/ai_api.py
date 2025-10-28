"""Unified AI API for MIDI Drums Generator.

This module provides a high-level, unified interface for AI-powered drum
generation using both Pydantic AI (type-safe) and Langchain (agent-based)
approaches.
"""

import asyncio
from pathlib import Path

from midi_drums.ai.agents.pattern_agent_v2 import PatternCompositionAgentV2
from midi_drums.ai.backends import AIBackendConfig
from midi_drums.ai.pattern_generator import PydanticPatternGenerator
from midi_drums.ai.schemas import (
    PatternGenerationRequest,
    PatternGenerationResponse,
)
from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Song


class DrumGeneratorAI:
    """Unified AI interface for intelligent drum generation.

    This class provides both type-safe (Pydantic AI) and agent-based
    (Langchain) approaches to AI-powered drum pattern and song generation.

    Backend configuration is flexible via environment variables:
        AI_PROVIDER: anthropic (default), openai, groq, cohere
        AI_MODEL: Model identifier (defaults per provider)
        ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.: Provider API keys

    Examples:
        # Type-safe pattern generation (uses env vars)
        >>> ai = DrumGeneratorAI()
        >>> pattern, response = await ai.generate_pattern_from_text(
        ...     "aggressive metal breakdown with double bass"
        ... )

        # Custom backend configuration
        >>> config = AIBackendConfig(provider="openai", model="gpt-4o")
        >>> ai = DrumGeneratorAI(backend_config=config)

        # Agent-based composition
        >>> result = ai.compose_with_agent(
        ...     "create a progressive rock song with bonham style"
        ... )

        # Export to MIDI
        >>> ai.export_pattern(pattern, "breakdown.mid", tempo=180)
    """

    def __init__(
        self,
        api_key: str | None = None,
        backend_config: AIBackendConfig | None = None,
    ):
        """Initialize the AI drum generator.

        Args:
            api_key: Optional API key (deprecated, use backend_config or env vars)
            backend_config: AI backend configuration. If None, uses env vars.
        """
        # Handle legacy api_key parameter
        if api_key and not backend_config:
            backend_config = AIBackendConfig(api_key=api_key)

        self.backend_config = backend_config

        # Initialize AI approaches (lazy-loaded)
        self._pydantic_gen: PydanticPatternGenerator | None = None
        self._agent: PatternCompositionAgentV2 | None = None

    @property
    def pydantic_generator(self) -> PydanticPatternGenerator:
        """Lazy-load Pydantic AI pattern generator."""
        if self._pydantic_gen is None:
            self._pydantic_gen = PydanticPatternGenerator(
                backend_config=self.backend_config
            )
        return self._pydantic_gen

    @property
    def agent(self) -> PatternCompositionAgentV2:
        """Lazy-load Langchain composition agent (V2)."""
        if self._agent is None:
            self._agent = PatternCompositionAgentV2(
                backend_config=self.backend_config
            )
        return self._agent

    async def generate_pattern_from_text(
        self,
        description: str,
        section: str = "verse",
        tempo: int = 120,
        bars: int = 4,
        complexity: float = 0.5,
        drummer_style: str | None = None,
    ) -> tuple[Pattern, PatternGenerationResponse]:
        """Generate drum pattern from natural language using Pydantic AI.

        This method uses type-safe Pydantic AI to analyze the description
        and generate a validated, structured pattern.

        Args:
            description: Natural language pattern description
            section: Song section (verse, chorus, etc.)
            tempo: Tempo in BPM
            bars: Number of bars
            complexity: Pattern complexity (0.0-1.0)
            drummer_style: Optional drummer style to apply

        Returns:
            Tuple of (Pattern, PatternGenerationResponse with metadata)

        Example:
            >>> ai = DrumGeneratorAI()
            >>> pattern, info = await ai.generate_pattern_from_text(
            ...     "funky groove with ghost notes and syncopation",
            ...     tempo=110,
            ...     bars=4
            ... )
            >>> print(f"Genre: {info.characteristics.genre}")
            >>> print(f"Confidence: {info.confidence}")
        """
        request = PatternGenerationRequest(
            description=description,
            section=section,
            tempo=tempo,
            bars=bars,
            complexity=complexity,
            drummer_style=drummer_style,
        )

        return await self.pydantic_generator.generate_pattern_async(request)

    def generate_pattern_from_text_sync(
        self,
        description: str,
        section: str = "verse",
        tempo: int = 120,
        bars: int = 4,
        complexity: float = 0.5,
        drummer_style: str | None = None,
    ) -> tuple[Pattern, PatternGenerationResponse]:
        """Synchronous version of generate_pattern_from_text.

        Uses asyncio.run() to provide a sync interface to async generation.

        Args:
            description: Natural language pattern description
            section: Song section (verse, chorus, etc.)
            tempo: Tempo in BPM
            bars: Number of bars
            complexity: Pattern complexity (0.0-1.0)
            drummer_style: Optional drummer style to apply

        Returns:
            Tuple of (Pattern, PatternGenerationResponse with metadata)
        """
        return asyncio.run(
            self.generate_pattern_from_text(
                description, section, tempo, bars, complexity, drummer_style
            )
        )

    def compose_with_agent(self, request: str) -> dict:
        """Compose patterns or songs using intelligent Langchain agent.

        This method uses a Langchain agent that can reason about musical
        structure, chain multiple operations, and provide creative suggestions.

        The agent has access to tools for:
        - Generating patterns in any genre/style
        - Applying drummer styles
        - Creating complete multi-section songs
        - Listing available options

        Args:
            request: Natural language composition request

        Returns:
            Dictionary with agent response and any generated IDs

        Examples:
            >>> ai = DrumGeneratorAI()
            >>> result = ai.compose_with_agent(
            ...     "create a death metal song with intro, verses, and "
            ...     "breakdown"
            ... )
            >>> print(result['output'])

            >>> result = ai.compose_with_agent(
            ...     "make an aggressive breakdown and then apply bonham style"
            ... )
        """
        return self.agent.compose(request)

    def export_pattern(
        self,
        pattern: Pattern | str,
        output_path: str | Path,
        tempo: int = 120,
    ) -> bool:
        """Export pattern to MIDI file.

        Args:
            pattern: Pattern object or pattern ID from agent
            output_path: Path for MIDI output
            tempo: Tempo in BPM

        Returns:
            True if successful, False otherwise

        Example:
            >>> ai = DrumGeneratorAI()
            >>> pattern, _ = await ai.generate_pattern_from_text("heavy metal")
            >>> ai.export_pattern(pattern, "metal.mid", tempo=155)
        """
        output_path = str(output_path)

        # Handle pattern ID from agent
        if isinstance(pattern, str):
            return self.agent.export_pattern(pattern, output_path, tempo)

        # Handle Pattern object from Pydantic generator
        from midi_drums.engines.midi_engine import MIDIEngine

        engine = MIDIEngine()
        engine.pattern_to_midi(pattern, output_path, tempo)
        return True

    def export_song(self, song: Song | str, output_path: str | Path) -> bool:
        """Export song to MIDI file.

        Args:
            song: Song object or song ID from agent
            output_path: Path for MIDI output

        Returns:
            True if successful, False otherwise

        Example:
            >>> ai = DrumGeneratorAI()
            >>> result = ai.compose_with_agent("create a metal song")
            >>> # Extract song_id from result['output']
            >>> ai.export_song("metal_death_song_0", "song.mid")
        """
        output_path = str(output_path)

        # Handle song ID from agent
        if isinstance(song, str):
            return self.agent.export_song(song, output_path)

        # Handle Song object
        from midi_drums.engines.midi_engine import MIDIEngine

        engine = MIDIEngine()
        engine.song_to_midi(song, output_path)
        return True

    def get_pattern_from_agent(self, pattern_id: str) -> Pattern | None:
        """Retrieve pattern generated by agent.

        Args:
            pattern_id: Pattern ID from agent response

        Returns:
            Pattern object or None

        Example:
            >>> result = ai.compose_with_agent("create metal breakdown")
            >>> # Extract pattern_id from result['output']
            >>> pattern = ai.get_pattern_from_agent("metal_death_breakdown_0")
        """
        return self.agent.get_pattern(pattern_id)

    def get_song_from_agent(self, song_id: str) -> Song | None:
        """Retrieve song generated by agent.

        Args:
            song_id: Song ID from agent response

        Returns:
            Song object or None
        """
        return self.agent.get_song(song_id)

    # Convenience methods for common use cases

    async def quick_pattern(
        self, description: str, output_path: str | None = None
    ) -> Pattern:
        """Quick pattern generation with optional MIDI export.

        Args:
            description: Natural language pattern description
            output_path: Optional path for immediate MIDI export

        Returns:
            Generated Pattern object

        Example:
            >>> ai = DrumGeneratorAI()
            >>> pattern = await ai.quick_pattern(
            ...     "aggressive blast beat",
            ...     "blast.mid"
            ... )
        """
        pattern, _ = await self.generate_pattern_from_text(description)

        if output_path:
            self.export_pattern(pattern, output_path)

        return pattern

    def quick_song(
        self, description: str, output_path: str | None = None
    ) -> str:
        """Quick song composition with optional MIDI export.

        Args:
            description: Natural language song description
            output_path: Optional path for immediate MIDI export

        Returns:
            Song ID for reference

        Example:
            >>> ai = DrumGeneratorAI()
            >>> song_id = ai.quick_song(
            ...     "progressive rock song with bonham style",
            ...     "prog_rock.mid"
            ... )
        """
        result = self.compose_with_agent(
            f"Create a song: {description}. "
            "Use appropriate structure and sections."
        )

        # Extract song ID from response (simple parsing)
        output = result.get("output", "")
        # Look for "song_id" or "ID:" patterns
        import re

        match = re.search(r"ID:\s*(\w+)", output)
        if match:
            song_id = match.group(1)
            if output_path:
                self.export_song(song_id, output_path)
            return song_id

        return output

    def __repr__(self) -> str:
        """String representation."""
        return (
            "DrumGeneratorAI(pydantic=PydanticPatternGenerator, "
            "agent=PatternCompositionAgent)"
        )
