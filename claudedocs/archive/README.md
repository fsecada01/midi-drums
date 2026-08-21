# Claude Code Documentation Archive

Historical development documentation for the MIDI Drums Generator project.

## Archive Structure

### 2025-09-september/ - Genre System Expansion
**Period**: September 28-30, 2025

**Major Features**:
1. **Genre Plugin Expansion** (Sep 28)
   - Added Rock genre (7 styles)
   - Added Jazz genre (7 styles)
   - Added Funk genre (7 styles)
   - File: `memo.md`

2. **Genre Context Adaptation** (Sep 30)
   - Designed and implemented genre blending system
   - Allows patterns to adapt to overall song context
   - Files: `GENRE_CONTEXT_ADAPTATION_DESIGN.md`, `GENRE_CONTEXT_ADAPTATION_COMPLETE.md`

3. **Critical Bug Fixes** (Sep 30)
   - Fixed empty pattern bug in bridge generation
   - Resolved Chambers drummer crash with progressive patterns
   - Files: `BUG_FIX_SUMMARY.md`, `FINAL_RESULTS_COMPARISON.md`

**System State**: 4 genres × 7 styles = 28 total styles, 7 drummer plugins

---

### 2025-09-28_song_generation/ - Complex Song Examples
**Date**: September 28, 2025

**Content**: Example song generation projects demonstrating:
- Complex multi-genre song structures
- Professional project organization
- Drummer style applications
- Tempo variation handling

**Files**:
- `COMPLEX_SONG_SUMMARY.md` - Death metal song with multiple sections
- `ORGANIZED_SONG_PROJECT_SUCCESS.md` - Professional directory structure demo

---

### 2026-08-21_docs-cleanup/ - Documentation Reorganization (Issue #59)
**Date**: 2026-08-21

**Content**: Design docs, implementation plans, and research notes
superseded by their shipped features or migrated into
[`docs/adr/`](../../docs/adr/) as decision records:
- `design_reaper_panel.md`, `2026-08-21-unified-reaper-panel-plan.md` -> [ADR 0001](../../docs/adr/0001-unified-reaper-panel.md)
- `PHYSICAL_FEASIBILITY_FIXES.md`, `HUMANIZATION_IMPROVEMENTS.md`, `HUMANIZATION_SUMMARY.md` -> [ADR 0002](../../docs/adr/0002-physical-feasibility-and-advanced-humanization.md)
- `2026-08-10-system-prompt-update-design.md`, `2026-08-10-system-prompt-update-plan.md`, `research_subagent_token_reduction_20260810.md` -> [ADR 0003](../../docs/adr/0003-claude-code-workflow-policy.md)
- `REFACTORING_PLAN.md`, `REFACTORING_PROGRESS.md` - superseded by `CLAUDE.md`'s own "Refactoring Achievement" section (same content, kept current there instead)
- `AI_GENERATION_SUCCESS.md` - a single dated manual test log, pure point-in-time record
- `AI_BACKEND_MIGRATION.md` - Langchain backend migration, now complete (see `docs/AI_INTEGRATION.md` for the current architecture)
- `research_vendor_drum_midi_maps_20260812.md` - vendor MIDI note-map research for issue #47 (EZDrummer 3 confirmed; Superior Drummer 3/BFD3/Addictive Drums 2 remain unresolved if that follow-up research is picked back up)
- `REAPER_INTEGRATION.md`, `REAPER_TASKS.md` - the original single-workflow REAPER export feature, superseded by the unified panel (ADR 0001) and current `midi_drums/export/reaper/` module layout

---

## Document Index by Topic

### Architecture & Design
- `2025-09-september/GENRE_CONTEXT_ADAPTATION_DESIGN.md` - Genre blending architecture

### Implementation Reports
- `2025-09-september/GENRE_CONTEXT_ADAPTATION_COMPLETE.md` - Genre blending implementation
- `2025-09-september/memo.md` - Genre plugin expansion summary

### Bug Fixes
- `2025-09-september/BUG_FIX_SUMMARY.md` - Empty pattern bug fix
- `2025-09-september/FINAL_RESULTS_COMPARISON.md` - Before/after validation

### Examples
- `2025-09-28_song_generation/COMPLEX_SONG_SUMMARY.md` - Complex song demo
- `2025-09-28_song_generation/ORGANIZED_SONG_PROJECT_SUCCESS.md` - Project organization

---

## Timeline Summary

**September 28, 2025**:
- Genre plugin expansion (Rock, Jazz, Funk)
- Complex song generation examples

**September 30, 2025**:
- Genre context adaptation feature
- Empty pattern bug fix
- System validation and testing

**October 26, 2025**:
- Documents archived for organization
- Comprehensive refactoring plan created

---

## Notes

These documents represent successful feature implementations and are preserved for:
1. Historical reference
2. Understanding design decisions
3. Learning from bug fixes
4. Example project demonstrations

For current development planning, see: `../REFACTORING_PLAN.md`
