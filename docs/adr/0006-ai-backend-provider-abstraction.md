# 0006. Provider-agnostic AI backend abstraction

> **Status**: Accepted (implemented)
> **Date**: 2026-08-22 (retroactively documented; original migration undated, prior to 2026-08-21 doc-cleanup reorg)

## Context

The AI-powered generation module (`midi_drums/ai/`) originally hardcoded
Anthropic as its only LLM backend. Locking to a single provider meant no
fallback if Anthropic's API had an outage, no ability to trade cost/quality
across providers, and no clean seam for testing against a mock backend.
Separately, the `PatternCompositionAgent` (Langchain-based agentic
generation) was written against a pre-1.0 Langchain API and needed a
migration when Langchain 1.0 changed `AgentExecutor` and
`create_tool_calling_agent`.

## Decision

Introduce `AIBackendConfig`/`AIProvider`/`AIBackendFactory`
(`midi_drums/ai/backends.py`) as the single seam through which both the
Pydantic-AI pattern generator and the Langchain agent obtain their LLM
client. Provider selection and credentials come from environment variables
(`AI_PROVIDER`, `AI_MODEL`, `{PROVIDER}_API_KEY`, `AI_TEMPERATURE`,
`AI_MAX_TOKENS`) by default, with a `backend_config` constructor param on
`DrumGeneratorAI` for programmatic override — env-var-driven configuration
was chosen as the default path specifically so production deployment needs
no code change to switch providers. Legacy direct `api_key` parameters are
still accepted for backward compatibility rather than becoming a breaking
change.

The Langchain 1.0 migration (`create_react_agent` replacing
`create_tool_calling_agent`, updated import paths) was completed as part of
this same effort — `PatternCompositionAgent` is fully re-enabled and
exported from `midi_drums/ai/__init__.py`, not left in the "temporarily
disabled" state an earlier draft of this work had it in.

## Consequences

- Switching AI providers (Anthropic, OpenAI, Groq, Cohere) is a pure
  environment-variable change in production, no code deploy required.
- `midi_drums/ai/backends.py` is now the one place backend-selection logic
  lives; both the Pydantic-AI path and the Langchain agent path consume it,
  rather than each hardcoding its own client construction.
- Test infrastructure reorganization rode along with this change: tests
  moved into `tests/{unit,integration,ai}/`, with `pytest.ini` markers
  (`ai`, `requires_api`) so provider-dependent tests skip cleanly without
  API keys present — see `tests/ai/test_backend_abstraction.py`.
- Deferred (not built as part of this decision): streaming generation,
  response caching, per-provider cost tracking, and additional providers
  beyond the four enumerated in `AIProvider`.

## References

- Original migration write-up has been removed now that this ADR captures
  its decisions — see `claudedocs/archive/2026-08-21_docs-cleanup/AI_BACKEND_MIGRATION.md`
  in git history prior to this ADR's introduction for the full text.
- Current architecture/usage guide: [`docs/AI_INTEGRATION.md`](../AI_INTEGRATION.md)
- Shipped in `midi_drums/ai/backends.py`, `midi_drums/ai/pattern_generator.py`,
  `midi_drums/ai/ai_api.py`, `midi_drums/ai/agents/pattern_agent.py`
- Model-routing policy for the product's own runtime AI backend (distinct
  from Claude Code's own subagent model tiers, see
  [[0003-claude-code-workflow-policy]]): `midi_drums/ai/prompts/model_routing.md`
