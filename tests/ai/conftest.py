"""AI-specific pytest fixtures and configuration.

These fixtures require AI dependencies (pydantic, langchain, etc.)
which are only installed when the 'ai' dependency group is present.
"""

import pytest

from midi_drums.ai import AIBackendConfig, DrumGeneratorAI


# AI fixtures
@pytest.fixture
def ai_backend_config():
    """Provide AI backend configuration from environment."""
    return AIBackendConfig.from_env()


@pytest.fixture
def has_ai_api_key(ai_backend_config):
    """Check if AI API key is available."""
    return ai_backend_config.api_key is not None


@pytest.fixture
def drum_ai(ai_backend_config):
    """Provide DrumGeneratorAI instance with backend config."""
    return DrumGeneratorAI(backend_config=ai_backend_config)


# Skip AI tests if no API key
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip AI tests without API key."""
    skip_ai = pytest.mark.skip(
        reason="AI tests require API key (set ANTHROPIC_API_KEY or configure AI_PROVIDER)"
    )

    for item in items:
        # Only check explicit markers, not directory names
        if "requires_api" in item.keywords:
            # Check if API key is available
            config_obj = AIBackendConfig.from_env()
            if not config_obj.api_key:
                item.add_marker(skip_ai)
