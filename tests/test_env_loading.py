"""Test script to verify .env loading without making API calls."""

from midi_drums.ai import AIBackendConfig, AIProvider

# Test loading from environment
config = AIBackendConfig.from_env()

print("=" * 60)
print("Environment Configuration Test")
print("=" * 60)
print(f"Provider: {config.provider.value}")
print(f"Model: {config.model}")
print(f"API Key present: {'Yes' if config.api_key else 'No'}")
if config.api_key and len(config.api_key) > 10:
    print(f"API Key (masked): {config.api_key[:7]}...")
else:
    print("API Key (masked): Not set")
print(f"Temperature: {config.temperature}")
print(f"Max Tokens: {config.max_tokens}")
print("=" * 60)

# Verify it's configured for OpenAI o3-mini
if config.provider == AIProvider.OPENAI:
    print("[OK] Provider correctly set to OpenAI")
else:
    print(f"[WARN] Provider is {config.provider.value}, expected openai")

if config.model == "o3-mini-2025-01-31":
    print("[OK] Model correctly set to o3-mini-2025-01-31")
else:
    print(f"[WARN] Model is {config.model}, expected o3-mini-2025-01-31")

if config.api_key and config.api_key != "your-openai-api-key-here":
    print("[OK] API key is configured")
else:
    print("[WARN] API key needs to be set in .env file")
    print("       Edit .env and replace 'your-openai-api-key-here'")
    print("       with your actual OpenAI API key")

print("=" * 60)
print("\nTo use AI features:")
print("1. Get an OpenAI API key from: https://platform.openai.com/api-keys")
print("2. Edit .env file and replace 'your-openai-api-key-here'")
print("3. Run AI generation scripts")
print("\nExample usage:")
print("  from midi_drums.ai import DrumGeneratorAI")
print("  ai = DrumGeneratorAI()")
print("  pattern, info = await ai.generate_pattern_from_text('heavy metal')")
