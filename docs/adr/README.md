# Architecture Decision Records

Short, MADR-lite records (Status / Context / Decision / Consequences) for
decisions worth remembering *why* we made, not just *what* the code does
today — the code itself is the source of truth for the "what". Start a
new ADR from [`0000-adr-template.md`](0000-adr-template.md).

## When to write one

A significant, hard-to-reverse, or frequently-relitigated decision:
picking one architecture over another, adopting or dropping a dependency,
a cross-cutting policy (like [0003](0003-claude-code-workflow-policy.md)).
Not every design doc needs to become an ADR — a doc that's still just a
proposal, or a one-off implementation plan with no standalone decision,
stays in `claudedocs/` (active) or its archive (historical) instead.

## Index

| # | Title | Status |
|---|-------|--------|
| [0001](0001-unified-reaper-panel.md) | Unified REAPER panel replaces three standalone Lua scripts | Accepted |
| [0002](0002-physical-feasibility-and-advanced-humanization.md) | Physical feasibility validation and Gaussian-based advanced humanization | Accepted |
| [0003](0003-claude-code-workflow-policy.md) | Claude Code sub-agent, model-tier, and framework-selection policy | Accepted |
| [0004](0004-riff-driven-snare-accent-reaction.md) | Riff-driven snare accent reaction as a separate, opt-in modification | Accepted |
| [0005](0005-genre-context-blending.md) | Genre-context blending via per-genre intensity profiles | Accepted |
| [0006](0006-ai-backend-provider-abstraction.md) | Provider-agnostic AI backend abstraction | Accepted |
| [0007](0007-reaper-rpp-export-engine.md) | Direct .RPP file manipulation for Reaper project export | Accepted |
| [0008](0008-vendor-midi-note-map-corrections.md) | GM preset note-map correction; other vendor kits left unresearched rather than guessed | Accepted |
