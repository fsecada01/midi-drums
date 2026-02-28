"""Shared pytest fixtures and configuration for MIDI Drums tests."""

import pytest

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


# Markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "ai: AI tests (requires API key)")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line(
        "markers", "requires_api: Tests requiring API access"
    )
