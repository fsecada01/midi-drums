"""Langchain agents for AI-powered drum composition."""

from midi_drums.ai.agents.pattern_agent_v2 import PatternCompositionAgentV2

# Alias for backwards compatibility
PatternCompositionAgent = PatternCompositionAgentV2

__all__ = ["PatternCompositionAgent", "PatternCompositionAgentV2"]
