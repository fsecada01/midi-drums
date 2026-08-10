# Design: Update `.claude/system-prompt.md` for parallel workflows, model tiers, SC-vs-Superpowers, token reduction

**Date**: 2026-08-10
**Status**: Approved
**File to change**: `.claude/system-prompt.md` (manual-reference dev doc, same role as `CLAUDE.md` but slimmer/task-focused; not auto-loaded by any hook — confirmed by inspecting `.claude/settings.local.json`, no `systemPrompt`/append field present)

## Motivation

The file was last touched when the repo added the justfile/AI-prompts docs (commit
`7e3910c`). Since then the project has picked up the Agent/Workflow tool ecosystem,
SuperClaude (`/sc:*`), and Superpowers (`superpowers:*`) skills, none of which the file
mentions. Driving concerns (per user): the file is generally stale, and existing
multi-agent/parallel work in this repo hasn't been well-defined against the tasks this
repo actually has (cross-genre pattern work, drummer-plugin testing, etc.) — not a
specific cost incident.

## Scope

Add/replace four sections in `.claude/system-prompt.md`:

1. Sub-agent parallel workflow policy
2. Model tier table for Claude Code subagent work (distinct from the AI module's own
   `model_routing.md`, which governs the *product's* runtime multi-model calls, not
   Claude Code's own tooling)
3. SuperClaude vs Superpowers decision table
4. Token reduction strategies for subagent work

Research backing section 4 (and informing 1) is at
`claudedocs/research_subagent_token_reduction_20260810.md`.

## 1. Sub-agent parallel workflow policy

### General rule

Default to single-agent. Per Anthropic's own multi-agent research writeup, multi-agent
systems cost ~15x a plain chat turn, and **coding tasks are explicitly named as a poor
multi-agent fit** because most coding subtasks share files/state (this repo's shared
`constants.py`, `templates.py`, `drummer_mods.py` are exactly that case). Reach for
Agent/Workflow deliberately, when subtasks are genuinely independent — not by default.

- **1 agent** (default): single-file change, lookup, bugfix, most plugin edits.
- **2–4 agents**: only for genuinely independent slices — e.g., one agent per genre
  plugin, one per drummer plugin.
- **Never approach the 15-agent Workflow ceiling** for this repo's size; needing that
  many agents is a signal the task is mis-scoped, not a signal to add more agents.
- Every dispatch prompt states: objective, expected output format, in-scope
  files/tools, explicit boundaries. This was Anthropic's most-cited real failure mode
  (vague delegation → duplicated work/gaps) and the single highest-leverage token lever
  found in research, ahead of model choice or caching.

### Repo-specific patterns

- **Cross-genre pattern audit** → one agent per genre plugin (metal/rock/jazz/funk),
  each checks for magic numbers / constants usage / template composition compliance,
  then one synthesis pass.
- **Drummer-plugin compatibility sweep** → one agent per drummer plugin, tested against
  its declared `compatible_genres`.
- **New genre or drummer plugin** → **sequential, not parallel**: brainstorm/design →
  single implementation agent → test-writing agent → review agent. Shared-file
  dependency rule applies (new plugins touch shared infra modules).
- **REAPER Lua ↔ Python sidecar changes** → **sequential, never parallel** — both sides
  share the `midi_drums_sections.json` sidecar contract; parallel edits risk drifting
  the schema out of sync between the two languages.

## 2. Model tier table (Claude Code subagent work)

This governs which model to select for *Claude Code's own* Agent/Workflow subagent
calls in this repo. It is separate from `midi_drums/ai/prompts/model_routing.md`, which
governs the product's own runtime AI generation backend routing (Anthropic/OpenAI/Groq/
Cohere tiers called by the app itself) — do not conflate the two.

| Task type | Model | Why |
|---|---|---|
| Lookups, greps, Explore-agent searches, mechanical lint/format fixups | Haiku 4.5 | Cheap, no judgment required |
| Plugin/pattern implementation, test writing, docs updates, CLI/API wiring | Sonnet 5 (session default — inherit, don't override) | Standard repo work |
| DDD re-architecture planning (Epic #8), cross-cutting SOLID/architecture review, ambiguous multi-genre design tradeoffs, hard debugging with unclear root cause | Opus 5 | Anthropic's research found token usage explains 80% of quality variance, but a model-tier upgrade beat doubling the token budget — spend the upgrade on genuinely hard reasoning, not on volume |
| Prose meant for a human reader's enjoyment/persuasion — README feature copy, GitHub Pages site copy, drummer-plugin flavor text/bios, personality-driven changelog entries | Fable 5 | Narrative voice, not structural correctness. **Opt-in only.** If the deliverable is something a developer will reference for facts (docstrings, API docs, CLAUDE.md) or feeds back into code/config, stay on Sonnet. Default to Sonnet when in doubt. |

## 3. SuperClaude vs Superpowers — task-shape table

No hard precedence rule; resolve by task shape (per user decision — this avoids
declaring an artificial winner when the two frameworks cover genuinely different
ground):

| Task shape | Use |
|---|---|
| New feature, needs a spec before code | `superpowers:brainstorming` |
| Bug / unexpected behavior | `superpowers:systematic-debugging` |
| External/current information needed | `sc:research` |
| Multi-file independent implementation tasks | `superpowers:subagent-driven-development` |
| Implementing any feature/bugfix (test-first) | `superpowers:test-driven-development` |
| Business/strategy tradeoffs | `sc:business-panel` |
| Cheap session start / repo orientation | `sc:load` / `sc:index-repo` |

## 4. Token reduction strategies for subagent work

Condensed from `claudedocs/research_subagent_token_reduction_20260810.md`:

1. Write tight dispatch prompts (objective/format/scope/boundaries) — highest-leverage
   lever, ahead of model choice or caching.
2. Subagents return a condensed answer (~1,000–2,000 tokens), never a raw tool-call
   trace — point at file paths/diffs instead of inlining large content back into the
   parent context.
3. Force structured/schema output for verdicts and extraction tasks; leave free-form
   reasoning for open design/judgment calls (schemas measurably reduce reasoning quality
   on genuinely open-ended work).
4. Use compaction / scratch-file note-taking for long sessions instead of letting
   context grow unbounded.
5. Don't treat prompt caching as justification for fan-out — caching lowers the fixed
   scaffolding cost (shared system prompt/tool schemas across a parallel batch), it does
   not reduce the N-times marginal cost of running N agents instead of 1.

## Out of scope

- Changing `midi_drums/ai/prompts/model_routing.md` or any AI-module runtime behavior —
  that file governs the product's own generation backend, not Claude Code tooling, and
  is untouched by this change.
- Any code changes. This is a documentation-only update to `.claude/system-prompt.md`.

## Self-review notes

- No placeholders/TBDs remain.
- Section 2 explicitly disambiguates from `model_routing.md` to prevent future
  confusion between the two "model tier" concepts living in the same repo.
- Section 1's general rule and repo-specific patterns are consistent (both lean on the
  "shared files = don't parallelize" finding).
- Scope is a single file edit; no decomposition needed.
