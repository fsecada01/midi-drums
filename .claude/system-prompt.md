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

## Claude Code Model Tiers

Which model to use for *Claude Code's own* Agent/Workflow subagent calls in this repo.
Distinct from "AI Module Runtime Model Routing" below, which governs the product's own
generation backend — do not conflate the two.

| Task type | Model | Why |
|---|---|---|
| Lookups, greps, Explore-agent searches, mechanical lint/format fixups | Haiku 4.5 | Cheap, no judgment required |
| Plugin/pattern implementation, test writing, docs updates, CLI/API wiring | Sonnet 5 (session default — inherit, don't override) | Standard repo work |
| DDD re-architecture planning (Epic #8), cross-cutting SOLID/architecture review, ambiguous multi-genre design tradeoffs, hard debugging with unclear root cause | Opus 5 | Token usage explains most quality variance, but a model-tier upgrade beats doubling the token budget — spend the upgrade on genuinely hard reasoning, not on volume |
| Prose meant for a human reader's enjoyment/persuasion — README feature copy, GitHub Pages site copy, drummer-plugin flavor text/bios, personality-driven changelog entries | Fable 5 | Narrative voice, not structural correctness. **Opt-in only.** If the deliverable is something a developer will reference for facts (docstrings, API docs, CLAUDE.md) or feeds back into code/config, stay on Sonnet. Default to Sonnet when in doubt. |

## SuperClaude vs Superpowers

**Default to SuperClaude (`/sc:*`).** Superpowers' process skills
(`brainstorming` -> `writing-plans` -> `subagent-driven-development`) dispatch a fresh
implementer + fresh reviewer subagent per task, which is real overhead — worth it for
genuinely risky multi-file code changes, not for routine work. Reserve Superpowers for
tasks with real cross-file correctness risk, or where SuperClaude has no equivalent.
When in doubt, do the work directly or with a single Agent dispatch instead of routing
it through either framework's ceremony.

| Task shape | Use |
|---|---|
| New feature, needs a spec before code | `sc:design` or `sc:brainstorm` |
| Bug / unexpected behavior | `sc:troubleshoot` |
| External/current information needed | `sc:research` |
| Multi-file implementation tasks | `sc:implement` / `sc:task`; escalate to `superpowers:subagent-driven-development` only for genuinely high-risk, tightly-coupled multi-file work |
| Business/strategy tradeoffs | `sc:business-panel` |
| Cheap session start / repo orientation | `sc:load` / `sc:index-repo` |
| No SuperClaude equivalent (e.g. systematic root-cause debugging loop) | fall back to the matching `superpowers:*` skill |

## UX/UI Redesign Workflow

This repo's only UI surface is the docs site (`docs/site-pages/*.html`, built by
`docs/make.py`). Which agent/skill/command fits depends on whether the work is
*originating* a visual identity or *operating on* one that already exists — those are
different jobs with different tools.

| Situation | Use |
|---|---|
| Requirements/scope unclear (what should this page accomplish, for whom) | `sc:brainstorm` or `sc:design` first, or plain Socratic dialogue with the user — pin down subject/audience/constraints before any visual work starts (see feedback memory on Socratic design clarity) |
| **Net-new** visual identity — new page, rebrand, "make this not look like every other AI-generated site" | `frontend-design:frontend-design` skill (Anthropic official plugin, enabled in this repo's global settings). Its brainstorm → plan → critique → build → critique loop is built for exactly this: opinionated palette/type/layout/signature-element choices grounded in the subject. Invoke it directly (`Skill` tool) so its process guidance loads into the *acting* context — don't just summarize it into a subagent prompt secondhand. |
| **Consolidation / technical-debt / accessibility pass** on an *already-shipped* identity (e.g. issue #44 AC Group 4: dedupe the 5 pages' duplicated `<style>` blocks, fix contrast, add landmarks) | `frontend-architect` agent, dispatched directly with a tight objective/scope/boundaries prompt. Skip the frontend-design skill's creative-brainstorm framework here — it doesn't apply when the brief is explicitly "preserve the existing identity, don't rebrand." |
| Want several independent visual directions to compare before committing (e.g. a genuine redesign, not a consolidation) | `Workflow` tool, judge-panel pattern (N independent design attempts, scored synthesis) — **opt-in only**, per this repo's standing multi-agent policy above. Never default to this; the user has to ask for parallel exploration explicitly. |
| Post-implementation check | `just docs-serve` + a manual look (Chrome browser tools if available) is sufficient at this repo's scale. Escalate to `quality-engineer` only if the redesign grows real interactive/JS behavior worth a dedicated test pass — not needed for the current static-HTML docs site. |

None of this needs `--auto-merge` or Workflow's full ceremony by default — a docs-site
pass is exactly the "single cohesive shared-file task" case the general sub-agent
policy above already covers (all 5 site pages + `docs/make.py`'s build wiring are one
unit of work, dispatched to one agent, not split per-page).

## Token Reduction Strategies for Subagent Work

Condensed from `claudedocs/research_subagent_token_reduction_20260810.md`:

1. Write tight dispatch prompts (objective/format/scope/boundaries) — highest-leverage
   lever, ahead of model choice or caching.
2. Subagents return a condensed answer (~1,000-2,000 tokens), never a raw tool-call
   trace — point at file paths/diffs instead of inlining large content back into the
   parent context.
3. Force structured/schema output for verdicts and extraction tasks; leave free-form
   reasoning for open design/judgment calls (schemas measurably reduce reasoning
   quality on genuinely open-ended work).
4. Use compaction / scratch-file note-taking for long sessions instead of letting
   context grow unbounded.
5. Don't treat prompt caching as justification for fan-out — caching lowers the fixed
   scaffolding cost (shared system prompt/tool schemas across a parallel batch), it
   does not reduce the N-times marginal cost of running N agents instead of 1.

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
