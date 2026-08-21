# Research: Token Reduction Strategies for Sub-Agent / Multi-Agent Claude Code Workflows

**Date**: 2026-08-10
**Scope**: Practical policy for a single-developer local repo (midi_drums), not enterprise scale.
**Depth**: Deep (primary Anthropic engineering sources + supporting industry sources)

## Executive Summary

Multi-agent orchestration is expensive by default — Anthropic's own figures put agentic
chat at ~4x the tokens of a plain chat turn, and multi-agent systems at ~15x. That cost
is worth paying only when the task's value clears the multiplier, when subtasks are
genuinely independent (low cross-agent dependency), and when the work is scoped tightly
enough that agents don't duplicate each other. For a single-developer repo, the practical
takeaway is: default to no parallelism, reach for it deliberately, and when you do, spend
the token budget on tight task scoping and result compression rather than agent count.

## Key Findings

### 1. Baseline cost multipliers (Anthropic, primary source)
- Agentic chat interactions: ~4x tokens of standard chat.
- Multi-agent systems (orchestrator + subagents): ~15x tokens of standard chat.
- Independently, industry measurement of Claude Code subagent-heavy sessions puts the
  multiplier around ~7x a single-thread session — lower than Anthropic's research-system
  figure, consistent with subagents being used for scoped delegation rather than full
  parallel research fleets.
- **Implication**: token cost, not architecture cleverness, is the dominant lever —
  Anthropic found token usage alone explained 80% of performance variance in their
  research-quality evals, and upgrading model tier beat doubling token budget.

### 2. When multi-agent is NOT worth it (Anthropic, primary source)
Three explicit disqualifiers:
- **Low task value**: the task must be worth paying the multiplier for. Simple, cheap,
  or low-stakes tasks should stay single-agent.
- **Shared-context / high cross-dependency domains**: Anthropic names **coding tasks
  specifically** as a poor fit for multi-agent parallelism, because most coding subtasks
  need to share state (the same files, the same running interpreter, the same test
  suite) rather than working in isolation. This directly informs midi_drums policy: most
  plugin/pattern edits touch shared files (`constants.py`, `templates.py`,
  `drummer_mods.py`) and should NOT be fanned out blindly.
- **Coordination-heavy work**: current models are not yet reliable at real-time
  delegation/coordination between agents — favor a flat fan-out with a synthesis step
  over deep agent hierarchies or agents that need to negotiate with each other mid-task.

Supporting literature (arXiv, industry) adds a quantitative view: coordination overhead
grows *superlinearly* with agent count (roughly O(n^1.4–2.1)), and even a 2-agent team can
already lose 15–49% of single-agent quality on tasks with real interdependency. Context
isolation (each agent sees only its slice) reduces coordination overhead but can hurt
correctness when agents actually need each other's information — so isolation is a good
default only for genuinely independent subtasks.

### 3. Subagent count should scale to task shape, not habit (Anthropic, primary source)
Anthropic's own scaling table for their research agent:
- Simple fact-finding → 1 agent, 3–10 tool calls.
- Direct comparisons → 2–4 subagents, 10–15 calls each.
- Complex, multi-part work → 10+ subagents with clearly divided responsibilities.

The named failure mode is spawning many subagents for a simple query. For midi_drums —
a small single-maintainer repo — the equivalent ceiling is much lower than a research
system's; the existing session default of "keep workflows under 15 agents" is directionally
right, and most repo tasks should land in the 1–4 agent band, not near that ceiling.

### 4. Task scoping is the highest-leverage lever (Anthropic, primary source)
Vague delegation ("go look at the genre plugins") reliably causes agents to duplicate
work, leave gaps, or search redundantly — this was Anthropic's most-cited real failure
mode. Every subagent dispatch should specify, in the prompt itself:
- the objective,
- the expected output shape (schema/format),
- which tools/files/sources are in scope,
- explicit task boundaries (what NOT to touch or re-derive).

This matches the existing Agent-tool guidance already in use ("brief the agent like a
smart colleague... include file paths, line numbers, what specifically to change") — the
research confirms that guidance is not just a style preference, it is the primary token
lever, ahead of model choice or caching.

### 5. Result compression: subagents should return distillate, not trace (Anthropic, primary source)
A subagent doing deep exploration may burn tens of thousands of tokens internally, but
should hand back a condensed summary — Anthropic's own subagents return roughly
**1,000–2,000 tokens** regardless of how much they explored internally. Two techniques:
- **Summarize before returning**: never let a subagent's raw tool-call trace flow back
  into the orchestrator's context; the subagent's final message should be the answer,
  not a log.
- **Reference, don't inline, large artifacts**: for large outputs (generated files, full
  diffs, long file dumps), have the subagent write to disk/report a path or a diff
  summary and let the orchestrator (or a review step) read it directly rather than
  copying it through conversation history a second time. Anthropic explicitly calls out
  bypassing the coordinator for large results as a token-overhead reduction.
- Structured/schema output (JSON-schema-forced results) is also more token-efficient
  than free text for the same information, and it composes well with the Workflow tool's
  `schema` option — but there is a documented tradeoff: heavily constrained output can
  measurably reduce reasoning quality on genuinely open-ended judgment calls, so reserve
  strict schemas for extraction/classification/verdict-style outputs, not for open design
  reasoning.

### 6. Context engineering techniques that reduce cost independent of agent count (Anthropic, primary source)
- **Compaction**: summarize conversation history near context limits, keep decisions and
  open issues, drop redundant tool output — clear old tool-call results once they're deep
  in history rather than carrying them forever.
- **Structured note-taking / external memory**: write progress notes outside the active
  context (a scratch file, a task list) and re-read them, instead of keeping the full
  working state in the live context window.
- **Just-in-time / progressive retrieval**: keep lightweight references (file paths,
  search queries) in context and load full content only when actually needed, rather than
  pre-loading everything up front.
- **Token-efficient tool design**: fewer, non-overlapping tools with a single obvious use
  reduce wasted exploration and mis-selection — directly relevant to this session's
  practice of loading MCP tools only on demand via ToolSearch rather than upfront.

### 7. Prompt caching interacts with parallelism, but is orthogonal to agent count
Anthropic's multi-agent research paper does not address caching directly, but the
supporting caching literature is consistent and strong: cached input tokens cost ~10% of
base price (vs. a 25% premium to *write* the cache), and production agentic workloads
with 80–95% stable prefix content see 41–90% reductions in input cost from caching alone.
The practical corollary for parallel subagents: **agents sharing an identical system
prompt / tool-schema prefix benefit from cache hits across the parallel batch**, but each
agent still pays for its own unique task-specific context — caching reduces the fixed
cost of orchestration scaffolding, it does not reduce the marginal cost of running N
agents instead of 1. It's a multiplier-reducer, not a parallelism-justifier.

## Recommendations for midi_drums Claude Code Policy

1. **Default to zero or minimal parallelism.** Most midi_drums tasks (a plugin edit, a
   bugfix, a test) are single-agent work with high cross-file dependency — exactly the
   shared-context case Anthropic flags as a poor multi-agent fit. Reach for Agent/Workflow
   deliberately, not by default.
2. **Scale agent count to task shape**: 1 agent for a lookup or single-file change;
   2–4 for genuinely independent slices (e.g., one agent per genre plugin, one per
   drummer plugin); do not approach the 15-agent workflow ceiling for this repo's size.
3. **Write tight dispatch prompts**: objective, output format, in-scope files/tools,
   explicit boundaries — every time, not just for Workflow-tool scripts.
4. **Force structured output for verdicts/extraction**, leave free-form reasoning for
   open design/judgment work.
5. **Never let raw subagent tool-traces re-enter the parent context.** Require a
   condensed final answer; point at files/diffs by path instead of inlining large
   content.
6. **Use compaction and scratch-file note-taking for long-running sessions** instead of
   letting context grow unbounded, independent of whether subagents are involved.
7. **Don't count on caching to justify parallel fan-out** — it reduces the fixed
   scaffolding cost, not the N-times marginal cost of running N agents.

## Sources

- [Anthropic — How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [How Anthropic Built Multi-Agent Deep Research (secondary summary)](https://theaiengineer.substack.com/p/how-anthropic-built-multi-agent-deep)
- [How Anthropic Built a Multi-Agent Research System (secondary summary)](https://blog.bytebytego.com/p/how-anthropic-built-a-multi-agent)
- [Best Practices for Claude Code Subagents Optimization — UX Planet](https://uxplanet.org/best-practices-for-claude-code-subagents-optimization-7ff0dd3e20b5)
- [Claude Code Subagents: A 2026 Practical Guide — Tembo.io](https://www.tembo.io/blog/claude-code-subagents)
- [Claude Code Token Optimization 2026 — ofox.ai](https://ofox.ai/blog/claude-code-token-optimization-2026/)
- [Prompt caching with Claude — Anthropic/Claude blog](https://claude.com/blog/prompt-caching)
- [Claude API Cost Optimization: Caching, Batching, and 60% Token Reduction — dev.to](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- [Token efficiency with structured output from language models — Microsoft/Medium](https://medium.com/data-science-at-microsoft/token-efficiency-with-structured-output-from-language-models-be2e51d3d9d5)
- [Parallel Agent Execution vs Sequential Agents: When to Use Each — MindStudio](https://www.mindstudio.ai/blog/parallel-agent-execution-vs-sequential-agents)
- [Parallelism Meets Adaptiveness: Scalable Documents Understanding in Multi-Agent LLM Systems (arXiv)](https://arxiv.org/html/2507.17061v3)

## Confidence & Gaps

- **High confidence**: cost multipliers, subagent scaling table, "coding is a poor
  multi-agent fit" claim, result-compression pattern — all from Anthropic's own
  engineering writeups (primary source, internal data).
- **Medium confidence**: the superlinear coordination-overhead exponent and the 15–49%
  quality-loss figures for 2-agent teams — from arXiv preprints, not replicated here,
  treat as directional rather than exact.
- **Gap**: no source directly measured token cost for Claude Code's specific
  `Agent`/`Workflow` tool implementations (this research covers the general multi-agent
  pattern, not this harness's exact overhead) — the recommendations above are the general
  pattern applied to this repo's context, not a benchmark of this repo's actual usage.
