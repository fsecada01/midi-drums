"""Pydantic AI-based pattern generation with type-safe structured outputs.

This module uses Pydantic AI to generate drum patterns from natural language
descriptions with full type safety and validation.
"""

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

from midi_drums.ai.schemas import (
    PatternCharacteristics,
    PatternGenerationRequest,
    PatternGenerationResponse,
)
from midi_drums.core.engine import DrumGenerator
from midi_drums.models.pattern import Pattern


class PydanticPatternGenerator:
    """Type-safe pattern generator using Pydantic AI.

    This class uses Pydantic AI with Claude to analyze natural language
    pattern descriptions and generate structured, validated pattern
    specifications that integrate with the existing MIDI Drums architecture.
    """

    def __init__(self, api_key: str | None = None):
        """Initialize the Pydantic AI pattern generator.

        Args:
            api_key: Optional Anthropic API key. If not provided, will use
                    ANTHROPIC_API_KEY environment variable.
        """
        # Initialize Anthropic model
        self.model = AnthropicModel(
            "claude-sonnet-4-20250514",  # Latest Claude Sonnet
            api_key=api_key,
        )

        # Create agent for pattern characteristic inference
        self.characteristics_agent = Agent(
            self.model,
            result_type=PatternCharacteristics,
            system_prompt=self._build_system_prompt(),
        )

        # Initialize drum generator for actual pattern creation
        self.drum_generator = DrumGenerator()

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for pattern analysis."""
        return """You are an expert drum pattern analyzer for the
MIDI Drums Generator.

Your role is to analyze natural language descriptions of drum patterns and infer
the appropriate musical characteristics to generate them.

## Available Genres and Styles:

**Metal**: heavy, death, power, progressive, thrash, doom, breakdown
**Rock**: classic, blues, alternative, progressive, punk, hard, pop
**Jazz**: swing, bebop, fusion, latin, ballad, hard_bop, contemporary
**Funk**: classic, pfunk, shuffle, new_orleans, fusion, minimal, heavy

## Available Drummer Styles:

- **bonham**: John Bonham - triplet vocabulary, behind-the-beat timing
- **porcaro**: Jeff Porcaro - half-time shuffle, studio precision
- **weckl**: Dave Weckl - linear playing, fusion expertise
- **chambers**: Dennis Chambers - funk mastery, incredible chops
- **roeder**: Jason Roeder - atmospheric sludge, minimal creativity
- **dee**: Mikkey Dee - speed/precision, versatile power
- **hoglan**: Gene Hoglan - mechanical precision, blast beats

## Pattern Templates Available:

- BasicGroove: Standard kick + snare + hihat
- DoubleBassPedal: Continuous, gallop, burst patterns
- BlastBeat: Traditional, hammer, gravity blast beats
- JazzRidePattern: Swing ride patterns with accents
- FunkGhostNotes: Ghost note layers for funk
- CrashAccents: Crash cymbal placement
- TomFill: Descending, ascending, accent fills

## Drummer Modifications Available:

- BehindBeatTiming, TripletVocabulary, GhostNoteLayer
- LinearCoordination, HeavyAccents, ShuffleFeelApplication
- FastChopsTriplets, PocketStretching, MinimalCreativity
- SpeedPrecision, TwistedAccents, MechanicalPrecision

## Your Task:

Analyze the user's pattern description and infer:
1. **Genre** and **Style**: Choose the most appropriate combination
2. **Intensity**: How aggressive/energetic (0.0=gentle, 1.0=maximum)
3. **Techniques**: Which drum techniques apply (double bass, ghost
   notes, syncopation)
4. **Primary Cymbal**: Which cymbal is central (hihat, ride, crash)
5. **Reasoning**: Brief explanation of your choices

Be intelligent about keywords:
- "aggressive", "heavy", "brutal" → high intensity, possibly metal
- "swing", "smooth", "groovy" → jazz/funk, lower intensity
- "fast", "blast", "extreme" → death metal, use_double_bass=True
- "ghost notes", "subtle" → use_ghost_notes=True
- "syncopated", "offbeat" → use_syncopation=True
- Drummer names → match to available styles

Provide thoughtful analysis based on musical knowledge and the
description context.
"""

    async def analyze_pattern_description(
        self, description: str
    ) -> PatternCharacteristics:
        """Analyze natural language pattern description using Pydantic AI.

        Args:
            description: Natural language pattern description

        Returns:
            PatternCharacteristics with AI-inferred characteristics

        Example:
            >>> gen = PydanticPatternGenerator()
            >>> chars = await gen.analyze_pattern_description(
            ...     "aggressive death metal breakdown with double bass"
            ... )
            >>> print(f"Genre: {chars.genre}, Style: {chars.style}")
            Genre: metal, Style: death
        """
        result = await self.characteristics_agent.run(description)
        return result.data

    def generate_pattern(
        self,
        request: PatternGenerationRequest,
        characteristics: PatternCharacteristics | None = None,
    ) -> tuple[Pattern, PatternGenerationResponse]:
        """Generate drum pattern from request using AI analysis.

        Args:
            request: Pattern generation request with NL description
            characteristics: Optional pre-analyzed characteristics.
                           If None, will analyze description first.

        Returns:
            Tuple of (generated Pattern, generation response metadata)

        Example:
            >>> gen = PydanticPatternGenerator()
            >>> request = PatternGenerationRequest(
            ...     description="funky groove with ghost notes",
            ...     tempo=110,
            ...     bars=4
            ... )
            >>> pattern, response = gen.generate_pattern(request)
            >>> print(f"Generated: {pattern.name}")
        """
        # Analyze characteristics if not provided (requires async call)
        if characteristics is None:
            raise ValueError(
                "Characteristics must be provided or use "
                "async generate_pattern_async() method"
            )

        # Generate pattern using existing architecture
        pattern = self.drum_generator.generate_pattern(
            genre=characteristics.genre,
            section=request.section,
            style=characteristics.style,
            bars=request.bars,
        )

        if pattern is None:
            raise ValueError(
                f"Failed to generate pattern for {characteristics.genre}/"
                f"{characteristics.style}"
            )

        # Apply drummer style if requested
        if request.drummer_style:
            pattern = self.drum_generator.apply_drummer_style(
                pattern, request.drummer_style
            )

        # Build response metadata
        response = PatternGenerationResponse(
            pattern_name=pattern.name,
            characteristics=characteristics,
            templates_used=self._infer_templates_used(characteristics),
            modifications_applied=self._infer_modifications(
                request.drummer_style
            ),
            confidence=0.85,  # High confidence with Claude analysis
            suggestions=self._generate_suggestions(characteristics),
        )

        return pattern, response

    async def generate_pattern_async(
        self, request: PatternGenerationRequest
    ) -> tuple[Pattern, PatternGenerationResponse]:
        """Async version of generate_pattern with automatic analysis.

        Args:
            request: Pattern generation request with NL description

        Returns:
            Tuple of (generated Pattern, generation response metadata)

        Example:
            >>> gen = PydanticPatternGenerator()
            >>> request = PatternGenerationRequest(
            ...     description="aggressive metal breakdown with double bass"
            ... )
            >>> pattern, response = await gen.generate_pattern_async(request)
        """
        # Analyze characteristics from description
        characteristics = await self.analyze_pattern_description(
            request.description
        )

        # Generate pattern using analyzed characteristics
        return self.generate_pattern(request, characteristics)

    def _infer_templates_used(
        self, characteristics: PatternCharacteristics
    ) -> list[str]:
        """Infer which pattern templates were likely used."""
        templates = ["BasicGroove"]

        if characteristics.use_double_bass:
            templates.append("DoubleBassPedal")

        if "blast" in characteristics.style.lower() or (
            characteristics.genre == "metal" and characteristics.intensity > 0.7
        ):
            templates.append("BlastBeat")

        if characteristics.genre == "jazz":
            templates.append("JazzRidePattern")

        if characteristics.use_ghost_notes:
            templates.append("FunkGhostNotes")

        return templates

    def _infer_modifications(self, drummer_style: str | None) -> list[str]:
        """Infer which drummer modifications were applied."""
        if not drummer_style:
            return []

        # Map drummer styles to their modifications
        modification_map = {
            "bonham": [
                "BehindBeatTiming",
                "TripletVocabulary",
                "HeavyAccents",
            ],
            "porcaro": ["ShuffleFeelApplication", "GhostNoteLayer"],
            "weckl": ["LinearCoordination", "GhostNoteLayer"],
            "chambers": [
                "BehindBeatTiming",
                "FastChopsTriplets",
                "GhostNoteLayer",
                "PocketStretching",
            ],
            "roeder": ["MinimalCreativity", "HeavyAccents"],
            "dee": ["SpeedPrecision", "TwistedAccents"],
            "hoglan": ["MechanicalPrecision", "HeavyAccents"],
        }

        return modification_map.get(drummer_style, [])

    def _generate_suggestions(
        self, characteristics: PatternCharacteristics
    ) -> list[str]:
        """Generate suggestions for alternative patterns."""
        suggestions = []

        # Suggest intensity variations
        if characteristics.intensity < 0.5:
            suggestions.append(
                f"Try higher intensity for more aggressive {
                    characteristics.genre
                }"
            )
        elif characteristics.intensity > 0.7:
            suggestions.append(
                f"Try lower intensity for more subtle {
                    characteristics.genre
                }"
            )

        # Suggest style variations within genre
        style_suggestions = {
            "metal": ["Try 'progressive' for complex patterns"],
            "rock": ["Try 'blues' for shuffle feel"],
            "jazz": ["Try 'fusion' for modern energy"],
            "funk": ["Try 'minimal' for pocket grooves"],
        }

        if characteristics.genre in style_suggestions:
            suggestions.extend(style_suggestions[characteristics.genre])

        return suggestions[:3]  # Limit to 3 suggestions
