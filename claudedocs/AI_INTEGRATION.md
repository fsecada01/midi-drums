# AI Integration for MIDI Drums Generator

**Status**: ✅ **IMPLEMENTATION COMPLETE**

## Overview

The MIDI Drums Generator now includes powerful AI integration using both **Pydantic AI** (type-safe) and **Langchain** (agent-based) approaches. This enables natural language pattern generation, intelligent composition, and creative musical assistance.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Unified AI API                               │
│                  DrumGeneratorAI                                │
├─────────────────────────────────────────────────────────────────┤
│  Pydantic AI (Type-Safe)  │  Langchain (Agent-Based)            │
│  - Pattern Analysis       │  - Multi-step Reasoning             │
│  - Structured Outputs     │  - Tool Orchestration               │
│  - Validation             │  - Creative Suggestions             │
├─────────────────────────────────────────────────────────────────┤
│                Existing MIDI Drums Architecture                 │
│  Pattern Templates │ Modifications │ Genre/Drummer Plugins      │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### 1. Natural Language Pattern Generation (Pydantic AI)

Generate drum patterns from text descriptions with full type safety:

```python
from midi_drums.ai import DrumGeneratorAI

ai = DrumGeneratorAI(api_key="your-anthropic-key")

# Type-safe pattern generation
pattern, response = await ai.generate_pattern_from_text(
    "aggressive metal breakdown with double bass and blast beats",
    tempo=180,
    bars=4
)

# Access structured metadata
print(f"Genre: {response.characteristics.genre}")
print(f"Style: {response.characteristics.style}")
print(f"Intensity: {response.characteristics.intensity}")
print(f"AI Confidence: {response.confidence}")
print(f"Templates Used: {response.templates_used}")

# Export to MIDI
ai.export_pattern(pattern, "breakdown.mid", tempo=180)
```

**Key Benefits:**
- ✅ Type-safe with Pydantic validation
- ✅ Structured, predictable outputs
- ✅ Full metadata and reasoning
- ✅ High confidence analysis

### 2. Agent-Based Composition (Langchain)

Intelligent agent that can reason, plan, and compose:

```python
# Agent can handle complex requests
result = ai.compose_with_agent(
    "create a progressive metal song at 140 BPM with "
    "intro, verse, chorus, verse, chorus, bridge, breakdown, chorus, outro"
)

# Agent chains multiple operations
result = ai.compose_with_agent(
    "create a classic rock verse and then apply John Bonham's style"
)

# Agent provides musical knowledge
result = ai.compose_with_agent(
    "what drummer styles are available and which would work "
    "best for jazz fusion?"
)
```

**Key Benefits:**
- ✅ Multi-step reasoning and planning
- ✅ Tool orchestration (generate → apply style → compose)
- ✅ Creative suggestions and alternatives
- ✅ Musical knowledge and guidance

### 3. Quick Convenience Methods

Rapid generation for common use cases:

```python
# Quick pattern with immediate export
pattern = await ai.quick_pattern(
    "heavy thrash metal with fast double bass",
    output_path="thrash.mid"
)

# Quick song composition
song_id = ai.quick_song(
    "energetic punk rock song",
    output_path="punk_song.mid"
)
```

## Installation

### 1. Install AI Dependencies

Using uv (recommended):
```bash
uv sync --group ai
```

Using pip:
```bash
pip install -r ai_requirements.txt
```

### 2. Set API Key

```bash
# Environment variable (recommended)
export ANTHROPIC_API_KEY='your-anthropic-api-key'

# Or pass directly in code
ai = DrumGeneratorAI(api_key="your-key")
```

## Dependencies

The AI integration adds these dependencies:

```toml
[dependency-groups]
ai = [
    "langchain>=0.3.0",           # Agent framework
    "langchain-openai>=0.3.0",    # OpenAI integration
    "pydantic-ai>=0.0.14",        # Type-safe AI
    "librosa>=0.10.0",            # Audio analysis (future)
    "numpy>=1.24.0",              # Audio processing
    "soundfile>=0.12.0",          # Audio file I/O
    "anthropic>=0.39.0",          # Claude API
]
```

## Examples

### Example 1: Type-Safe Pattern Generation

```python
import asyncio
from midi_drums.ai import DrumGeneratorAI

async def generate_patterns():
    ai = DrumGeneratorAI()

    # Metal breakdown
    pattern1, info1 = await ai.generate_pattern_from_text(
        "aggressive death metal breakdown with double bass",
        tempo=180
    )
    print(f"Generated: {pattern1.name}")
    print(f"Style: {info1.characteristics.style}")
    ai.export_pattern(pattern1, "breakdown.mid", tempo=180)

    # Funky groove
    pattern2, info2 = await ai.generate_pattern_from_text(
        "funky groove with ghost notes and syncopation",
        tempo=110,
        drummer_style="chambers"
    )
    ai.export_pattern(pattern2, "funk.mid", tempo=110)

asyncio.run(generate_patterns())
```

### Example 2: Agent-Based Song Composition

```python
from midi_drums.ai import DrumGeneratorAI

ai = DrumGeneratorAI()

# Compose complete song
result = ai.compose_with_agent(
    "create a progressive rock song at 145 BPM with "
    "intro verse chorus verse chorus bridge solo chorus outro, "
    "use Dave Weckl's drumming style"
)

print(result['output'])
# Extract song_id from output and export
```

### Example 3: Interactive Refinement

```python
ai = DrumGeneratorAI()

# Initial request
result1 = ai.compose_with_agent("create a metal verse pattern")

# Refine
result2 = ai.compose_with_agent(
    "make it more aggressive with double bass"
)

# Apply style
result3 = ai.compose_with_agent(
    "apply Gene Hoglan's style for mechanical precision"
)
```

### Example 4: Batch Generation

```python
async def batch_generate():
    ai = DrumGeneratorAI()

    descriptions = [
        "aggressive metal breakdown",
        "heavy doom metal breakdown",
        "technical progressive breakdown",
    ]

    for i, desc in enumerate(descriptions, 1):
        pattern, info = await ai.generate_pattern_from_text(desc)
        ai.export_pattern(pattern, f"variant_{i}.mid", tempo=180)
        print(f"Variant {i}: {info.characteristics.style}")

asyncio.run(batch_generate())
```

## Pydantic AI Schemas

The AI integration uses Pydantic for type-safe, validated outputs:

### PatternGenerationRequest
```python
class PatternGenerationRequest(BaseModel):
    description: str         # Natural language description
    section: Literal[...]    # verse, chorus, bridge, etc.
    tempo: int              # 40-300 BPM
    bars: int               # 1-16 bars
    complexity: float       # 0.0-1.0
    drummer_style: Optional[str]  # bonham, porcaro, etc.
```

### PatternCharacteristics
```python
class PatternCharacteristics(BaseModel):
    genre: Literal[...]           # metal, rock, jazz, funk
    style: str                    # Specific style within genre
    intensity: float              # 0.0-1.0
    use_double_bass: bool
    use_ghost_notes: bool
    use_syncopation: bool
    primary_cymbal: Literal[...]  # hihat, ride, crash
    reasoning: str                # AI's analysis reasoning
```

### PatternGenerationResponse
```python
class PatternGenerationResponse(BaseModel):
    pattern_name: str
    characteristics: PatternCharacteristics
    templates_used: list[str]
    modifications_applied: list[str]
    confidence: float
    suggestions: list[str]
```

## Langchain Agent Tools

The agent has access to these tools:

1. **generate_pattern**: Create patterns with specific genre/style/section
2. **apply_drummer_style**: Apply drummer techniques to existing patterns
3. **create_song**: Compose complete multi-section songs
4. **list_genres**: Show available genres and styles
5. **list_drummers**: Show available drummer styles with descriptions

## API Reference

### DrumGeneratorAI

Main unified interface for AI features.

**Methods:**

```python
# Async type-safe generation
async def generate_pattern_from_text(
    description: str,
    section: str = "verse",
    tempo: int = 120,
    bars: int = 4,
    complexity: float = 0.5,
    drummer_style: Optional[str] = None
) -> tuple[Pattern, PatternGenerationResponse]

# Sync wrapper
def generate_pattern_from_text_sync(...) -> tuple[Pattern, PatternGenerationResponse]

# Agent-based composition
def compose_with_agent(request: str) -> dict

# Export utilities
def export_pattern(pattern: Union[Pattern, str], output_path: str, tempo: int = 120) -> bool
def export_song(song: Union[Song, str], output_path: str) -> bool

# Convenience methods
async def quick_pattern(description: str, output_path: Optional[str] = None) -> Pattern
def quick_song(description: str, output_path: Optional[str] = None) -> str
```

## Performance Considerations

- **Pydantic AI**: ~2-5 seconds per pattern (single LLM call)
- **Langchain Agent**: ~5-15 seconds (multi-step reasoning, tool calls)
- **Caching**: Patterns and songs cached in memory during agent session
- **Async**: Use `async` methods for better performance with concurrent operations

## Future Enhancements

### Planned Features
- [ ] **Audio Analysis**: WAV/MP3 → MIDI pattern extraction
- [ ] **Pattern Evolution**: AI-driven pattern variations and progressions
- [ ] **Style Transfer**: Blend drummer styles or transfer between genres
- [ ] **Learning System**: Learn from user feedback and preferences
- [ ] **Real-time Generation**: Stream-based pattern generation
- [ ] **Multi-modal**: Visual pattern editing with AI suggestions

### Audio Analysis (In Progress)
```python
# Future API
from midi_drums.ai import DrumGeneratorAI

ai = DrumGeneratorAI()

# Analyze audio file and generate MIDI pattern
pattern, analysis = await ai.analyze_audio(
    audio_path="drums.wav",
    genre_hint="metal",
    extract_tempo=True
)

print(f"Detected Tempo: {analysis.detected_tempo} BPM")
print(f"Pattern: {analysis.pattern_description}")
ai.export_pattern(pattern, "extracted.mid")
```

## Best Practices

### 1. Be Descriptive
```python
# Good: Detailed description
"aggressive death metal breakdown with continuous double bass pedal, "
"blast beats on the ride, and syncopated crash accents"

# Less effective: Vague description
"metal pattern"
```

### 2. Use Appropriate Approach
```python
# Use Pydantic AI for:
- Single pattern generation with validation
- Type-safe, predictable outputs
- When you need structured metadata

# Use Langchain Agent for:
- Multi-step composition workflows
- Creative exploration and suggestions
- Complex song structures
- Musical knowledge queries
```

### 3. Leverage Drummer Styles
```python
# Combine genre + style + drummer for authentic results
pattern, _ = await ai.generate_pattern_from_text(
    "classic rock verse with behind-the-beat feel",
    drummer_style="bonham"  # John Bonham's signature style
)
```

### 4. Iterate and Refine
```python
# Start simple, refine with agent
result1 = ai.compose_with_agent("create a rock pattern")
result2 = ai.compose_with_agent("make it more syncopated")
result3 = ai.compose_with_agent("apply Porcaro's shuffle feel")
```

## Troubleshooting

### API Key Issues
```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# Set temporarily
export ANTHROPIC_API_KEY='your-key'

# Set permanently (add to ~/.bashrc or ~/.zshrc)
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
```

### Import Errors
```bash
# Ensure AI dependencies are installed
uv sync --group ai

# Verify installation
python -c "import pydantic_ai; import langchain; print('OK')"
```

### Pattern Generation Failures
- Check description is specific enough (5+ words)
- Verify genre/style combination exists
- Use agent's `list_genres` and `list_drummers` tools
- Check API key permissions and usage limits

## Examples File

Complete examples with all features:
```bash
# Run comprehensive AI examples
python examples/ai_examples.py
```

This will generate:
- Multiple pattern variations
- Complete songs
- Agent-based compositions
- Batch generations
- All exported to `output/` directory

## Integration with Existing API

The AI features integrate seamlessly:

```python
from midi_drums import DrumGenerator
from midi_drums.ai import DrumGeneratorAI

# Traditional approach
gen = DrumGenerator()
pattern1 = gen.generate_pattern("metal", "verse", "death")

# AI approach
ai = DrumGeneratorAI()
pattern2, info = await ai.generate_pattern_from_text(
    "death metal verse pattern"
)

# Both produce Pattern objects compatible with existing MIDI export
gen.export_pattern_midi(pattern1, "traditional.mid", tempo=180)
ai.export_pattern(pattern2, "ai_generated.mid", tempo=180)
```

## License and Attribution

The AI integration uses:
- **Anthropic Claude**: For LLM-powered analysis and generation
- **Pydantic AI**: Type-safe AI framework (Apache 2.0)
- **Langchain**: Agent framework (MIT)

All AI-generated patterns are created using the existing MIDI Drums Generator
architecture and pattern templates.

---

**Generated**: 2025-10-26
**Author**: Claude Code
**Project**: MIDI Drums Generator AI Integration
