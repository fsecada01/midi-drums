# Reaper Integration - Implementation Tasks

> **Branch**: `feat/reaper-integration` | **Estimate**: 12-19 hours | **Priority**: High

## Task Breakdown

### Phase 1: Research & Prototyping (2-4 hours)

#### Task 1.1: Reverse-Engineer .RPP Marker Syntax
**Estimate**: 1-2 hours | **Priority**: Critical

- [ ] Open Reaper and create blank project
- [ ] Add 4-5 markers manually with different names
- [ ] Export/save project to `test_markers.rpp`
- [ ] Open in text editor and examine marker syntax
- [ ] Document exact format (position, name, color, flags)
- [ ] Create reference document with examples

**Acceptance Criteria**:
- Documented marker syntax with all fields explained
- Example markers captured from real Reaper file

**Blocking**: All other tasks depend on this

---

#### Task 1.2: Install and Test rpp Library
**Estimate**: 0.5-1 hour | **Priority**: High

- [ ] Add `rpp>=0.5.0` to `pyproject.toml`
- [ ] Run `uv pip install rpp`
- [ ] Create prototype script to load test .rpp file
- [ ] Test parsing markers with `rpp.load()`
- [ ] Test generating simple .rpp with `rpp.dumps()`
- [ ] Verify output loads in Reaper

**Acceptance Criteria**:
- rpp library installed successfully
- Can parse and generate basic .rpp files
- Generated files load without errors in Reaper

**Dependencies**: Task 1.1 (need test file)

---

#### Task 1.3: Prototype Marker Creation
**Estimate**: 0.5-1 hour | **Priority**: High

- [ ] Create script to add single marker to .rpp
- [ ] Test with different time positions
- [ ] Test with different marker names
- [ ] Verify in Reaper that marker appears correctly
- [ ] Document any quirks or limitations

**Acceptance Criteria**:
- Working prototype that adds marker
- Marker appears at correct time in Reaper
- No errors when loading modified .rpp

**Dependencies**: Task 1.2

---

### Phase 2: Core Engine Implementation (4-6 hours)

#### Task 2.1: Create Data Models
**Estimate**: 1 hour | **Priority**: High

**File**: `midi_drums/models/reaper_models.py`

- [ ] Create `Marker` dataclass
  - `position_seconds: float`
  - `name: str`
  - `color: str`
  - `marker_id: int`
- [ ] Create `ReaperTrack` dataclass
  - `name: str`
  - `midi_source: Optional[str]`
  - `volume: float`
  - `pan: float`
- [ ] Add type hints and docstrings
- [ ] Create validation methods

**Acceptance Criteria**:
- All models defined with proper type hints
- Validation logic in place
- Docstrings complete

**Dependencies**: None

---

#### Task 2.2: Implement Time Position Calculator
**Estimate**: 1 hour | **Priority**: High

**File**: `midi_drums/engines/reaper_engine.py`

- [ ] Implement `bars_to_seconds()` function
  - Input: bars, tempo, time_signature
  - Output: position in seconds
- [ ] Handle edge cases (tempo=0, negative bars)
- [ ] Add comprehensive docstring with formula
- [ ] Write unit tests for various scenarios

**Acceptance Criteria**:
- Function calculates correct time positions
- Handles 4/4, 3/4, 7/8 time signatures
- Unit tests cover edge cases

**Dependencies**: Task 1.1 (understand time format)

---

#### Task 2.3: Implement ReaperEngine Class
**Estimate**: 2-3 hours | **Priority**: High

**File**: `midi_drums/engines/reaper_engine.py`

- [ ] Create `ReaperEngine` class
- [ ] Implement `create_marker()` method
- [ ] Implement `add_markers_to_project()` method
- [ ] Implement `create_midi_track()` method (optional)
- [ ] Add error handling and validation
- [ ] Write comprehensive docstrings
- [ ] Add logging for debugging

**Acceptance Criteria**:
- All methods implemented and documented
- Error handling for invalid inputs
- Logging provides useful debug info

**Dependencies**: Task 2.1, Task 2.2, Task 1.3 (marker syntax)

---

### Phase 3: High-Level API (2-3 hours)

#### Task 3.1: Implement ReaperExporter Class
**Estimate**: 2-3 hours | **Priority**: High

**File**: `midi_drums/exporters/reaper_exporter.py`

- [ ] Create `ReaperExporter` class
- [ ] Implement `export_with_markers()` method
  - Parse input .rpp
  - Calculate marker positions from Song
  - Add markers using ReaperEngine
  - Optionally add MIDI track
  - Write to output .rpp
- [ ] Implement `calculate_marker_positions()` method
- [ ] Add validation for file paths
- [ ] Add comprehensive error messages
- [ ] Write docstrings with examples

**Acceptance Criteria**:
- `export_with_markers()` works end-to-end
- Immutable operation (original file unchanged)
- Clear error messages for common issues

**Dependencies**: Task 2.3 (ReaperEngine)

---

### Phase 4: Testing (3-4 hours)

#### Task 4.1: Unit Tests - ReaperEngine
**Estimate**: 1-1.5 hours | **Priority**: High

**File**: `tests/unit/engines/test_reaper_engine.py`

- [ ] Test `bars_to_seconds()` calculation
  - 4/4 time signature
  - 3/4 time signature
  - Various tempos (60, 120, 180 BPM)
- [ ] Test `create_marker()` element creation
- [ ] Test marker serialization to .rpp format
- [ ] Test edge cases and error handling

**Acceptance Criteria**:
- 10+ unit tests covering core functions
- All tests pass
- Edge cases covered

**Dependencies**: Task 2.2, Task 2.3

---

#### Task 4.2: Unit Tests - ReaperExporter
**Estimate**: 1-1.5 hours | **Priority**: High

**File**: `tests/unit/exporters/test_reaper_exporter.py`

- [ ] Test `calculate_marker_positions()` from Song
- [ ] Test file I/O operations
- [ ] Test immutability (original file unchanged)
- [ ] Test error handling for invalid inputs
- [ ] Mock ReaperEngine for isolated testing

**Acceptance Criteria**:
- 8+ unit tests
- All tests pass
- Mocking used appropriately

**Dependencies**: Task 3.1

---

#### Task 4.3: Integration Tests
**Estimate**: 1-1.5 hours | **Priority**: High

**File**: `tests/integration/test_reaper_integration.py`

- [ ] Test full export workflow (Song → .rpp)
  - Generate song with multiple sections
  - Export to .rpp with markers
  - Verify .rpp can be loaded
  - Check marker positions are correct
- [ ] Test with different song structures
- [ ] Test with/without MIDI track option
- [ ] Test error recovery

**Acceptance Criteria**:
- 5+ integration tests
- All tests pass
- Tests use realistic scenarios

**Dependencies**: Task 3.1

---

### Phase 5: Documentation & Examples (1-2 hours)

#### Task 5.1: Create Example Scripts
**Estimate**: 0.5-1 hour | **Priority**: Medium

**Files**:
- `examples/reaper_export_basic.py`
- `examples/reaper_export_advanced.py`

- [ ] Create basic export example
  - Generate simple song
  - Export with markers
  - Print success message
- [ ] Create advanced example
  - Custom marker colors
  - MIDI track options
  - Error handling demonstration
- [ ] Add comments explaining each step
- [ ] Test examples work correctly

**Acceptance Criteria**:
- Examples run without errors
- Output files load in Reaper correctly
- Well-commented and educational

**Dependencies**: Task 3.1

---

#### Task 5.2: Update Main Documentation
**Estimate**: 0.5-1 hour | **Priority**: Medium

**File**: `CLAUDE.md`

- [ ] Add Reaper integration section
- [ ] Document new API methods
- [ ] Add usage examples
- [ ] Update feature list
- [ ] Add to table of contents

**Acceptance Criteria**:
- Documentation clear and complete
- Examples match actual API
- Properly formatted

**Dependencies**: Task 5.1

---

### Phase 6: Workflow B (Future - Optional)

#### Task 6.1: Implement Marker Parsing
**Estimate**: 2-3 hours | **Priority**: Low (Future)

**File**: `midi_drums/parsers/rpp_parser.py`

- [ ] Create `RPPParser` class
- [ ] Implement `parse_markers()` method
- [ ] Extract marker positions and names
- [ ] Convert positions to bars based on tempo
- [ ] Handle missing tempo/time signature

**Dependencies**: Task 3.1 (ReaperExporter complete)

---

#### Task 6.2: Implement Generate from Markers
**Estimate**: 2-3 hours | **Priority**: Low (Future)

**File**: `midi_drums/exporters/reaper_exporter.py`

- [ ] Implement `generate_from_markers()` method
- [ ] Parse .rpp markers
- [ ] Infer section types from marker names
- [ ] Generate Song structure
- [ ] Generate aligned MIDI patterns
- [ ] Export MIDI file

**Dependencies**: Task 6.1

---

## Task Dependencies Graph

```
1.1 (RPP Syntax Research)
  ↓
1.2 (Install rpp) → 1.3 (Prototype)
  ↓                    ↓
2.1 (Models)       2.2 (Time Calc)
  ↓                    ↓
  ↓                    ↓
  └─────→ 2.3 (ReaperEngine) ←─────┘
            ↓
        3.1 (ReaperExporter)
            ↓
  ┌─────────┼─────────┐
  ↓         ↓         ↓
4.1 (Unit) 4.2 (Unit) 4.3 (Integration)
  └─────────┼─────────┘
            ↓
  ┌─────────┼─────────┐
  ↓         ↓
5.1 (Examples) 5.2 (Docs)
```

## Time Estimates Summary

| Phase | Tasks | Estimate |
|-------|-------|----------|
| Phase 1: Research | 3 tasks | 2-4 hours |
| Phase 2: Engine | 3 tasks | 4-6 hours |
| Phase 3: API | 1 task | 2-3 hours |
| Phase 4: Testing | 3 tasks | 3-4 hours |
| Phase 5: Docs | 2 tasks | 1-2 hours |
| **TOTAL (MVP)** | **12 tasks** | **12-19 hours** |
| Phase 6: Workflow B | 2 tasks | 4-6 hours (future) |

## Progress Tracking

### Completed ✅
- [x] Architecture design
- [x] Task breakdown
- [x] Branch created

### In Progress 🚧
- [ ] Phase 1: Research

### Blocked ⏸️
- None currently

### Next Up ⏭️
- Task 1.1: Reverse-engineer .RPP marker syntax

## Notes

- **Critical Path**: Task 1.1 → 1.2 → 1.3 → 2.3 → 3.1 → 4.3
- **Can Parallelize**: Tasks 2.1, 2.2 can be done simultaneously
- **Testing**: Write tests alongside implementation (not at end)
- **Manual Validation**: Test each milestone in Reaper before proceeding
