"""Shared pytest fixtures and configuration for MIDI Drums tests."""


import pytest

from midi_drums.ai import AIBackendConfig, DrumGeneratorAI
from midi_drums.api.python_api import DrumGeneratorAPI
from midi_drums.core.engine import DrumGenerator


# Test output directory
@pytest.fixture(scope="session")
def test_output_dir(tmp_path_factory):
    """Create temporary output directory for test files."""
    return tmp_path_factory.mktemp("test_output")


# Core fixtures
@pytest.fixture
def drum_generator():
    """Provide DrumGenerator instance."""
    return DrumGenerator()


@pytest.fixture
def drum_api():
    """Provide DrumGeneratorAPI instance."""
    return DrumGeneratorAPI()


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


# Markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "ai: AI tests (requires API key)")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "requires_api: Tests requiring API access")


# Skip AI tests if no API key
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip AI tests without API key."""
    skip_ai = pytest.mark.skip(reason="AI tests require API key (set ANTHROPIC_API_KEY or configure AI_PROVIDER)")

    for item in items:
        # Only check explicit markers, not directory names
        if "requires_api" in item.keywords:
            # Check if API key is available
            config_obj = AIBackendConfig.from_env()
            if not config_obj.api_key:
                item.add_marker(skip_ai)
