"""Test AI-powered drum generation with natural language prompt."""

import asyncio

from loguru import logger

from midi_drums.ai import DrumGeneratorAI


async def main():
    """Generate doom metal/blues drum track using AI."""

    # Initialize AI generator (automatically loads from .env)
    logger.info("Initializing DrumGeneratorAI with OpenAI o3-mini...")
    ai = DrumGeneratorAI()

    # User's prompt for doom metal/bluesy track
    prompt = """
    Please create a MIDI drum track with EZDrummer3's key map for a doom
    metal/bluesy song, in the vein of Crowbar and Sleep. The idea is to play
    a three-chord progression with two dominant chords with an A minor root.
    The A chord would also feature mixing of the major and minor thirds, a
    traditional blues practice. I'd like to feature drum styles by Dennis
    Chambers, Jeff Porcaro and Jason Roeder.
    """

    logger.info("Generating pattern from natural language prompt...")
    logger.info(f"Prompt: {prompt.strip()}")

    try:
        # Generate pattern using Pydantic AI
        pattern, response = await ai.generate_pattern_from_text(
            prompt,
            section="verse",
            tempo=70,  # Doom metal tempo (slow and heavy)
            bars=4,
            complexity=0.7,
        )

        logger.success("Pattern generated successfully!")
        logger.info("=" * 60)
        logger.info("AI Analysis Results:")
        logger.info("=" * 60)
        logger.info(f"Genre: {response.characteristics.genre}")
        logger.info(f"Style: {response.characteristics.style}")
        logger.info(f"Intensity: {response.characteristics.intensity}")
        logger.info(f"Double Bass: {response.characteristics.use_double_bass}")
        logger.info(f"Confidence: {response.confidence}")
        logger.info(f"Pattern Name: {pattern.name}")
        logger.info(f"Total Beats: {len(pattern.beats)}")

        # Export to MIDI
        output_file = "doom_blues_ai_generated.mid"
        ai.export_pattern(pattern, output_file, tempo=70)
        logger.success(f"Exported to: {output_file}")

        # Now let's try the agent-based approach for multi-drummer styling
        logger.info("\n" + "=" * 60)
        logger.info("Using Langchain Agent for Multi-Drummer Composition")
        logger.info("=" * 60)

        agent_prompt = """
        Create a doom metal song with the following characteristics:
        - Slow, heavy tempo (around 70 BPM)
        - Bluesy feel with emphasis on groove
        - Start with a verse pattern in doom metal style
        - Then apply Jason Roeder's atmospheric, minimal style
        - Add Jeff Porcaro's ghost notes and shuffle feel
        - Finally, enhance with Dennis Chambers' pocket and groove

        Generate patterns and apply all three drummer styles in sequence.
        """

        logger.info("Sending request to agent...")
        result = ai.compose_with_agent(agent_prompt)

        logger.success("Agent composition complete!")
        logger.info("\nAgent Response:")
        logger.info("=" * 60)
        logger.info(result["output"])
        logger.info("=" * 60)

        if result.get("pattern_cache"):
            logger.info(f"\nGenerated Patterns: {result['pattern_cache']}")

        if result.get("song_cache"):
            logger.info(f"Generated Songs: {result['song_cache']}")

    except Exception as e:
        logger.error(f"Error during generation: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
