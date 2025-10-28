"""
AI Backend Abstraction Layer.

Provides unified interface for multiple LLM providers (Anthropic, OpenAI, etc.)
configured via environment variables for maximum flexibility.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field

# Load .env file if it exists
dotenv_path = Path(__file__).parent.parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    logger.debug(f"Loaded environment variables from {dotenv_path}")


class AIProvider(str, Enum):
    """Supported AI providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"
    COHERE = "cohere"


class AIBackendConfig(BaseModel):
    """Configuration for AI backend with environment variable support."""

    provider: AIProvider = Field(
        default=AIProvider.ANTHROPIC,
        description="AI provider to use (anthropic, openai, groq, cohere)",
    )
    model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model identifier for the provider",
    )
    api_key: str | None = Field(
        default=None, description="API key for authentication"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int = Field(default=4096, ge=1, description="Max output tokens")

    @classmethod
    def from_env(cls) -> AIBackendConfig:
        """
        Create configuration from environment variables.

        Environment Variables:
            AI_PROVIDER: Provider name (anthropic, openai, groq, cohere)
            AI_MODEL: Model identifier
            AI_TEMPERATURE: Temperature (0.0-2.0)
            AI_MAX_TOKENS: Maximum tokens
            ANTHROPIC_API_KEY: Anthropic API key
            OPENAI_API_KEY: OpenAI API key
            GROQ_API_KEY: Groq API key
            COHERE_API_KEY: Cohere API key

        Returns:
            Configured AIBackendConfig instance
        """
        provider_str = os.getenv("AI_PROVIDER", "anthropic").lower()
        try:
            provider = AIProvider(provider_str)
        except ValueError:
            logger.warning(
                f"Invalid AI_PROVIDER '{provider_str}', defaulting to anthropic"
            )
            provider = AIProvider.ANTHROPIC

        # Get API key based on provider
        api_key = os.getenv(f"{provider.value.upper()}_API_KEY")

        # Default models per provider
        default_models = {
            AIProvider.ANTHROPIC: "claude-sonnet-4-20250514",
            AIProvider.OPENAI: "gpt-4o",
            AIProvider.GROQ: "llama-3.3-70b-versatile",
            AIProvider.COHERE: "command-r-plus",
        }

        model = os.getenv("AI_MODEL", default_models[provider])
        temperature = float(os.getenv("AI_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("AI_MAX_TOKENS", "4096"))

        config = cls(
            provider=provider,
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(
            f"AI Backend configured: {config.provider.value}/{config.model} "
            f"(temp={config.temperature}, max_tokens={config.max_tokens})"
        )
        if not config.api_key:
            provider_key = f"{config.provider.value.upper()}_API_KEY"
            logger.warning(
                f"No API key found for {config.provider.value}. "
                f"Set {provider_key} environment variable."
            )

        return config


class AIBackendFactory:
    """Factory for creating AI backend instances."""

    @staticmethod
    def create_pydantic_model(config: AIBackendConfig | None = None) -> Any:
        """
        Create Pydantic AI model instance.

        Args:
            config: Backend configuration (uses env vars if None)

        Returns:
            Configured Pydantic AI model
        """
        if config is None:
            config = AIBackendConfig.from_env()

        if config.provider == AIProvider.ANTHROPIC:
            from pydantic_ai.models.anthropic import AnthropicModel

            logger.debug(f"Creating Anthropic model: {config.model}")
            return AnthropicModel(
                config.model,
                api_key=config.api_key,
            )

        elif config.provider == AIProvider.OPENAI:
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.openai import OpenAIProvider

            logger.debug(f"Creating OpenAI model: {config.model}")
            provider = OpenAIProvider(api_key=config.api_key)
            return OpenAIModel(config.model, provider=provider)

        elif config.provider == AIProvider.GROQ:
            from pydantic_ai.models.groq import GroqModel

            logger.debug(f"Creating Groq model: {config.model}")
            return GroqModel(
                config.model,
                api_key=config.api_key,
            )

        else:
            raise ValueError(
                f"Unsupported provider for Pydantic AI: {config.provider}"
            )

    @staticmethod
    def create_langchain_llm(config: AIBackendConfig | None = None) -> Any:
        """
        Create Langchain LLM instance using init_chat_model.

        Args:
            config: Backend configuration (uses env vars if None)

        Returns:
            Configured Langchain chat model
        """
        if config is None:
            config = AIBackendConfig.from_env()

        # Use Langchain's universal init_chat_model
        # Set API key in environment if provided
        import os

        from langchain.chat_models import init_chat_model

        if config.api_key:
            env_key = f"{config.provider.value.upper()}_API_KEY"
            os.environ[env_key] = config.api_key

        # Format: "provider:model"
        model_string = f"{config.provider.value}:{config.model}"

        logger.debug(f"Creating Langchain model: {model_string}")
        return init_chat_model(
            model_string,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )


def get_backend_config() -> AIBackendConfig:
    """
    Get AI backend configuration from environment.

    Convenience function for quick access to backend config.

    Returns:
        AIBackendConfig instance
    """
    return AIBackendConfig.from_env()
