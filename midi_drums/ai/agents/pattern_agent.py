"""Langchain agent for intelligent pattern composition and evolution.

This agent orchestrates pattern generation, evolution, and composition using
Langchain's agent framework with access to the MIDI Drums Generator as tools.
"""

from typing import Any

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import BaseTool, StructuredTool
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from midi_drums.core.engine import DrumGenerator
from midi_drums.models.pattern import Pattern
from midi_drums.models.song import Song


# Tool input schemas
class GeneratePatternInput(BaseModel):
    """Input for generate_pattern tool."""

    genre: str = Field(description="Genre (metal, rock, jazz, funk)")
    style: str = Field(
        description="Style within genre (e.g., 'death', 'swing')"
    )
    section: str = Field(
        description="Section (verse, chorus, bridge, breakdown)"
    )
    bars: int = Field(default=4, description="Number of bars (1-16)")


class ApplyDrummerStyleInput(BaseModel):
    """Input for apply_drummer_style tool."""

    pattern_id: str = Field(
        description="ID of pattern to modify (use from previous generation)"
    )
    drummer: str = Field(
        description="Drummer style (bonham, porcaro, weckl, chambers, etc.)"
    )


class CreateSongInput(BaseModel):
    """Input for create_song tool."""

    genre: str = Field(description="Primary genre")
    style: str = Field(description="Primary style")
    tempo: int = Field(default=120, description="Tempo in BPM")
    structure_description: str = Field(
        description="Description of song structure (e.g., 'verse chorus verse "
        "chorus bridge chorus')"
    )


class PatternCompositionAgent:
    """Langchain agent for intelligent drum pattern composition.

    This agent can:
    - Generate patterns from natural language
    - Apply drummer styles and modifications
    - Compose complete songs with multiple sections
    - Evolve and vary existing patterns
    - Provide musical suggestions and alternatives
    """

    def __init__(self, api_key: str | None = None):
        """Initialize the pattern composition agent.

        Args:
            api_key: Optional Anthropic API key. If not provided, will use
                    ANTHROPIC_API_KEY environment variable.
        """
        # Initialize LLM
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=api_key,
            temperature=0.7,  # Creativity for composition
        )

        # Initialize drum generator
        self.drum_generator = DrumGenerator()

        # Pattern storage for reference across agent calls
        self.pattern_cache: dict[str, Pattern] = {}
        self.song_cache: dict[str, Song] = {}

        # Create tools
        self.tools = self._create_tools()

        # Create agent
        self.agent = self._create_agent()

    def _create_tools(self) -> list[BaseTool]:
        """Create Langchain tools for drum generation."""

        def generate_pattern_tool(
            genre: str, style: str, section: str, bars: int = 4
        ) -> str:
            """Generate a drum pattern with specified characteristics.

            Args:
                genre: Musical genre (metal, rock, jazz, funk)
                style: Specific style within genre
                section: Song section type
                bars: Number of bars in pattern

            Returns:
                Description of generated pattern with ID for reference
            """
            pattern = self.drum_generator.generate_pattern(
                genre=genre, section=section, style=style, bars=bars
            )

            if pattern is None:
                return f"Error: Could not generate {genre}/{style} pattern"

            # Store pattern for later reference
            pattern_id = f"{genre}_{style}_{section}_{len(
                self.pattern_cache
            )}"
            self.pattern_cache[pattern_id] = pattern

            return (
                f"Generated {genre} {style} {section} pattern (ID: "
                f"{pattern_id}) with {len(pattern.beats)} beats across {bars}"
                f" bars. Pattern name: {pattern.name}"
            )

        def apply_drummer_style_tool(pattern_id: str, drummer: str) -> str:
            """Apply a specific drummer's style to an existing pattern.

            Args:
                pattern_id: ID of pattern from previous generation
                drummer: Drummer style to apply

            Returns:
                Description of modified pattern
            """
            if pattern_id not in self.pattern_cache:
                return f"Error: Pattern ID '{pattern_id}' not found"

            pattern = self.pattern_cache[pattern_id]
            styled_pattern = self.drum_generator.apply_drummer_style(
                pattern, drummer
            )

            if styled_pattern is None:
                return f"Error: Could not apply {drummer} style"

            # Store styled version with new ID
            styled_id = f"{pattern_id}_{drummer}"
            self.pattern_cache[styled_id] = styled_pattern

            return (
                f"Applied {drummer} drummer style to {pattern_id}. "
                f"New pattern ID: {styled_id}. "
                f"Pattern now has {len(styled_pattern.beats)} beats with "
                f"{drummer}'s characteristic techniques."
            )

        def list_genres_tool() -> str:
            """List all available genres and their styles."""
            genres = self.drum_generator.get_available_genres()
            result = "Available genres and styles:\n\n"

            for genre in genres:
                styles = self.drum_generator.get_genre_styles(genre)
                result += f"**{genre.upper()}**: {', '.join(styles)}\n"

            return result

        def list_drummers_tool() -> str:
            """List all available drummer styles with descriptions."""
            drummers = self.drum_generator.get_available_drummers()
            descriptions = {
                "bonham": "John Bonham - triplet vocabulary, behind-the-beat "
                "timing",
                "porcaro": "Jeff Porcaro - half-time shuffle, studio "
                "precision",
                "weckl": "Dave Weckl - linear playing, fusion expertise",
                "chambers": "Dennis Chambers - funk mastery, incredible chops",
                "roeder": "Jason Roeder - atmospheric sludge, minimal "
                "creativity",
                "dee": "Mikkey Dee - speed/precision, versatile power",
                "hoglan": "Gene Hoglan - mechanical precision, blast beats",
            }

            result = "Available drummer styles:\n\n"
            for drummer in drummers:
                desc = descriptions.get(drummer, "No description available")
                result += f"- **{drummer}**: {desc}\n"

            return result

        def create_song_tool(
            genre: str, style: str, tempo: int, structure_description: str
        ) -> str:
            """Create a complete song with multiple sections.

            Args:
                genre: Primary musical genre
                style: Primary style within genre
                tempo: Tempo in BPM
                structure_description: Natural language song structure

            Returns:
                Description of created song
            """
            # Parse structure description into sections
            # Simple parsing: "verse chorus verse chorus bridge chorus"
            section_map = {
                "verse": ("verse", 8),
                "chorus": ("chorus", 8),
                "bridge": ("bridge", 4),
                "breakdown": ("breakdown", 4),
                "intro": ("intro", 4),
                "outro": ("outro", 4),
            }

            structure = []
            words = structure_description.lower().split()

            for word in words:
                if word in section_map:
                    structure.append(section_map[word])

            # Default structure if parsing fails
            if not structure:
                structure = [
                    ("intro", 4),
                    ("verse", 8),
                    ("chorus", 8),
                    ("verse", 8),
                    ("chorus", 8),
                    ("outro", 4),
                ]

            # Create song
            song = self.drum_generator.create_song(
                genre=genre,
                style=style,
                tempo=tempo,
                structure=structure,
                complexity=0.7,
            )

            # Store song
            song_id = f"{genre}_{style}_song_{len(self.song_cache)}"
            self.song_cache[song_id] = song

            total_bars = sum(s.bars for s in song.sections)
            duration = (total_bars * 4 * 60) / tempo  # Rough estimate

            return (
                f"Created {genre} {style} song (ID: {song_id}) at {tempo} BPM."
                f" Structure: {len(song.sections)} sections, {total_bars} "
                f"total bars, ~{duration:.1f} seconds. "
                f"Sections: {', '.join(s.section_type for s in song.sections)}"
            )

        # Create structured tools
        return [
            StructuredTool.from_function(
                func=generate_pattern_tool,
                name="generate_pattern",
                description="Generate a drum pattern with specific genre, "
                "style, and section",
                args_schema=GeneratePatternInput,
            ),
            StructuredTool.from_function(
                func=apply_drummer_style_tool,
                name="apply_drummer_style",
                description="Apply a specific drummer's playing style to an "
                "existing pattern",
                args_schema=ApplyDrummerStyleInput,
            ),
            StructuredTool.from_function(
                func=list_genres_tool,
                name="list_genres",
                description="List all available musical genres and their "
                "styles",
            ),
            StructuredTool.from_function(
                func=list_drummers_tool,
                name="list_drummers",
                description="List all available drummer styles with "
                "descriptions",
            ),
            StructuredTool.from_function(
                func=create_song_tool,
                name="create_song",
                description="Create a complete song with multiple sections "
                "and structure",
                args_schema=CreateSongInput,
            ),
        ]

    def _create_agent(self) -> AgentExecutor:
        """Create the Langchain agent with tools."""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert drum composition assistant with deep
knowledge of drumming, musical genres, and song structure.

You have access to tools that can generate drum patterns, apply drummer
styles, and create complete songs using the MIDI Drums Generator system.

## Your Capabilities:

1. **Pattern Generation**: Create drum patterns for any genre/style/section
2. **Drummer Styles**: Apply authentic playing styles from famous drummers
3. **Song Composition**: Build complete multi-section songs
4. **Musical Guidance**: Suggest appropriate styles, structures, and techniques

## Available Genres:
- **Metal**: heavy, death, power, progressive, thrash, doom, breakdown
- **Rock**: classic, blues, alternative, progressive, punk, hard, pop
- **Jazz**: swing, bebop, fusion, latin, ballad, hard_bop, contemporary
- **Funk**: classic, pfunk, shuffle, new_orleans, fusion, minimal, heavy

## Available Drummers:
- bonham, porcaro, weckl, chambers, roeder, dee, hoglan

## Guidelines:

- **Understand Intent**: Analyze what the user wants musically
- **Make Intelligent Choices**: Select appropriate genres, styles, and drummers
- **Be Creative**: Suggest variations and alternatives
- **Explain Decisions**: Tell users why you chose specific options
- **Use Tools Wisely**: Chain tool calls to build complex compositions
- **Provide Context**: Explain musical terms and techniques

When users ask for patterns or songs:
1. First understand their musical goals
2. Choose appropriate genre, style, and section
3. Generate the pattern/song using tools
4. Optionally apply drummer styles for authenticity
5. Suggest variations or improvements
6. Provide the pattern/song ID for export

Be helpful, creative, and musically knowledgeable!
""",
                ),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )

    def compose(self, user_request: str) -> dict[str, Any]:
        """Process a user composition request using the agent.

        Args:
            user_request: Natural language request for pattern/song composition

        Returns:
            Agent response with generated patterns/songs

        Example:
            >>> agent = PatternCompositionAgent()
            >>> result = agent.compose(
            ...     "create an aggressive death metal breakdown with "
            ...     "double bass"
            ... )
            >>> print(result['output'])
        """
        result = self.agent.invoke({"input": user_request})
        return result

    def get_pattern(self, pattern_id: str) -> Pattern | None:
        """Retrieve a generated pattern by ID.

        Args:
            pattern_id: Pattern ID from agent response

        Returns:
            Pattern object or None if not found
        """
        return self.pattern_cache.get(pattern_id)

    def get_song(self, song_id: str) -> Song | None:
        """Retrieve a generated song by ID.

        Args:
            song_id: Song ID from agent response

        Returns:
            Song object or None if not found
        """
        return self.song_cache.get(song_id)

    def export_pattern(
        self, pattern_id: str, output_path: str, tempo: int = 120
    ) -> bool:
        """Export a generated pattern to MIDI file.

        Args:
            pattern_id: Pattern ID from agent
            output_path: Path for MIDI file output
            tempo: Tempo in BPM

        Returns:
            True if successful, False otherwise
        """
        pattern = self.get_pattern(pattern_id)
        if pattern is None:
            return False

        self.drum_generator.export_pattern_midi(pattern, output_path, tempo)
        return True

    def export_song(self, song_id: str, output_path: str) -> bool:
        """Export a generated song to MIDI file.

        Args:
            song_id: Song ID from agent
            output_path: Path for MIDI file output

        Returns:
            True if successful, False otherwise
        """
        song = self.get_song(song_id)
        if song is None:
            return False

        self.drum_generator.export_midi(song, output_path)
        return True
