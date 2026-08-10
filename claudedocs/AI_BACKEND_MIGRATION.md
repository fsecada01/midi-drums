# AI Backend Abstraction Migration

## Overview

Successfully implemented AI backend abstraction layer for provider-agnostic AI integration.

## ✅ Completed

### 1. Backend Abstraction Layer (`midi_drums/ai/backends.py`)
- **AIProvider enum**: Supports Anthropic, OpenAI, Groq, Cohere
- **AIBackendConfig**: Pydantic model for type-safe configuration
- **Environment Variable Support**:
  - `AI_PROVIDER`: Provider selection (default: anthropic)
  - `AI_MODEL`: Model selection (provider-specific defaults)
  - `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `COHERE_API_KEY`
  - `AI_TEMPERATURE`, `AI_MAX_TOKENS`: Generation parameters
- **AIBackendFactory**: Creates Pydantic AI and Langchain instances

### 2. Updated AI Modules
- **PydanticPatternGenerator**: Now uses AIBackendFactory
- **DrumGeneratorAI**: Supports backend_config parameter
- Backward compatible with legacy api_key parameter

### 3. Test Infrastructure
- Created `tests/` directory structure (unit, integration, ai)
- Moved 17 test files from root to organized directories
- Created `pytest.ini` with comprehensive configuration:
  - Coverage reporting (70% threshold)
  - Parallel execution (`pytest-xdist`)
  - Async support (`pytest-asyncio`)
  - Test markers (unit, integration, ai, slow, requires_api)
- Created `tests/conftest.py` with shared fixtures
- Added `test_backend_abstraction.py` with comprehensive backend tests

### 4. Dependency Updates
- Added `pytest-asyncio>=0.24.0` for async test support
- Added `pytest-xdist>=3.6.1` for parallel test execution
- Modern Hatchling build backend (replaced setuptools)

## 🚧 In Progress

### Langchain 1.0 Migration
Langchain 1.0 introduced breaking API changes:
- `langchain.agents.AgentExecutor` → Moved/removed
- `create_tool_calling_agent` → Replaced with `create_react_agent`
- Import paths changed (`langchain.tools` → `langchain_core.tools`)

**Status**: Temporarily disabled Langchain agent features
**Files affected**:
- `midi_drums/ai/agents/pattern_agent.py`
- `midi_drums/ai/ai_api.py` (agent methods commented out)
- `midi_drums/ai/__init__.py` (PatternCompositionAgent import disabled)

**Next steps**:
1. Review [Langchain 1.0 migration guide](https://python.langchain.com/docs/versions/migrating_chains/)
2. Update PatternCompositionAgent to use new API
3. Re-enable agent methods in DrumGeneratorAI
4. Add agent tests

## Usage Examples

### Environment Variable Configuration
```bash
# Use Anthropic (default)
export ANTHROPIC_API_KEY="sk-ant-..."
export AI_MODEL="claude-sonnet-5"

# Switch to OpenAI
export AI_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."
export AI_MODEL="gpt-4o"

# Switch to Groq
export AI_PROVIDER="groq"
export GROQ_API_KEY="gsk_..."
export AI_MODEL="llama-3.3-70b-versatile"
```

### Programmatic Configuration
```python
from midi_drums.ai import DrumGeneratorAI, AIBackendConfig, AIProvider

# Use environment variables (recommended)
ai = DrumGeneratorAI()

# Or configure programmatically
config = AIBackendConfig(
    provider=AIProvider.OPENAI,
    model="gpt-4o",
    api_key="sk-...",
    temperature=0.7
)
ai = DrumGeneratorAI(backend_config=config)

# Generate pattern
pattern, response = await ai.generate_pattern_from_text(
    "aggressive metal breakdown with double bass"
)
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m ai           # AI tests (requires API key)

# Run with coverage
pytest --cov=midi_drums --cov-report=html

# Run in parallel
pytest -n auto

# Skip AI tests if no API key
pytest -m "not ai"
```

## Architecture

```
midi_drums/ai/
├── backends.py              # ✅ Backend abstraction layer
├── pattern_generator.py     # ✅ Updated to use backends
├── ai_api.py                # ✅ Updated (agent methods disabled)
├── schemas.py               # ✅ Pydantic models
├── logging_config.py        # ✅ Production logging
├── agents/
│   └── pattern_agent.py     # 🚧 Needs Langchain 1.0 update
└── __init__.py              # ✅ Exports backend classes

tests/
├── conftest.py              # ✅ Shared fixtures
├── unit/                    # ✅ 8 unit test files
├── integration/             # ✅ 6 integration test files
└── ai/                      # ✅ 3 AI test files
    └── test_backend_abstraction.py  # ✅ Backend tests
```

## Benefits

1. **Provider Flexibility**: Easy switching between AI providers
2. **Environment-Driven**: Production-ready configuration via env vars
3. **Type Safety**: Full Pydantic validation
4. **Backward Compatible**: Legacy api_key parameter still works
5. **Test Coverage**: Comprehensive test infrastructure
6. **Production Ready**: Proper logging, error handling, validation

## Migration Checklist

- [x] Create backend abstraction layer
- [x] Update Pydantic AI integration
- [x] Update DrumGeneratorAI API
- [x] Create test infrastructure
- [x] Move tests to organized structure
- [x] Add pytest configuration
- [ ] Update Langchain agent for v1.0
- [ ] Re-enable agent features
- [ ] Add agent integration tests
- [ ] Update documentation
- [ ] Add usage examples

## Known Issues

1. **Langchain Agent Disabled**: Temporarily disabled due to Langchain 1.0 breaking changes
2. **Agent Tests Skipped**: Tests requiring agent functionality will be skipped
3. **Documentation Updates Needed**: README and CLAUDE.md need backend abstraction examples

## Future Enhancements

1. **Additional Providers**: Add support for more AI providers (Cohere, Mistral, etc.)
2. **Streaming Support**: Add streaming generation for real-time pattern creation
3. **Caching**: Implement intelligent caching for repeated requests
4. **Rate Limiting**: Add rate limiting and retry logic
5. **Cost Tracking**: Track API usage and costs per provider
