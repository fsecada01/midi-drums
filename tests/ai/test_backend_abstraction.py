"""Test AI backend abstraction layer."""

import pytest

from midi_drums.ai.backends import AIBackendConfig, AIBackendFactory, AIProvider


@pytest.mark.unit
class TestAIBackendConfig:
    """Test AI backend configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = AIBackendConfig()
        assert config.provider == AIProvider.ANTHROPIC
        assert config.model == "claude-sonnet-4-20250514"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096

    def test_custom_config(self):
        """Test custom configuration."""
        config = AIBackendConfig(
            provider=AIProvider.OPENAI,
            model="gpt-4o",
            api_key="test-key",
            temperature=0.5,
            max_tokens=2048,
        )
        assert config.provider == AIProvider.OPENAI
        assert config.model == "gpt-4o"
        assert config.api_key == "test-key"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048

    def test_from_env_default(self, monkeypatch):
        """Test configuration from environment with defaults."""
        # Clear any existing API keys
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("AI_PROVIDER", raising=False)

        config = AIBackendConfig.from_env()
        assert config.provider == AIProvider.ANTHROPIC
        assert config.model == "claude-sonnet-4-20250514"

    def test_from_env_custom_provider(self, monkeypatch):
        """Test configuration with custom provider."""
        monkeypatch.setenv("AI_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

        config = AIBackendConfig.from_env()
        assert config.provider == AIProvider.OPENAI
        assert config.api_key == "test-openai-key"
        assert config.model == "gpt-4o"  # Default OpenAI model

    def test_from_env_custom_model(self, monkeypatch):
        """Test configuration with custom model."""
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        monkeypatch.setenv("AI_MODEL", "claude-opus-4-20250514")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        config = AIBackendConfig.from_env()
        assert config.model == "claude-opus-4-20250514"
        assert config.api_key == "test-key"

    def test_from_env_temperature(self, monkeypatch):
        """Test configuration with custom temperature."""
        monkeypatch.setenv("AI_TEMPERATURE", "0.9")

        config = AIBackendConfig.from_env()
        assert config.temperature == 0.9

    def test_from_env_max_tokens(self, monkeypatch):
        """Test configuration with custom max tokens."""
        monkeypatch.setenv("AI_MAX_TOKENS", "8192")

        config = AIBackendConfig.from_env()
        assert config.max_tokens == 8192

    def test_invalid_provider_fallback(self, monkeypatch):
        """Test fallback to default on invalid provider."""
        monkeypatch.setenv("AI_PROVIDER", "invalid_provider")

        config = AIBackendConfig.from_env()
        assert config.provider == AIProvider.ANTHROPIC  # Falls back to default


@pytest.mark.unit
class TestAIBackendFactory:
    """Test AI backend factory."""

    @pytest.mark.ai
    @pytest.mark.requires_api
    def test_create_anthropic_pydantic_model(self):
        """Test creating Anthropic Pydantic AI model."""
        config = AIBackendConfig(
            provider=AIProvider.ANTHROPIC, model="claude-sonnet-4-20250514"
        )
        model = AIBackendFactory.create_pydantic_model(config)
        assert model is not None
        # Note: Can't test much without making actual API calls

    @pytest.mark.ai
    def test_create_anthropic_langchain_llm(self):
        """Test creating Anthropic Langchain LLM."""
        config = AIBackendConfig(
            provider=AIProvider.ANTHROPIC,
            model="claude-sonnet-4-20250514",
            temperature=0.8,
        )
        llm = AIBackendFactory.create_langchain_llm(config)
        assert llm is not None
        assert llm.temperature == 0.8

    def test_unsupported_provider_pydantic(self):
        """Test error on unsupported Pydantic AI provider."""
        config = AIBackendConfig(
            provider=AIProvider.COHERE, model="command-r-plus"
        )
        with pytest.raises(ValueError, match="Unsupported provider"):
            AIBackendFactory.create_pydantic_model(config)

    def test_unsupported_provider_langchain(self):
        """Test error on unsupported Langchain provider."""
        config = AIBackendConfig(
            provider=AIProvider.COHERE, model="command-r-plus"
        )
        with pytest.raises(ValueError, match="Unsupported provider"):
            AIBackendFactory.create_langchain_llm(config)


class TestProviderSupport:
    """Test provider support matrix."""

    def test_supported_pydantic_providers(self):
        """Test which providers are supported for Pydantic AI."""
        supported = [AIProvider.ANTHROPIC, AIProvider.OPENAI, AIProvider.GROQ]

        for provider in supported:
            config = AIBackendConfig(provider=provider, model="test-model")
            # Should not raise
            try:
                AIBackendFactory.create_pydantic_model(config)
            except ValueError:
                pytest.fail(f"{provider} should be supported for Pydantic AI")
            except Exception:
                # Other errors (missing API key, etc.) are okay
                pass

    def test_supported_langchain_providers(self):
        """Test which providers are supported for Langchain."""
        supported = [AIProvider.ANTHROPIC, AIProvider.OPENAI, AIProvider.GROQ]

        for provider in supported:
            config = AIBackendConfig(provider=provider, model="test-model")
            # Should not raise
            try:
                AIBackendFactory.create_langchain_llm(config)
            except ValueError:
                pytest.fail(f"{provider} should be supported for Langchain")
            except Exception:
                # Other errors (missing API key, etc.) are okay
                pass
