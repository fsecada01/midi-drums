# System Prompt Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `.claude/system-prompt.md` with four new/clarified sections — sub-agent parallel workflow policy, Claude Code model tiers, SuperClaude-vs-Superpowers guidance, and token reduction strategies — per the approved design at `docs/superpowers/specs/2026-08-10-system-prompt-update-design.md`.

**Architecture:** Documentation-only edit to a single Markdown file. No code, no tests in the pytest sense — each task inserts one Markdown section via exact anchor-based edits and verifies the insertion landed in the right place with the right structure (heading present, table well-formed, no duplicate headings).

**Tech Stack:** Markdown. Target file: `.claude/system-prompt.md` in `C:\dev\python\projects\midi_drums`.

## Global Constraints

- Single file: `.claude/system-prompt.md`. No other files are modified by this plan (the spec and research doc are already written and committed).
- Do not touch `midi_drums/ai/prompts/model_routing.md` — it governs the product's own AI backend routing, not Claude Code tooling. The plan only adds a disambiguating note to `system-prompt.md`'s existing "Multi-Model Workflow" section pointing this out.
- Preserve all existing content in `.claude/system-prompt.md` outside the four new/edited sections — this is an additive/clarifying change, not a rewrite.
- New section headings use `##` (same level as existing top-level sections like `## Core Principles`, `## Multi-Model Workflow`).
- Insertion order in the file: existing content through `### Quality Gates` stays first, then the four new sections in this order — (1) Claude Code Sub-Agent Workflow Policy, (2) Claude Code Model Tiers, (3) SuperClaude vs Superpowers, (4) Token Reduction Strategies for Subagent Work — then the (renamed/clarified) existing `## Multi-Model Workflow` section, then all remaining existing content unchanged.

---

### Task 1: Disambiguate the existing "Multi-Model Workflow" section

**Files:**
- Modify: `.claude/system-prompt.md` (existing `## Multi-Model Workflow` heading, currently at line 35)

**Interfaces:**
- Consumes: nothing (first task, operates on existing file content only)
- Produces: renamed heading `## AI Module Runtime Model Routing (Product Backend)` that later tasks' new sections sit above in the file — later tasks insert new sections *before* this heading, so this rename should land first to avoid ambiguity about which "model" section is which while editing.

- [ ] **Step 1: Rename the heading and add a disambiguation note**

Use the Edit tool on `.claude/system-prompt.md` with this exact replacement:

Old string:
```
## Multi-Model Workflow

### Model Tiers
```

New string:
```
## AI Module Runtime Model Routing (Product Backend)

> This section governs the **product's own** AI generation backend (the `midi_drums.ai`
> module calling Anthropic/OpenAI/Groq/Cohere at runtime for pattern/song generation).
> It is unrelated to which model *Claude Code itself* should use for development
> subagents — see "Claude Code Model Tiers" below for that.

### Model Tiers
```

- [ ] **Step 2: Verify the rename**

Run: `grep -n "Multi-Model Workflow\|AI Module Runtime Model Routing" .claude/system-prompt.md`
Expected: no match for "Multi-Model Workflow", one match for "## AI Module Runtime Model Routing (Product Backend)".

- [ ] **Step 3: Commit**

```bash
git add .claude/system-prompt.md
git commit -m "docs: disambiguate AI-module model routing from Claude Code tooling"
```

---

### Task 2: Add "Claude Code Sub-Agent Workflow Policy" section

**Files:**
- Modify: `.claude/system-prompt.md` (insert new section immediately after `### Quality Gates` code block, i.e. immediately before the `## AI Module Runtime Model Routing (Product Backend)` heading produced by Task 1)

**Interfaces:**
- Consumes: the Task-1 heading text `## AI Module Runtime Model Routing (Product Backend)` as the insertion anchor.
- Produces: new `## Claude Code Sub-Agent Workflow Policy` heading, which Task 3 will insert its own new section directly after.

- [ ] **Step 1: Insert the section**

Use the Edit tool on `.claude/system-prompt.md` with this exact replacement:

Old string:
```
```bash
just lint      # ruff, black, isort
just test      # pytest with markers
just check     # format + lint + test
```

## AI Module Runtime Model Routing (Product Backend)
```

New string:
```
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
```

- [ ] **Step 2: Verify the insertion**

Run: `grep -n "^## " .claude/system-prompt.md`
Expected: `## Claude Code Sub-Agent Workflow Policy` appears once, positioned between
`## Core Principles` and `## AI Module Runtime Model Routing (Product Backend)` in the
output order.

- [ ] **Step 3: Commit**

```bash
git add .claude/system-prompt.md
git commit -m "docs: add Claude Code sub-agent workflow policy"
```

---

### Task 3: Add "Claude Code Model Tiers" section

**Files:**
- Modify: `.claude/system-prompt.md` (insert new section immediately after the section Task 2 added, before `## AI Module Runtime Model Routing (Product Backend)`)

**Interfaces:**
- Consumes: the `## AI Module Runtime Model Routing (Product Backend)` heading as the insertion anchor (same anchor Task 2 used — Task 2 must run first so this anchor is preceded by the Sub-Agent Workflow Policy section, keeping insertion order correct).
- Produces: new `## Claude Code Model Tiers` heading, which Task 4 inserts its own new section directly after.

- [ ] **Step 1: Insert the section**

Use the Edit tool on `.claude/system-prompt.md` with this exact replacement:

Old string:
```
## AI Module Runtime Model Routing (Product Backend)
```

New string:
```
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

## AI Module Runtime Model Routing (Product Backend)
```

- [ ] **Step 2: Verify the insertion**

Run: `grep -n "^## " .claude/system-prompt.md`
Expected: `## Claude Code Model Tiers` appears once, positioned between
`## Claude Code Sub-Agent Workflow Policy` and `## AI Module Runtime Model Routing
(Product Backend)`.

Run: `grep -c "^| Lookups, greps\|^| Plugin/pattern\|^| DDD re-architecture\|^| Prose meant" .claude/system-prompt.md`
Expected: `4` — confirms all four data rows of the new table are present and weren't
truncated mid-insert.

- [ ] **Step 3: Commit**

```bash
git add .claude/system-prompt.md
git commit -m "docs: add Claude Code model tier table"
```

---

### Task 4: Add "SuperClaude vs Superpowers" and "Token Reduction Strategies" sections

**Files:**
- Modify: `.claude/system-prompt.md` (insert two new sections immediately after the section Task 3 added, before `## AI Module Runtime Model Routing (Product Backend)`)

**Interfaces:**
- Consumes: the `## AI Module Runtime Model Routing (Product Backend)` heading as the insertion anchor (Tasks 2 and 3 must have already run so this anchor is preceded by the two prior new sections in order).
- Produces: final section ordering for the whole file — no downstream task depends on this task's output; this is the last insertion.

- [ ] **Step 1: Insert both sections**

Use the Edit tool on `.claude/system-prompt.md` with this exact replacement:

Old string:
```
## AI Module Runtime Model Routing (Product Backend)
```

New string:
```
## SuperClaude vs Superpowers

No hard precedence — resolve by task shape:

| Task shape | Use |
|---|---|
| New feature, needs a spec before code | `superpowers:brainstorming` |
| Bug / unexpected behavior | `superpowers:systematic-debugging` |
| External/current information needed | `sc:research` |
| Multi-file independent implementation tasks | `superpowers:subagent-driven-development` |
| Implementing any feature/bugfix (test-first) | `superpowers:test-driven-development` |
| Business/strategy tradeoffs | `sc:business-panel` |
| Cheap session start / repo orientation | `sc:load` / `sc:index-repo` |

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
```

- [ ] **Step 2: Verify the insertion and full section order**

Run: `grep -n "^## " .claude/system-prompt.md`
Expected order of headings from top to bottom:
```
## Essential References
## Core Principles
## Claude Code Sub-Agent Workflow Policy
## Claude Code Model Tiers
## SuperClaude vs Superpowers
## Token Reduction Strategies for Subagent Work
## AI Module Runtime Model Routing (Product Backend)
## AI Module Prompts
## Quick Reference
## Code Review Checklist
```

- [ ] **Step 3: Commit**

```bash
git add .claude/system-prompt.md
git commit -m "docs: add SuperClaude-vs-Superpowers guide and token reduction strategies"
```

---

### Task 5: Final full-file review

**Files:**
- Read only: `.claude/system-prompt.md`

**Interfaces:**
- Consumes: the fully-edited file produced by Tasks 1-4.
- Produces: nothing (verification-only task; no further tasks depend on it).

- [ ] **Step 1: Read the complete file**

Read `.claude/system-prompt.md` in full and confirm:
- All four new sections are present with correct heading text (see Task-by-task
  headings above).
- The `## AI Module Runtime Model Routing (Product Backend)` disambiguation note from
  Task 1 is still present and immediately follows that heading.
- No duplicate headings, no leftover merge artifacts, no broken Markdown tables (every
  table row has the same number of `|`-delimited columns as its header row).
- All pre-existing content (Essential References, Core Principles, AI Module Prompts,
  Quick Reference, Code Review Checklist, footer) is unchanged.

- [ ] **Step 2: Confirm no other files were touched**

Run: `git status --porcelain`
Expected: clean (everything already committed by Tasks 1-4); if anything is unstaged,
investigate before proceeding — this plan should only have touched
`.claude/system-prompt.md` across four commits.

- [ ] **Step 3: Confirm commit history**

Run: `git log --oneline -5`
Expected: four new commits on top of `2608f98` (the spec/research commit), one per
Task 1-4, each with a `docs:` prefix.

No commit needed for this task — it is verification-only.
