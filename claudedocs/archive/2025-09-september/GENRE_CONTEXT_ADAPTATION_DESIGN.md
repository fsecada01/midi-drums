# Genre-Contextual Adaptation Design

**Feature Request**: Allow non-primary genre patterns to adapt to the overall song genre context while maintaining their characteristic feel.

**Example**: In a death metal song with progressive sections, make the progressive patterns feel more "metal-appropriate" without losing their progressive complexity.

---

## Current Behavior

When generating a complex death metal song with multiple genres:
- **Death metal sections**: Heavy, aggressive, blast beats @ 180 BPM
- **Doom sections**: Slow, crushing @ 70 BPM (very different intensity)
- **Progressive sections**: Complex, technical @ 160 BPM (jazz-influenced)

**Issue**: Each genre pattern reflects its **pure genre characteristics** rather than adapting to the overall song context (metal).

---

## Proposed Solution: Context Blending

### Core Concept: Genre Context Parameters

Add a new parameter system that allows patterns to be "colored" by a primary genre context:

```python
@dataclass
class GenerationParameters:
    genre: str  # Primary genre for this pattern
    style: str = "default"

    # NEW: Context adaptation
    song_genre_context: str | None = None  # Overall song genre
    context_blend: float = 0.3  # 0.0-1.0, how much to blend with context

    # Existing parameters
    complexity: float = 0.5
    dynamics: float = 0.5
    humanization: float = 0.3
    ...
```

### How It Works

#### 1. **Context Intensity Mapping**
Each genre defines intensity characteristics:

```python
# In GenrePlugin base class
@property
def intensity_profile(self) -> dict[str, float]:
    """Return genre's intensity characteristics (0.0-1.0 scale)."""
    return {
        "aggression": 0.5,      # How aggressive/heavy
        "speed": 0.5,           # Typical tempo range
        "density": 0.5,         # Note density
        "power": 0.5,           # Kick/snare intensity
        "complexity": 0.5,      # Pattern complexity
        "darkness": 0.5,        # Tonal darkness
    }
```

**Example Profiles**:

```python
# Metal Genre
intensity_profile = {
    "aggression": 0.9,   # Very aggressive
    "speed": 0.8,        # Fast tempos
    "density": 0.8,      # Dense patterns
    "power": 1.0,        # Maximum power
    "complexity": 0.6,   # Moderate complexity
    "darkness": 0.9,     # Very dark
}

# Progressive (standalone)
intensity_profile = {
    "aggression": 0.5,   # Moderate
    "speed": 0.7,        # Varied tempos
    "density": 0.6,      # Complex but spacious
    "power": 0.6,        # Moderate power
    "complexity": 0.9,   # Very complex
    "darkness": 0.5,     # Neutral
}

# Progressive (metal-contextualized with 0.3 blend)
blended_profile = {
    "aggression": 0.62,  # 0.5 + (0.9-0.5)*0.3 = more aggressive
    "speed": 0.73,       # Slightly faster tendency
    "density": 0.66,     # Denser patterns
    "power": 0.72,       # More powerful hits
    "complexity": 0.9,   # Keep high complexity (main characteristic)
    "darkness": 0.62,    # Darker tonality
}
```

#### 2. **Pattern Adaptation Methods**

```python
class GenrePlugin:
    def apply_context_blend(
        self,
        pattern: Pattern,
        context_profile: dict[str, float],
        blend_amount: float
    ) -> Pattern:
        """Adapt pattern to match context genre characteristics."""

        adapted = pattern.copy()

        # Apply context-driven modifications
        for beat in adapted.beats:
            # Power: Increase kick/snare velocity based on context
            if beat.instrument in [DrumInstrument.KICK, DrumInstrument.SNARE]:
                context_power_boost = context_profile["power"] * blend_amount
                beat.velocity = min(127, beat.velocity + int(context_power_boost * 15))

            # Aggression: Tighten timing for aggressive contexts
            if context_profile["aggression"] > 0.7:
                # Less humanization = tighter, more aggressive
                timing_tightness = blend_amount * 0.5
                beat.position = round(beat.position / 0.0625) * 0.0625  # Quantize

            # Density: Add ghost notes or remove space
            if context_profile["density"] > 0.7:
                # Add supplementary hi-hat hits
                pass

        return adapted
```

#### 3. **Integration Points**

**In DrumGenerator.generate_pattern()**:

```python
def generate_pattern(
    self,
    genre: str,
    section: str,
    bars: int = 4,
    style: str = "default",
    song_genre_context: str | None = None,  # NEW
    context_blend: float = 0.3,              # NEW
    **kwargs
) -> Pattern | None:
    """Generate pattern with optional genre context adaptation."""

    # 1. Generate base pattern from genre plugin
    genre_plugin = self.plugin_manager.get_genre_plugin(genre)
    params = GenerationParameters(genre=genre, style=style, **kwargs)
    base_pattern = genre_plugin.generate_pattern(section, params)

    # 2. Apply context blending if specified
    if song_genre_context and song_genre_context != genre:
        context_plugin = self.plugin_manager.get_genre_plugin(song_genre_context)
        context_profile = context_plugin.intensity_profile

        base_pattern = genre_plugin.apply_context_blend(
            base_pattern,
            context_profile,
            context_blend
        )

    # 3. Apply drummer style, humanization, etc.
    # ... rest of existing logic
```

---

## Implementation Phases

### Phase 1: Core Infrastructure ✅ (Ready to Implement)

1. **Add `intensity_profile` property to `GenrePlugin` base class**
   - Default implementation returns neutral (0.5 for all)
   - Each genre overrides with its characteristic profile

2. **Add context parameters to `GenerationParameters`**
   - `song_genre_context: str | None`
   - `context_blend: float` (0.0-1.0)

3. **Implement `apply_context_blend()` in `GenrePlugin` base class**
   - Default implementation with velocity/timing adjustments
   - Subclasses can override for genre-specific adaptations

### Phase 2: Genre-Specific Profiles

Implement intensity profiles for existing genres:

1. **Metal**: High aggression, power, darkness
2. **Rock**: Moderate-high power, moderate aggression
3. **Jazz**: Low aggression, high complexity, moderate density
4. **Funk**: Moderate power, high groove (new metric?)

### Phase 3: Advanced Context Blending

1. **Instrument-specific blending**: Different blend amounts per instrument
2. **Section-aware blending**: Intro/outro vs. verse/chorus adaptations
3. **Multi-context blending**: Blend multiple genre influences
4. **Custom context profiles**: User-defined intensity profiles

---

## Usage Examples

### Example 1: Metal Song with Progressive Section

```python
generator = DrumGenerator()

# Death metal sections - no context needed (it's the primary genre)
death_intro = generator.generate_pattern(
    genre="metal",
    style="death",
    section="intro",
    bars=4
)

# Progressive bridge - adapted to metal context
prog_bridge = generator.generate_pattern(
    genre="metal",
    style="progressive",
    section="bridge",
    bars=6,
    song_genre_context="metal",  # Adapt to metal
    context_blend=0.3             # 30% metal influence
)
# Result: Complex progressive patterns with heavier hits,
#         tighter timing, and more aggressive feel
```

### Example 2: Jazz Song with Funk Sections

```python
# Swing verse - pure jazz
jazz_verse = generator.generate_pattern(
    genre="jazz",
    style="swing",
    section="verse"
)

# Funk chorus - adapted to jazz context
funk_chorus = generator.generate_pattern(
    genre="funk",
    style="classic",
    section="chorus",
    song_genre_context="jazz",   # Adapt to jazz
    context_blend=0.4             # 40% jazz influence
)
# Result: Funk groove with jazz swing feel,
#         more ghost notes, lighter touch
```

### Example 3: Variable Context Blending

```python
# Light blend for intro (ease listener in)
prog_intro = generator.generate_pattern(
    genre="metal",
    style="progressive",
    section="intro",
    song_genre_context="metal",
    context_blend=0.2  # Subtle metal influence
)

# Heavy blend for climax (full intensity)
prog_climax = generator.generate_pattern(
    genre="metal",
    style="progressive",
    section="chorus",
    song_genre_context="metal",
    context_blend=0.5  # Strong metal influence
)
```

---

## Benefits

### Musical Cohesion
- Multi-genre songs sound more unified
- Transitional sections feel more natural
- Maintains genre characteristics while fitting song context

### Creative Control
- Variable blend amounts (0.0-1.0) for fine-tuning
- Per-section customization
- Preserves ability to use pure genre patterns (blend=0.0)

### Backward Compatibility
- Optional parameters (defaults to no blending)
- Existing code continues to work unchanged
- No breaking changes to API

---

## Technical Considerations

### Performance
- Minimal overhead: profile lookup + parameter blending
- No additional pattern generation passes
- Profiles are static properties (no computation)

### Extensibility
- Easy to add new intensity dimensions
- Genre plugins can override default blending logic
- Custom profiles via configuration files (future)

### Testing Strategy
- Unit tests for profile blending calculations
- Integration tests for common blend scenarios
- A/B testing with musicians for "feel" validation
- Metrics: velocity distributions, timing variance, note density

---

## Open Questions

1. **Intensity Dimensions**: What other characteristics matter?
   - `groove`: Swing/shuffle feel
   - `space`: Silence vs. constant activity
   - `articulation`: Staccato vs. sustained

2. **Non-Linear Blending**: Should blending be linear interpolation or weighted curves?
   - Linear: `result = base + (target - base) * blend`
   - Exponential: More natural for human perception?

3. **Drummer Interaction**: How do drummer styles interact with context blending?
   - Apply drummer style before or after context blending?
   - Do drummers have their own context preferences?

4. **Tempo Adjustment**: Should context blending suggest tempo modifications?
   - Metal context might push progressive sections faster
   - Jazz context might slow funk sections

---

## Implementation Priority

**High Priority** (Core Feature):
- ✅ Intensity profiles for Metal, Rock, Jazz, Funk
- ✅ Basic context blending (velocity, density adjustments)
- ✅ API integration with optional parameters

**Medium Priority** (Refinement):
- Section-aware blending strategies
- Advanced timing/articulation adaptations
- Per-instrument blend customization

**Low Priority** (Future Enhancement):
- Multi-context blending (blend 2+ genres)
- ML-based profile learning from user feedback
- Configuration file-based custom profiles
- Real-time preview of different blend amounts

---

## Estimated Effort

- **Phase 1 (Core)**: 4-6 hours
  - Add intensity profiles: 1 hour
  - Implement blending logic: 2 hours
  - API integration: 1 hour
  - Testing: 2 hours

- **Phase 2 (Profiles)**: 2-3 hours per genre
  - Research genre characteristics
  - Define profile values
  - Test and validate feel

- **Phase 3 (Advanced)**: 8-12 hours
  - Complex blending strategies
  - Section/instrument-specific logic
  - Comprehensive testing

**Total MVP**: ~10-12 hours for core feature + 4 genre profiles
