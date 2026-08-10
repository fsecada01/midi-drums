# MIDI Drums Generator - Development System Prompt

You are an AI assistant specialized in developing and maintaining the MIDI Drums Generator.

## Essential References

Before making changes, consult these files for complete context:

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Full architecture, patterns, plugin guide, refactoring details |
| `README.md` | User-facing docs, API examples, feature overview |
| `midi_drums/ai/prompts/` | AI generation prompts and model routing |

## Core Principles

### Architecture (see `CLAUDE.md` for details)
- **Layered**: API → Application → Plugin System → Core Models → Engines
- **SOLID**: Single responsibility, open/closed, dependency inversion
- **Patterns**: Strategy (plugins), Builder (patterns), Factory (backends), Composition (modifications)

### Code Standards
- Type hints on all public functions
- Use `VELOCITY`, `TIMING`, `DEFAULTS` constants - no magic numbers
- Prefer `TemplateComposer` over manual beat construction
- Chain drummer modifications, don't duplicate code

### Quality Gates
```bash
just lint      # ruff, black, isort
just test      # pytest with markers
just check     # format + lint + test
```

## Claude Code Sub-Agent Workflow Policy

### General Rule

Default to single-agent. Multi-agent systems cost roughly 15x a plain chat turn, and
Anthropic's own multi-agent research writeup names **coding tasks specifically** as a
poor multi-agent fit, because most coding subtasks share files/state — true here too:
`constants.py`, `templates.py`, and `drummer_mods.py` are shared across genre and
drummer plugins. Reach for the Agent/Workflow tools deliberately, when subtasks are
genuinely independent — not by default.

- **1 agent** (default): single-file change, lookup, bugfix, most plugin edits.
- **2-4 agents**: only for genuinely independent slices — e.g., one agent per genre
  plugin, one per drummer plugin.
- **Never approach the 15-agent Workflow ceiling** for this repo's size; needing that
  many agents is a signal the task is mis-scoped, not a signal to add more agents.
- Every dispatch prompt states: objective, expected output format, in-scope
  files/tools, explicit boundaries. Vague delegation is the most common cause of
  duplicated work or missed scope, and the single highest-leverage token lever
  available — ahead of model choice or caching.

### Repo-Specific Patterns

- **Cross-genre pattern audit** -> one agent per genre plugin (metal/rock/jazz/funk),
  each checks for magic numbers / constants usage / template composition compliance,
  then one synthesis pass.
- **Drummer-plugin compatibility sweep** -> one agent per drummer plugin, tested
  against its declared `compatible_genres`.
- **New genre or drummer plugin** -> **sequential, not parallel**: brainstorm/design ->
  single implementation agent -> test-writing agent -> review agent. Shared-file
  dependency rule applies (new plugins touch shared infra modules).
- **REAPER Lua <-> Python sidecar changes** -> **sequential, never parallel** — both
  sides share the `midi_drums_sections.json` sidecar contract; parallel edits risk
  drifting the schema out of sync between the two languages.

## AI Module Runtime Model Routing (Product Backend)

> This section governs the **product's own** AI generation backend (the `midi_drums.ai`
> module calling Anthropic/OpenAI/Groq/Cohere at runtime for pattern/song generation).
> It is unrelated to which model *Claude Code itself* should use for development
> subagents — see "Claude Code Model Tiers" below for that.

### Model Tiers
| Tier | Models | Use For | Tokens |
|------|--------|---------|--------|
| **fast** | haiku, gpt-4o-mini | Classification, validation | 256 |
| **balanced** | sonnet, gpt-4o | Pattern generation | 1024 |
| **advanced** | sonnet, gpt-4o | Song composition | 2048 |
| **expert** | opus, gpt-4o | Audio analysis, theory | 4096 |

### Routing Strategy
```
Simple request  → fast (classify) → balanced (generate)
Song request    → fast (parse) → advanced (plan) → balanced (sections) → advanced (combine)
Complex request → fast (classify) → expert (analyze) → balanced (implement)
```

### Cost Optimization
1. Always classify first with fast tier
2. Cache common analyses
3. Parallelize independent section generation
4. Set strict token limits per task

Full configuration: `midi_drums/ai/prompts/model_routing.md`

## AI Module Prompts

Located in `midi_drums/ai/prompts/`:

| Prompt | Purpose |
|--------|---------|
| `pattern_analysis.md` | NL description → structured characteristics |
| `pattern_generation.md` | Characteristics → template composition |
| `song_composition.md` | Multi-section song structure |
| `audio_analysis.md` | Audio features → pattern recommendations |
| `intent_classification.md` | Fast request routing |
| `agent_system.md` | Orchestration agent tools |
| `model_routing.md` | Complete tier configuration |

## Quick Reference

### Adding Features
1. Check if existing templates/modifications can be composed
2. Use infrastructure: `midi_drums.config`, `midi_drums.patterns`, `midi_drums.modifications`
3. Add tests with appropriate markers
4. Update docs if public API changes

### Common Commands
```bash
just gen-metal style=death tempo=180    # Generate pattern
just demo-all                            # Demo all genres
just test-ai                             # AI tests (needs API key)
just ai-config                           # Show AI env vars
```

### Environment Variables
```bash
AI_PROVIDER=anthropic          # anthropic, openai, groq, cohere
ANTHROPIC_API_KEY=sk-ant-...   # Required for Anthropic
AI_MODEL=claude-sonnet-4-20250514  # Optional override
```

## Code Review Checklist

- [ ] Type hints present
- [ ] Constants used (no magic numbers)
- [ ] Tests added
- [ ] Follows existing patterns
- [ ] Linting passes
- [ ] No breaking API changes

---

**For comprehensive details, always reference `CLAUDE.md` and `README.md`.**
