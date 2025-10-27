"""AI Integration Examples for MIDI Drums Generator.

This module demonstrates how to use the AI-powered features including:
- Natural language pattern generation with Pydantic AI
- Agent-based composition with Langchain
- Type-safe structured outputs
- Intelligent song composition

Prerequisites:
    - Install AI dependencies: uv sync --group ai
    - Set environment variable: ANTHROPIC_API_KEY=your-key
    - Or pass api_key directly to DrumGeneratorAI()
"""

import asyncio
import os

from midi_drums.ai import DrumGeneratorAI

# ============================================================================
# Example 1: Type-Safe Pattern Generation (Pydantic AI)
# ============================================================================


async def example_pydantic_pattern_generation():
    """Generate patterns using type-safe Pydantic AI approach."""
    print("\n" + "=" * 70)
    print("Example 1: Type-Safe Pattern Generation (Pydantic AI)")
    print("=" * 70)

    # Initialize AI generator (uses ANTHROPIC_API_KEY env var)
    ai = DrumGeneratorAI()

    # Example 1a: Aggressive metal breakdown
    print("\n[1a] Generating aggressive metal breakdown...")
    pattern1, response1 = await ai.generate_pattern_from_text(
        description=(
            "aggressive metal breakdown with double bass and blast beats"
        ),
        section="breakdown",
        tempo=180,
        bars=4,
    )

    print(f"\n✓ Pattern: {pattern1.name}")
    print(f"  Genre: {response1.characteristics.genre}")
    print(f"  Style: {response1.characteristics.style}")
    print(f"  Intensity: {response1.characteristics.intensity:.2f}")
    print(f"  Double Bass: {response1.characteristics.use_double_bass}")
    print(f"  Templates Used: {', '.join(response1.templates_used)}")
    print(f"  AI Confidence: {response1.confidence:.2f}")
    print(f"  Reasoning: {response1.characteristics.reasoning}")
    print(f"  Suggestions: {response1.suggestions}")

    # Export to MIDI
    ai.export_pattern(pattern1, "output/ai_metal_breakdown.mid", tempo=180)
    print("  Exported: output/ai_metal_breakdown.mid")

    # Example 1b: Funky groove with ghost notes
    print("\n[1b] Generating funky groove...")
    pattern2, response2 = await ai.generate_pattern_from_text(
        description="funky groove with ghost notes and syncopation",
        section="verse",
        tempo=110,
        bars=4,
        drummer_style="chambers",  # Apply Dennis Chambers style
    )

    print(f"\n✓ Pattern: {pattern2.name}")
    print(f"  Genre: {response2.characteristics.genre}")
    print(f"  Style: {response2.characteristics.style}")
    print(f"  Ghost Notes: {response2.characteristics.use_ghost_notes}")
    print(f"  Syncopation: {response2.characteristics.use_syncopation}")
    print(f"  Modifications: {', '.join(response2.modifications_applied)}")

    ai.export_pattern(pattern2, "output/ai_funk_groove.mid", tempo=110)
    print("  Exported: output/ai_funk_groove.mid")

    # Example 1c: Jazz swing with Weckl style
    print("\n[1c] Generating jazz swing pattern...")
    pattern3, response3 = await ai.generate_pattern_from_text(
        description="smooth jazz swing pattern with ride cymbal",
        section="verse",
        tempo=120,
        bars=8,
        drummer_style="weckl",
    )

    print(f"\n✓ Pattern: {pattern3.name}")
    print(f"  Genre: {response3.characteristics.genre}")
    print(f"  Primary Cymbal: {response3.characteristics.primary_cymbal}")
    print(f"  Beats: {len(pattern3.beats)}")

    ai.export_pattern(pattern3, "output/ai_jazz_swing.mid", tempo=120)
    print("  Exported: output/ai_jazz_swing.mid")


# ============================================================================
# Example 2: Agent-Based Composition (Langchain)
# ============================================================================


def example_agent_composition():
    """Compose patterns and songs using intelligent Langchain agent."""
    print("\n" + "=" * 70)
    print("Example 2: Agent-Based Composition (Langchain)")
    print("=" * 70)

    ai = DrumGeneratorAI()

    # Example 2a: Simple pattern request
    print("\n[2a] Agent: Create a death metal breakdown...")
    result1 = ai.compose_with_agent(
        "create an aggressive death metal breakdown with double bass"
    )
    print("\n✓ Agent Response:")
    print(f"  {result1['output']}")

    # Example 2b: Pattern with drummer style
    print("\n[2b] Agent: Create pattern with Bonham style...")
    result2 = ai.compose_with_agent(
        "create a classic rock verse pattern and then apply John Bonham's "
        "drumming style to it"
    )
    print("\n✓ Agent Response:")
    print(f"  {result2['output']}")

    # Example 2c: Complete song composition
    print("\n[2c] Agent: Compose a complete song...")
    result3 = ai.compose_with_agent(
        "create a progressive metal song at 140 BPM with this structure: "
        "intro, verse, chorus, verse, chorus, bridge, breakdown, chorus, outro"
    )
    print("\n✓ Agent Response:")
    print(f"  {result3['output']}")

    # Example 2d: Query available options
    print("\n[2d] Agent: What drummers are available?")
    result4 = ai.compose_with_agent(
        "what drummer styles are available and what are they known for?"
    )
    print("\n✓ Agent Response:")
    print(f"  {result4['output']}")


# ============================================================================
# Example 3: Quick Convenience Methods
# ============================================================================


async def example_quick_methods():
    """Use quick convenience methods for rapid generation."""
    print("\n" + "=" * 70)
    print("Example 3: Quick Convenience Methods")
    print("=" * 70)

    ai = DrumGeneratorAI()

    # Quick pattern generation with immediate export
    print("\n[3a] Quick pattern generation...")
    pattern = await ai.quick_pattern(
        "heavy thrash metal with fast double bass",
        output_path="output/ai_quick_thrash.mid",
    )
    print(f"✓ Generated and exported: {pattern.name}")
    print("  File: output/ai_quick_thrash.mid")

    # Quick song composition
    print("\n[3b] Quick song composition...")
    song_id = ai.quick_song(
        "energetic punk rock song with fast tempo",
        output_path="output/ai_quick_punk_song.mid",
    )
    print(f"✓ Generated and exported song: {song_id}")
    print("  File: output/ai_quick_punk_song.mid")


# ============================================================================
# Example 4: Combining Both Approaches
# ============================================================================


async def example_combined_workflow():
    """Demonstrate combining Pydantic AI and Langchain approaches."""
    print("\n" + "=" * 70)
    print("Example 4: Combined Workflow")
    print("=" * 70)

    ai = DrumGeneratorAI()

    # Step 1: Use Pydantic AI for type-safe pattern generation
    print("\n[Step 1] Generate base pattern with Pydantic AI...")
    pattern, response = await ai.generate_pattern_from_text(
        "progressive rock verse with complex rhythms",
        tempo=145,
        bars=4,
    )
    print(f"✓ Generated: {pattern.name}")
    print(f"  Genre: {response.characteristics.genre}")
    print(f"  Style: {response.characteristics.style}")

    # Step 2: Use agent for creative suggestions
    print("\n[Step 2] Ask agent for creative variations...")
    result = ai.compose_with_agent(
        f"I have a {response.characteristics.genre} "
        f"{response.characteristics.style} pattern. "
        "What drummer style would work well and why?"
    )
    print("✓ Agent Suggestion:")
    print(f"  {result['output']}")

    # Step 3: Export final result
    print("\n[Step 3] Export final pattern...")
    ai.export_pattern(pattern, "output/ai_combined_progressive.mid", tempo=145)
    print("✓ Exported: output/ai_combined_progressive.mid")


# ============================================================================
# Example 5: Batch Generation
# ============================================================================


async def example_batch_generation():
    """Generate multiple patterns in batch for comparison."""
    print("\n" + "=" * 70)
    print("Example 5: Batch Generation")
    print("=" * 70)

    ai = DrumGeneratorAI()

    # Generate multiple variations of the same concept
    descriptions = [
        "aggressive metal breakdown",
        "heavy metal breakdown with blast beats",
        "slow doom metal breakdown with crushing weight",
        "technical progressive metal breakdown with odd time",
    ]

    print("\n[Batch] Generating 4 metal breakdown variations...")

    for i, desc in enumerate(descriptions, 1):
        pattern, response = await ai.generate_pattern_from_text(
            description=desc,
            section="breakdown",
            tempo=180,
            bars=4,
        )

        filename = f"output/ai_breakdown_variant_{i}.mid"
        ai.export_pattern(pattern, filename, tempo=180)

        print(f"\n✓ Variant {i}: {desc}")
        print(f"  Style: {response.characteristics.style}")
        print(f"  Intensity: {response.characteristics.intensity:.2f}")
        print(f"  File: {filename}")


# ============================================================================
# Example 6: Interactive Pattern Evolution
# ============================================================================


def example_interactive_evolution():
    """Show interactive pattern refinement using agent."""
    print("\n" + "=" * 70)
    print("Example 6: Interactive Pattern Evolution")
    print("=" * 70)

    ai = DrumGeneratorAI()

    # Start with a base request
    print("\n[Step 1] Initial pattern request...")
    result1 = ai.compose_with_agent("create a metal verse pattern")
    print(f"✓ {result1['output']}")

    # Refine based on initial result
    print("\n[Step 2] Request modification...")
    result2 = ai.compose_with_agent(
        "make it more aggressive and add double bass pedal patterns"
    )
    print(f"✓ {result2['output']}")

    # Apply drummer style
    print("\n[Step 3] Apply drummer style...")
    result3 = ai.compose_with_agent(
        "apply Gene Hoglan's drumming style to create mechanical precision"
    )
    print(f"✓ {result3['output']}")


# ============================================================================
# Main Runner
# ============================================================================


async def run_all_examples():
    """Run all AI integration examples."""
    print("\n" + "=" * 70)
    print("MIDI Drums Generator - AI Integration Examples")
    print("=" * 70)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠ Warning: ANTHROPIC_API_KEY not set!")
        print("  Set it with: export ANTHROPIC_API_KEY='your-key'")
        print("  Or pass api_key to DrumGeneratorAI(api_key='your-key')")
        return

    # Create output directory
    os.makedirs("output", exist_ok=True)

    # Run examples
    await example_pydantic_pattern_generation()
    example_agent_composition()
    await example_quick_methods()
    await example_combined_workflow()
    await example_batch_generation()
    example_interactive_evolution()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print("\nGenerated MIDI files are in the 'output/' directory.")
    print("Load them in your DAW or EZDrummer 3 to hear the results!")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(run_all_examples())
