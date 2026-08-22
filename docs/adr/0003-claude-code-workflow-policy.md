# 0003. Claude Code sub-agent, model-tier, and framework-selection policy

> **Status**: Accepted (implemented in `.claude/system-prompt.md`)
> **Date**: 2026-08-21 (retroactively documented; original decision dated 2026-08-10)

## Context

By August 2026 this repo had picked up the Agent/Workflow multi-agent
tool ecosystem, SuperClaude (`/sc:*`), and Superpowers (`superpowers:*`)
skills, none of which `.claude/system-prompt.md` (a manual-reference dev
doc, not auto-loaded by any hook) mentioned. There was no stated policy
for when parallel sub-agent work was appropriate for this repo's actual
task shapes (cross-genre pattern audits, drummer-plugin compatibility
sweeps, REAPER Lua/Python sidecar changes), which model tier to use for
Claude Code's own subagent calls (a decision distinct from
`midi_drums/ai/prompts/model_routing.md`, which governs the *product's*
own runtime AI generation backend), or which of the two competing
skill frameworks to reach for on a given task shape.

## Decision

Four additions to `.claude/system-prompt.md`:

1. **Sub-agent workflow policy** — default to single-agent; per
   Anthropic's own multi-agent research, coding tasks are a poor
   multi-agent fit because subtasks typically share files/state (this
   repo's `constants.py`, `templates.py`, `drummer_mods.py` are exactly
   that case). 2-4 agents only for genuinely independent slices (one
   agent per genre/drummer plugin); REAPER Lua↔Python sidecar-contract
   changes are explicitly sequential, never parallel, since the two
   sides share no type system to catch drift.
2. **Model tier table** for Claude Code's own subagent calls: Haiku 4.5
   for lookups/mechanical fixups, Sonnet 5 (session default) for standard
   plugin/test/docs work, Opus 5 for DDD re-architecture and ambiguous
   cross-cutting design tradeoffs, Fable 5 (opt-in only) for prose meant
   for human enjoyment rather than structural correctness.
3. **SuperClaude vs. Superpowers** — no hard precedence; a task-shape
   table resolves which to reach for (e.g. `superpowers:brainstorming`
   for a new feature needing a spec first, `sc:research` for
   external/current information, `superpowers:test-driven-development`
   for any feature/bugfix implementation).
4. **Token reduction strategies** for subagent dispatch: tight dispatch
   prompts (objective/format/scope/boundaries) as the single
   highest-leverage lever; condensed subagent return values, not raw
   tool-call traces; structured/schema output for verdicts, free-form
   for open design judgment; prompt caching lowers fixed scaffolding
   cost but does not reduce the N-times marginal cost of fan-out.

## Consequences

- Future Claude Code sessions in this repo have a concrete, repo-specific
  answer to "should this be parallelized" and "which model" instead of
  re-deriving it per task.
- The existing `## Multi-Model Workflow` heading in `.claude/system-prompt.md`
  was renamed to `## AI Module Runtime Model Routing (Product Backend)`
  with an explicit disambiguation note, to stop the product's own AI
  backend routing table from being conflated with Claude Code's own
  subagent model tiers.
- This is Claude-tooling guidance, not project architecture — it governs
  how future AI-assisted sessions work in this repo, not the shipped
  product. It carries no test coverage of its own (documentation-only
  change) and its correctness can only be judged by whether it's actually
  followed in later sessions.

## References

- Full design/spec: [`claudedocs/archive/2026-08-21_docs-cleanup/2026-08-10-system-prompt-update-design.md`](../../claudedocs/archive/2026-08-21_docs-cleanup/2026-08-10-system-prompt-update-design.md)
- Full task-by-task implementation plan: [`claudedocs/archive/2026-08-21_docs-cleanup/2026-08-10-system-prompt-update-plan.md`](../../claudedocs/archive/2026-08-21_docs-cleanup/2026-08-10-system-prompt-update-plan.md)
- Supporting research: [`claudedocs/archive/2026-08-21_docs-cleanup/research_subagent_token_reduction_20260810.md`](../../claudedocs/archive/2026-08-21_docs-cleanup/research_subagent_token_reduction_20260810.md)
- Implemented in `.claude/system-prompt.md`
