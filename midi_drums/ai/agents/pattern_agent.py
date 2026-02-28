"""Langchain agent for intelligent pattern composition.

This agent uses Langchain 1.x create_agent (LangGraph-backed) with tools for
drum pattern generation, composition, and evolution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from midi_drums.ai.backends import AIBackendConfig, AIBackendFactory
from midi_drums.core.engine import DrumGenerator
from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Song

SYSTEM_PROMPT = (
    "You are an expert drum pattern composer and music producer. "
    "You generate professional drum patterns and songs across multiple genres "
    "(metal, rock, jazz, funk) with various styles and drummer personalities.\n\n"
    "IMPORTANT — this is a single-shot, non-interactive command. "
    "The user will not respond after you act. You must infer all creative "
    "decisions from the prompt alone and immediately call the appropriate tools. "
    "Do NOT ask clarifying questions. Do NOT request more information. "
    "If the prompt is ambiguous, make a reasonable creative choice and proceed.\n\n"
    "If the user wants explicit control over genre, style, tempo, or structure "
    "they should use the CLI flags directly (e.g. --genre, --style, --tempo).\n\n"
    "IMPORTANT — valid style values per genre (use EXACTLY these strings):\n"
    "  metal : heavy, death, power, progressive, thrash, doom, breakdown\n"
    "  rock  : classic, blues, alternative, progressive, punk, hard, pop\n"
    "  jazz  : swing, bebop, fusion, latin, ballad, hard_bop, contemporary\n"
    "  funk  : classic, pfunk, shuffle, new_orleans, fusion, minimal, heavy\n\n"
    "Never pass a style like 'death metal' or 'heavy metal' — use 'death' or 'heavy'.\n\n"
    "When composing a song, follow this exact workflow:\n"
    "1. Infer genre, style, tempo, and structure from the user's description\n"
    "2. Call create_song with the full section list\n"
    "3. Call generate_pattern for each distinct section type that needs a unique pattern\n"
    "4. Call apply_drummer_style to apply the appropriate drummer to each pattern\n"
    "5. Call assign_pattern_to_section for EVERY section in the song — this is mandatory.\n"
    "   Without this step the exported MIDI will be wrong.\n"
    "6. After all assignments, briefly summarise what was created and reference the IDs\n\n"
    "Available tools allow you to generate patterns, apply drummer styles, "
    "create complete songs, and list available options."
)


class PatternCompositionAgent:
    """Langchain 1.0 agent for intelligent drum pattern composition.

    This class uses Langchain's create_react_agent function with a set of
    tools for generating patterns, applying drummer styles, and creating songs.

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

        # Create agent using Langchain 1.0 create_react_agent
        self.agent = self._create_agent()
        logger.success("Langchain Pattern Composition Agent V2 ready")

    def _create_tools(self) -> list:
        """Create Langchain tools for drum generation.

        Returns:
            List of tools the agent can use
        """
        from langchain.tools import tool

        _VALID_STYLES: dict[str, list[str]] = {
            "metal": [
                "heavy",
                "death",
                "power",
                "progressive",
                "thrash",
                "doom",
                "breakdown",
            ],
            "rock": [
                "classic",
                "blues",
                "alternative",
                "progressive",
                "punk",
                "hard",
                "pop",
            ],
            "jazz": [
                "swing",
                "bebop",
                "fusion",
                "latin",
                "ballad",
                "hard_bop",
                "contemporary",
            ],
            "funk": [
                "classic",
                "pfunk",
                "shuffle",
                "new_orleans",
                "fusion",
                "minimal",
                "heavy",
            ],
        }

        def _normalize_style(genre: str, style: str) -> str:
            valid = _VALID_STYLES.get(genre.lower(), [])
            if not valid:
                return style
            normalized = style.lower().replace("-", "_").replace(" ", "_")
            if normalized in valid:
                return normalized
            # Substring match: "death_metal" → "death", "classic_rock" → "classic"
            for v in valid:
                if v in normalized or normalized in v:
                    logger.debug(
                        f"Style '{style}' normalized to '{v}' for genre '{genre}'"
                    )
                    return v
            logger.warning(
                f"Unknown style '{style}' for genre '{genre}', using '{valid[0]}'"
            )
            return valid[0]

        @tool
        def generate_pattern(
            genre: str, style: str, section: str, bars: int = 4
        ) -> str:
            """Generate a drum pattern with specified characteristics.

            Args:
                genre: Musical genre — one of: metal, rock, jazz, funk
                style: Exact style token for the genre. Valid values:
                    metal → heavy | death | power | progressive | thrash | doom | breakdown
                    rock  → classic | blues | alternative | progressive | punk | hard | pop
                    jazz  → swing | bebop | fusion | latin | ballad | hard_bop | contemporary
                    funk  → classic | pfunk | shuffle | new_orleans | fusion | minimal | heavy
                section: Song section type (verse, chorus, bridge, breakdown, etc.)
                bars: Number of bars in pattern (1-16)

            Returns:
                Description of generated pattern with ID for reference
            """
            style = _normalize_style(genre, style)
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
                genre: Primary genre — one of: metal, rock, jazz, funk
                style: Exact style token for the genre. Valid values:
                    metal → heavy | death | power | progressive | thrash | doom | breakdown
                    rock  → classic | blues | alternative | progressive | punk | hard | pop
                    jazz  → swing | bebop | fusion | latin | ballad | hard_bop | contemporary
                    funk  → classic | pfunk | shuffle | new_orleans | fusion | minimal | heavy
                tempo: Tempo in BPM (40-300)
                structure: Song structure description or "default"

            Returns:
                Description of created song with ID
            """
            style = _normalize_style(genre, style)
            logger.info(
                f"Tool: create_song({genre}/{style}, {tempo} BPM, {structure})"
            )

            # Parse structure string into (section_name, bars) tuples
            _SECTION_BARS: dict[str, int] = {
                "intro": 4,
                "verse": 8,
                "chorus": 8,
                "bridge": 4,
                "breakdown": 4,
                "outro": 4,
                "pre_chorus": 4,
                "interlude": 4,
                "hook": 4,
            }
            parsed_structure = None
            if structure and structure.lower() != "default":
                parsed_structure = []
                for part in structure.split(","):
                    name = part.strip().lower()
                    if not name:
                        continue
                    # solo_slow, solo_build, solo_midtempo → 8 bars each
                    if name.startswith("solo"):
                        bars = 8
                    else:
                        bars = _SECTION_BARS.get(name, 4)
                    parsed_structure.append((name, bars))

            song = self.drum_generator.create_song(
                genre=genre,
                style=style,
                tempo=tempo,
                **({"structure": parsed_structure} if parsed_structure else {}),
            )

            # Cache the song
            song_id = f"song_{len(self.song_cache)}"
            self.song_cache[song_id] = song

            logger.success(
                f"Created song: {song_id} ({len(song.sections)} sections, {tempo} BPM)"
            )

            section_desc = ", ".join(
                (
                    f"{s.type}({s.bars})"
                    if hasattr(s, "type")
                    else f"{s.name}({s.bars})"
                )
                for s in song.sections[:5]
            )
            if len(song.sections) > 5:
                section_desc += f", +{len(song.sections) - 5} more"

            return (
                f"Created {genre}/{style} song at {tempo} BPM "
                f"(ID: {song_id}, {len(song.sections)} sections: {section_desc}). "
                f"Use this ID to export to MIDI."
            )

        @tool
        def assign_pattern_to_section(
            song_id: str, section_index: int, pattern_id: str
        ) -> str:
            """Assign a generated pattern to a specific section of a song.

            IMPORTANT: Always call this for every section after generating patterns
            so the exported MIDI reflects the correct drummer styles and patterns.

            Args:
                song_id: Song ID from create_song (e.g. "song_0")
                section_index: 0-based index of the section to replace
                pattern_id: Pattern ID from generate_pattern or apply_drummer_style

            Returns:
                Confirmation of the assignment
            """
            if song_id not in self.song_cache:
                return f"Song {song_id} not found. Create a song first."
            if pattern_id not in self.pattern_cache:
                return (
                    f"Pattern {pattern_id} not found. Generate a pattern first."
                )

            song = self.song_cache[song_id]
            if section_index < 0 or section_index >= len(song.sections):
                return (
                    f"Section index {section_index} out of range "
                    f"(song has {len(song.sections)} sections, 0-based)."
                )

            section = song.sections[section_index]
            section.pattern = self.pattern_cache[pattern_id]
            section_name = section.name

            logger.success(
                f"Assigned {pattern_id} → {song_id}[{section_index}] ({section_name})"
            )
            return (
                f"Assigned pattern '{pattern_id}' to section {section_index} "
                f"('{section_name}') of song '{song_id}'."
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
            assign_pattern_to_section,
            list_genres,
            list_drummers,
        ]

    def _create_agent(self) -> Any:
        """Create Langchain 1.x agent using create_agent (LangGraph-backed).

        Returns:
            Compiled LangGraph state machine (CompiledStateGraph)
        """
        from langchain.agents import create_agent

        logger.debug("Creating agent with create_agent()")

        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=SYSTEM_PROMPT,
        )

        logger.debug("LangGraph agent created successfully")
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

        # Invoke LangGraph agent with messages format (Langchain 1.x)
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": user_request}]}
        )

        logger.success("Agent composition complete")

        # LangGraph agent returns {"messages": [...]} - last message is the response
        messages = result.get("messages", [])
        final_response = messages[-1].content if messages else ""

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

    def export_pattern(
        self,
        pattern_or_id: Pattern | str,
        output_path: str,
        tempo: int = 120,
    ) -> bool:
        """Export a pattern (by ID or object) to MIDI file.

        Args:
            pattern_or_id: Pattern object or pattern ID string from agent cache
            output_path: Destination file path for MIDI output
            tempo: Tempo in BPM used for MIDI export

        Returns:
            True if export succeeded, False otherwise
        """
        from midi_drums.engines.midi_engine import MIDIEngine

        if isinstance(pattern_or_id, str):
            pattern = self.get_pattern(pattern_or_id)
            if pattern is None:
                logger.error(f"Pattern not found in cache: {pattern_or_id}")
                return False
        else:
            pattern = pattern_or_id

        try:
            engine = MIDIEngine()
            engine.save_pattern_midi(pattern, Path(output_path), tempo)
            logger.success(f"Pattern exported to: {output_path}")
            return True
        except Exception as exc:
            logger.error(f"Failed to export pattern: {exc}")
            return False

    def export_song(
        self,
        song_or_id: Song | str,
        output_path: str,
    ) -> bool:
        """Export a song (by ID or object) to MIDI file.

        Args:
            song_or_id: Song object or song ID string from agent cache
            output_path: Destination file path for MIDI output

        Returns:
            True if export succeeded, False otherwise
        """
        from midi_drums.engines.midi_engine import MIDIEngine

        if isinstance(song_or_id, str):
            song = self.get_song(song_or_id)
            if song is None:
                logger.error(f"Song not found in cache: {song_or_id}")
                return False
        else:
            song = song_or_id

        try:
            engine = MIDIEngine()
            engine.save_song_midi(song, Path(output_path))
            logger.success(f"Song exported to: {output_path}")
            return True
        except Exception as exc:
            logger.error(f"Failed to export song: {exc}")
            return False
