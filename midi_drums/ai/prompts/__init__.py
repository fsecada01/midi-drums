"""
AI Prompt Templates for MIDI Drums Generator.

This module provides structured prompts for various AI-powered generation tasks.
Prompts are organized by task type and support multi-model routing based on complexity.

Usage:
    from midi_drums.ai.prompts import (
        PATTERN_ANALYSIS_PROMPT,
        SONG_COMPOSITION_PROMPT,
        MODEL_ROUTING_CONFIG,
        get_prompt_for_task,
        get_model_tier,
    )
"""

from pathlib import Path

# Prompt directory
PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt from a markdown file."""
    prompt_file = PROMPTS_DIR / f"{name}.md"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Prompt file not found: {prompt_file}")


# Model tier definitions for cost optimization
MODEL_TIERS = {
    "fast": {
        "anthropic": "claude-3-5-haiku-20241022",
        "openai": "gpt-4o-mini",
        "groq": "llama-3.1-8b-instant",
        "cohere": "command-light",
        "max_tokens": 256,
        "temperature": 0.3,
    },
    "balanced": {
        "anthropic": "claude-sonnet-4-20250514",
        "openai": "gpt-4o",
        "groq": "llama-3.3-70b-versatile",
        "cohere": "command-r",
        "max_tokens": 1024,
        "temperature": 0.7,
    },
    "advanced": {
        "anthropic": "claude-sonnet-4-20250514",
        "openai": "gpt-4o",
        "groq": "llama-3.3-70b-versatile",
        "cohere": "command-r-plus",
        "max_tokens": 2048,
        "temperature": 0.8,
    },
    "expert": {
        "anthropic": "claude-opus-4-5-20251101",
        "openai": "gpt-4o",
        "groq": "llama-3.3-70b-versatile",
        "cohere": "command-r-plus",
        "max_tokens": 4096,
        "temperature": 0.7,
    },
}

# Task to model tier routing
TASK_ROUTING = {
    # Fast tier - simple classification and validation
    "classify_intent": "fast",
    "extract_tempo": "fast",
    "validate_genre": "fast",
    "check_drummer_compatibility": "fast",
    "parse_section_type": "fast",
    # Balanced tier - standard generation tasks
    "analyze_pattern_description": "balanced",
    "infer_characteristics": "balanced",
    "select_templates": "balanced",
    "map_drummer_style": "balanced",
    "generate_single_pattern": "balanced",
    "suggest_modifications": "balanced",
    # Advanced tier - complex composition
    "compose_song_structure": "advanced",
    "create_pattern_variations": "advanced",
    "generate_fill_suggestions": "advanced",
    "multi_section_composition": "advanced",
    "style_blending": "advanced",
    # Expert tier - complex analysis
    "analyze_audio_file": "expert",
    "evolve_pattern_sequence": "expert",
    "blend_genre_styles": "expert",
    "complex_polyrhythm_generation": "expert",
    "musical_theory_application": "expert",
}


def get_model_tier(task: str) -> str:
    """Get the appropriate model tier for a task."""
    return TASK_ROUTING.get(task, "balanced")


def get_model_config(task: str, provider: str = "anthropic") -> dict:
    """Get model configuration for a task and provider."""
    tier = get_model_tier(task)
    tier_config = MODEL_TIERS[tier]
    return {
        "model": tier_config.get(provider, tier_config["anthropic"]),
        "max_tokens": tier_config["max_tokens"],
        "temperature": tier_config["temperature"],
        "tier": tier,
    }


def get_prompt_for_task(task: str) -> str:
    """Load the appropriate prompt for a task."""
    prompt_mapping = {
        "analyze_pattern_description": "pattern_analysis",
        "infer_characteristics": "pattern_analysis",
        "generate_single_pattern": "pattern_generation",
        "compose_song_structure": "song_composition",
        "multi_section_composition": "song_composition",
        "analyze_audio_file": "audio_analysis",
        "classify_intent": "intent_classification",
    }
    prompt_name = prompt_mapping.get(task, "pattern_generation")
    return load_prompt(prompt_name)


__all__ = [
    "load_prompt",
    "MODEL_TIERS",
    "TASK_ROUTING",
    "get_model_tier",
    "get_model_config",
    "get_prompt_for_task",
]
