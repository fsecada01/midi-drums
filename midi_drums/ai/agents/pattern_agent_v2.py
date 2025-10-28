"""Langchain agent for intelligent pattern composition (Langchain 1.0 compatible).

This agent uses Langchain 1.0's create_agent function with tools for drum
pattern generation, composition, and evolution.
"""

from typing import Any

from langchain.agents import create_agent
from loguru import logger

from midi_drums.ai.backends import AIBackendConfig, AIBackendFactory
from midi_drums.core.engine import DrumGenerator
from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Song


class PatternCompositionAgentV2:
    """Langchain 1.0 agent for intelligent drum pattern composition.

    This class uses Langchain's create_agent function with a set of tools
    for generating patterns, applying drummer styles, and creating songs.

    Features:
    - Multi-step reasoning about musical composition
    - Tool-based pattern generation and manipulation
    - Support for all genres, styles, and drummers
    - Caching of generated patterns and songs
    """

    def __init__(
        self,
        api_key: str | None = None,
        backend_config: AIBackendConfig | None = None,
    ):
        """Initialize the pattern composition agent.

        Args:
            api_key: Optional API key (deprecated, use backend_config or env vars)
            backend_config: AI backend configuration. If None, uses env vars.
        """
        logger.info("Initializing Langchain Pattern Composition Agent V2")

        # Handle legacy api_key parameter
        if api_key and not backend_config:
            logger.warning(
                "api_key parameter is deprecated. Use backend_config or env vars."
            )
            backend_config = AIBackendConfig(api_key=api_key)

        # Get backend config
        self.backend_config = backend_config or AIBackendConfig.from_env()

        # Initialize LLM using backend factory (returns init_chat_model result)
        self.llm = AIBackendFactory.create_langchain_llm(self.backend_config)

        # Initialize drum generator
        self.drum_generator = DrumGenerator()

        # Pattern storage for reference across agent calls
        self.pattern_cache: dict[str, Pattern] = {}
        self.song_cache: dict[str, Song] = {}
        logger.debug("Pattern and song caches initialized")

        # Create tools
        self.tools = self._create_tools()
        logger.info(f"Agent tools created: {len(self.tools)} tools available")

        # Create agent using Langchain 1.0 create_agent
        self.agent = self._create_agent()
        logger.success("Langchain Pattern Composition Agent V2 ready")

    def _create_tools(self) -> list:
        """Create Langchain tools for drum generation.

        Returns:
            List of tools the agent can use
        """
        from langchain.tools import tool

        @tool
        def generate_pattern(
            genre: str, style: str, section: str, bars: int = 4
        ) -> str:
            """Generate a drum pattern with specified characteristics.

            Args:
                genre: Musical genre (metal, rock, jazz, funk)
                style: Specific style within genre
                section: Song section type (verse, chorus, bridge, breakdown, etc.)
                bars: Number of bars in pattern (1-16)

            Returns:
                Description of generated pattern with ID for reference
            """
            logger.info(
                f"Tool: generate_pattern({genre}/{style}/{section}, {bars} bars)"
            )

            pattern = self.drum_generator.generate_pattern(
                genre=genre, section=section, style=style, bars=bars
            )

            if not pattern:
                return (
                    f"Failed to generate {genre}/{style} pattern for {section}"
                )

            # Cache the pattern
            pattern_id = f"pattern_{len(self.pattern_cache)}"
            self.pattern_cache[pattern_id] = pattern

            logger.success(
                f"Generated pattern: {pattern_id} ({len(pattern.beats)} beats)"
            )

            return (
                f"Generated {genre}/{style} {section} pattern "
                f"(ID: {pattern_id}, {len(pattern.beats)} beats, {bars} bars). "
                f"Use this ID to reference or apply drummer styles."
            )

        @tool
        def apply_drummer_style(pattern_id: str, drummer: str) -> str:
            """Apply a drummer's signature style to an existing pattern.

            Args:
                pattern_id: ID of pattern to modify (from generate_pattern)
                drummer: Drummer style (bonham, porcaro, weckl, chambers, roeder, dee, hoglan)

            Returns:
                Description of styled pattern with new ID
            """
            logger.info(f"Tool: apply_drummer_style({pattern_id}, {drummer})")

            if pattern_id not in self.pattern_cache:
                return (
                    f"Pattern {pattern_id} not found. Generate a pattern first."
                )

            original_pattern = self.pattern_cache[pattern_id]
            styled_pattern = self.drum_generator.apply_drummer_style(
                original_pattern, drummer
            )

            if not styled_pattern:
                return f"Failed to apply {drummer} style (drummer not found)"

            # Cache the styled pattern
            styled_id = f"{pattern_id}_{drummer}"
            self.pattern_cache[styled_id] = styled_pattern

            logger.success(f"Applied {drummer} style: {styled_id}")

            return (
                f"Applied {drummer} style to {pattern_id} "
                f"(New ID: {styled_id}). "
                f"Pattern now has {drummer}'s signature characteristics."
            )

        @tool
        def create_song(
            genre: str, style: str, tempo: int = 120, structure: str = "default"
        ) -> str:
            """Create a complete multi-section song.

            Args:
                genre: Primary genre
                style: Primary style
                tempo: Tempo in BPM (40-300)
                structure: Song structure description or "default"

            Returns:
                Description of created song with ID
            """
            logger.info(
                f"Tool: create_song({genre}/{style}, {tempo} BPM, {structure})"
            )

            song = self.drum_generator.create_song(
                genre=genre,
                style=style,
                tempo=tempo,
                # Use default structure for now (could parse structure string)
            )

            # Cache the song
            song_id = f"song_{len(self.song_cache)}"
            self.song_cache[song_id] = song

            logger.success(
                f"Created song: {song_id} ({len(song.sections)} sections, {tempo} BPM)"
            )

            section_desc = ", ".join(
                f"{s.type}({s.bars})" for s in song.sections[:5]
            )
            if len(song.sections) > 5:
                section_desc += f", +{len(song.sections) - 5} more"

            return (
                f"Created {genre}/{style} song at {tempo} BPM "
                f"(ID: {song_id}, {len(song.sections)} sections: {section_desc}). "
                f"Use this ID to export to MIDI."
            )

        @tool
        def list_genres() -> str:
            """List all available genres.

            Returns:
                Comma-separated list of genres
            """
            genres = self.drum_generator.get_available_genres()
            return f"Available genres: {', '.join(genres)}"

        @tool
        def list_drummers() -> str:
            """List all available drummer styles.

            Returns:
                Comma-separated list of drummers with descriptions
            """
            drummers = self.drum_generator.get_available_drummers()
            return (
                f"Available drummers: {', '.join(drummers)}. "
                f"Each has unique signature characteristics."
            )

        return [
            generate_pattern,
            apply_drummer_style,
            create_song,
            list_genres,
            list_drummers,
        ]

    def _create_agent(self):
        """Create Langchain 1.0 agent using create_agent.

        Returns:
            Configured agent
        """
        logger.debug("Creating agent with create_agent()")

        # Use Langchain 1.0 create_agent
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=(
                "You are an expert drum pattern composer and music producer. "
                "You help users create professional drum patterns and songs across "
                "multiple genres (metal, rock, jazz, funk) with various styles and "
                "drummer personalities.\n\n"
                "When composing:\n"
                "1. Ask clarifying questions if the request is vague\n"
                "2. Suggest appropriate styles and drummers based on the user's goals\n"
                "3. Explain your creative decisions\n"
                "4. Reference generated pattern/song IDs for the user\n\n"
                "Available tools allow you to generate patterns, apply drummer styles, "
                "create complete songs, and list available options."
            ),
        )

        logger.debug("Agent created successfully")
        return agent

    def compose(self, user_request: str) -> dict[str, Any]:
        """Process a user composition request using the agent.

        Args:
            user_request: Natural language composition request

        Returns:
            Dictionary with agent response and metadata
        """
        logger.info(f"Agent request: '{user_request[:60]}...'")
        logger.debug(
            f"Cache state: {len(self.pattern_cache)} patterns, "
            f"{len(self.song_cache)} songs"
        )

        # Invoke agent with messages
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": user_request}]}
        )

        logger.success("Agent composition complete")

        # Extract final response
        final_response = ""
        if "messages" in result:
            # Get last message
            last_message = result["messages"][-1]
            final_response = (
                last_message.content
                if hasattr(last_message, "content")
                else str(last_message)
            )

        return {
            "output": final_response,
            "pattern_cache": list(self.pattern_cache.keys()),
            "song_cache": list(self.song_cache.keys()),
        }

    def get_pattern(self, pattern_id: str) -> Pattern | None:
        """Retrieve cached pattern by ID.

        Args:
            pattern_id: Pattern identifier from agent

        Returns:
            Pattern if found, None otherwise
        """
        return self.pattern_cache.get(pattern_id)

    def get_song(self, song_id: str) -> Song | None:
        """Retrieve cached song by ID.

        Args:
            song_id: Song identifier from agent

        Returns:
            Song if found, None otherwise
        """
        return self.song_cache.get(song_id)
