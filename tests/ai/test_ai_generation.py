#!/usr/bin/env python3
"""Test AI-powered MIDI generation with natural language."""

import asyncio
import sys
from pathlib import Path

from midi_drums.ai import DrumGeneratorAI
from midi_drums.ai.logging_config import configure_logging

# Fix Windows console encoding
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")

# Configure logging to console only for testing
configure_logging(level="WARNING", log_to_file=False)


async def test_ai_generation():
    """Test AI-powered pattern generation."""
    print("=" * 70)
    print("Testing AI-Powered MIDI Generation")
    print("=" * 70)

    ai = DrumGeneratorAI()
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Test 1: Pydantic AI - Natural language pattern generation
    print("\n[1] Pydantic AI: 'aggressive metal breakdown with double bass'...")
    pattern1, response1 = await ai.generate_pattern_from_text(
        description="aggressive metal breakdown with double bass and blast beats",
        section="breakdown",
        tempo=180,
        bars=4,
    )
    print(f"✅ Generated: {pattern1.name}")
    print(f"   AI-detected genre: {response1.characteristics.genre}")
    print(f"   AI-detected style: {response1.characteristics.style}")
    print(
        f"   AI-detected intensity: {response1.characteristics.intensity:.2f}"
    )
    print(f"   Double bass: {response1.characteristics.use_double_bass}")
    print(f"   Ghost notes: {response1.characteristics.use_ghost_notes}")

    ai_file1 = output_dir / "ai_metal_breakdown.mid"
    ai.export_pattern(pattern1, str(ai_file1), tempo=180)
    print(f"   Exported: {ai_file1}")

    # Test 2: Pydantic AI - Funky groove
    print("\n[2] Pydantic AI: 'funky groove with ghost notes'...")
    pattern2, response2 = await ai.generate_pattern_from_text(
        description="funky groove with lots of ghost notes and syncopation",
        section="verse",
        tempo=100,
        bars=4,
    )
    print(f"✅ Generated: {pattern2.name}")
    print(f"   AI-detected genre: {response2.characteristics.genre}")
    print(f"   AI-detected style: {response2.characteristics.style}")
    print(f"   Syncopation: {response2.characteristics.use_syncopation}")
    print(f"   Primary cymbal: {response2.characteristics.primary_cymbal}")

    ai_file2 = output_dir / "ai_funky_groove.mid"
    ai.export_pattern(pattern2, str(ai_file2), tempo=100)
    print(f"   Exported: {ai_file2}")

    # Test 3: Pydantic AI - Jazz swing
    print("\n[3] Pydantic AI: 'smooth jazz swing with ride cymbal'...")
    pattern3, response3 = await ai.generate_pattern_from_text(
        description="smooth jazz swing with ride cymbal",
        section="verse",
        tempo=140,
        bars=4,
    )
    print(f"✅ Generated: {pattern3.name}")
    print(f"   AI-detected genre: {response3.characteristics.genre}")
    print(f"   AI-detected style: {response3.characteristics.style}")
    print(f"   Primary cymbal: {response3.characteristics.primary_cymbal}")

    ai_file3 = output_dir / "ai_jazz_swing.mid"
    ai.export_pattern(pattern3, str(ai_file3), tempo=140)
    print(f"   Exported: {ai_file3}")

    # Test 4: Quick convenience method
    print("\n[4] Quick API: Fast death metal generation...")
    quick_pattern = await ai.quick_pattern(
        "intense death metal with blast beats", tempo=200
    )
    print(f"✅ Generated: {quick_pattern.name}")

    ai_file4 = output_dir / "ai_quick_death_metal.mid"
    ai.export_pattern(quick_pattern, str(ai_file4), tempo=200)
    print(f"   Exported: {ai_file4}")

    # Summary
    print("\n" + "=" * 70)
    print("AI Generation Test Complete!")
    print("=" * 70)
    print(f"Output directory: {output_dir.absolute()}")
    print(f"AI-generated files: {len(list(output_dir.glob('ai_*.mid')))}")
    print("\nAI Capabilities Demonstrated:")
    print("  ✅ Natural language understanding")
    print("  ✅ Genre/style detection")
    print("  ✅ Intensity analysis")
    print("  ✅ Musical characteristic inference")
    print("  ✅ Type-safe pattern generation")


def test_langchain_agent():
    """Test Langchain agent composition (synchronous)."""
    print("\n" + "=" * 70)
    print("Testing Langchain Agent Composition")
    print("=" * 70)

    ai = DrumGeneratorAI()
    Path("output")

    # Test agent-based composition
    print("\n[5] Langchain Agent: Multi-step composition workflow...")
    result = ai.compose_with_agent(
        "Create a progressive metal song with verse and chorus patterns, "
        "then apply the Bonham drummer style to make it more dynamic"
    )

    print("✅ Agent Response:")
    print(f"   {result['output'][:200]}...")

    print("\n" + "=" * 70)
    print("Langchain Agent Test Complete!")
    print("=" * 70)


async def main():
    """Run all AI tests."""
    # Test Pydantic AI patterns
    await test_ai_generation()

    # Test Langchain agent
    test_langchain_agent()

    print("\n" + "=" * 70)
    print("All AI Tests Passed! ✅")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
