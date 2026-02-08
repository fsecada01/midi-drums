# Physical Feasibility Fixes for MIDI Drum Generation

## Problem Statement

The MIDI drum generator currently produces patterns that are **physically impossible** for real drummers to play. Specifically, the composite drummer plugin (`composite_doom_blues`) generates simultaneous ride cymbal and hi-hat (hand) hits, which cannot be played by a human drummer who has only 2 hands.

### Discovered Issue

**File**: `midi_drums/plugins/drummers/composite_doom_blues.py`

The composite drummer layers three different drummer styles (Roeder, Porcaro, Chambers) sequentially without validating physical constraints:

```python
styled_pattern = self.roeder.apply_style(styled_pattern)   # Layer 1
styled_pattern = self.porcaro.apply_style(styled_pattern)  # Layer 2
styled_pattern = self.chambers.apply_style(styled_pattern) # Layer 3
```

Each drummer may add beats to the pattern, resulting in:
- ❌ Ride cymbal + Hi-hat (hand) at same timing
- ❌ More than 2 simultaneous hand-played instruments
- ❌ Patterns that sound good but are unplayable

## Physical Constraints of Drummers

### Limb Assignments

A drummer has exactly **4 limbs** with specific roles:

| Limb | Primary Function | Can Play |
|------|------------------|----------|
| Right Hand | Timekeeping/Lead | Ride, Hi-hat, Crash, Snare, Toms |
| Left Hand | Backbeat/Fill | Snare, Hi-hat, Toms, Crash |
| Right Foot | Bass Drum | Kick drum pedal only |
| Left Foot | Hi-hat Control | Hi-hat pedal (open/close/chick) |

### Critical Rules

1. **Maximum 2 simultaneous hand strikes** - Cannot play 3+ drums/cymbals at once
2. **Ride OR Hi-hat, not both** - Timekeeping uses either ride (hand) OR hi-hat (hand)
3. **Hi-hat foot pedal exception** - When riding on ride cymbal, hi-hat foot pedal can add "chick" sounds
4. **Kick drum is right foot only** - Left foot is reserved for hi-hat pedal

### Ride vs Hi-Hat Usage Patterns

**Low Energy Sections (Verse, Intro)**:
- ✅ Hi-hat (hand) for timekeeping
- ✅ Optional: Hi-hat foot pedal for additional texture

**High Energy Sections (Chorus, Bridge)**:
- ✅ Ride cymbal (hand) for timekeeping
- ✅ Hi-hat foot pedal for offbeat "chick" sounds
- ❌ NO simultaneous hi-hat hand hits

## Research Sources

### Industry Best Practices

1. **[MusicRadar - Programming Realistic Drums](https://www.musicradar.com/how-to/how-to-program-drums-that-sound-like-they-were-played-by-a-real-drummer)**
   - "Most drummers have only a finite number of limbs with which to play - with two legs and two arms at their disposal"
   - "Any percussion part you write should be something an actual drummer could play"

2. **[Loopmasters - 5 Advanced Tips](https://www.loopmasters.com/articles/4436-How-to-Program-Realistic-MIDI-Drums-5-advanced-tips-for-virtual-drummers)**
   - Drummers can only hit two drums with their sticks at any one time
   - Ride cymbal is an alternative to the hi-hats (not simultaneous)

3. **[Sweetwater - 6 Tips for Realistic Drums](https://www.sweetwater.com/insync/6-tips-for-programming-more-realistic-sounding-drums/)**
   - Real drummers don't strike every drum with the same force
   - Timing humanization is critical for realism

### Machine Learning Approaches

4. **[Google Magenta - GrooVAE](https://magenta.tensorflow.org/groovae)**
   - Trained on 13.6 hours of professional drummers on Roland TD-11 MIDI kit
   - Separates "score" (what to play) from "groove" (how to play it)
   - Captures velocity variations and microtiming deviations

5. **[Groove MIDI Dataset (GMD)](https://magenta.tensorflow.org/datasets/groove)**
   - Publicly available dataset of real drummer performances
   - All patterns are guaranteed physically feasible
   - 15 hours of professional drummers with full MIDI capture

## Proposed Solutions

### Issue #1: Physical Feasibility Validator

**Priority**: High
**Branch**: `feat/physical-feasibility-validator`

Create a validation system to detect impossible patterns:

**File**: `midi_drums/validation/physical_constraints.py`

**Features**:
- Detect simultaneous hand hits exceeding 2
- Identify ride + hi-hat (hand) conflicts
- Track limb assignments per beat
- Provide detailed conflict reports
- Suggest automatic fixes

**Test Coverage**:
- ✅ Valid patterns pass validation
- ✅ Ride + hi-hat conflicts detected
- ✅ 3+ simultaneous hands detected
- ✅ Foot instruments validated correctly

### Issue #2: Pattern Conflict Resolution Utility

**Priority**: High (Quick Win)
**Branch**: `feat/pattern-conflict-resolver`

Create utility to automatically fix impossible patterns:

**File**: `midi_drums/utils/pattern_fixer.py`

**Features**:
- Remove hi-hat hand hits when ride is present
- Convert hi-hat hand to foot pedal where appropriate
- Preserve musical intent while ensuring playability
- Logging of all modifications made

**Test Coverage**:
- ✅ Ride + hi-hat conflicts resolved
- ✅ Hi-hat converted to foot pedal correctly
- ✅ Original pattern preserved when valid
- ✅ Velocity adjustments for foot pedal

### Issue #3: Composite Drummer Conflict Resolution

**Priority**: High
**Branch**: `feat/composite-drummer-validation`

Update composite drummer to validate and fix patterns:

**File**: `midi_drums/plugins/drummers/composite_doom_blues.py`

**Changes**:
- Add physical validation after layering
- Apply conflict resolution automatically
- Log conflicts and resolutions
- Maintain sonic quality while ensuring playability

**Test Coverage**:
- ✅ Composite drummer produces valid patterns
- ✅ All sections validated (verse, chorus, bridge, etc.)
- ✅ No ride + hi-hat conflicts in output
- ✅ MIDI export works correctly

### Issue #4: Ride/Hi-hat Switching Logic

**Priority**: Medium
**Branch**: `feat/intelligent-ride-hihat-switching`

Add intelligent ride vs hi-hat selection in genre plugins:

**Files**:
- `midi_drums/plugins/genres/metal.py`
- `midi_drums/plugins/genres/rock.py`
- Other genre plugins as needed

**Features**:
- Section-based switching (verse = hi-hat, chorus = ride)
- Energy-based switching (low energy = hi-hat, high = ride)
- Automatic hi-hat foot pedal when on ride
- Configurable via GenerationParameters

**Test Coverage**:
- ✅ Verses use hi-hat timekeeping
- ✅ Choruses use ride timekeeping
- ✅ Hi-hat foot pedal added when riding
- ✅ Energy threshold switching works

### Issue #5: ML-Based Validation (Future)

**Priority**: Low (Future Enhancement)
**Branch**: `feat/ml-groove-validation`

Integrate Groove MIDI Dataset for pattern validation:

**Features**:
- Download and parse GMD
- Compare generated patterns against real drummer data
- ML-based "realism score"
- Pattern similarity matching
- Hybrid rule-based + ML approach

## Implementation Plan

### Phase 1: Core Validation (Week 1)

1. ✅ Create documentation (this file)
2. ⬜ Create GitHub issues for each problem
3. ⬜ Create feature branches
4. ⬜ Implement `PhysicalValidator` class
5. ⬜ Implement `pattern_fixer` utility
6. ⬜ Create comprehensive test suite
7. ⬜ Update composite drummer plugin

### Phase 2: Genre Plugin Updates (Week 2)

1. ⬜ Add ride/hi-hat switching to Metal genre
2. ⬜ Add ride/hi-hat switching to Rock genre
3. ⬜ Add ride/hi-hat switching to Jazz genre
4. ⬜ Add ride/hi-hat switching to Funk genre
5. ⬜ Update all tests for new behavior

### Phase 3: CI/CD & Quality (Week 2-3)

1. ⬜ Create GitHub Actions workflow
2. ⬜ Run tests on feature branches
3. ⬜ Run tests on PRs
4. ⬜ Run tests on main branch commits
5. ⬜ Add coverage reporting

### Phase 4: ML Integration (Future)

1. ⬜ Download Groove MIDI Dataset
2. ⬜ Create dataset parser
3. ⬜ Implement pattern similarity matching
4. ⬜ Train or use pre-trained GrooVAE
5. ⬜ Integrate as validation step

## Testing Strategy

### Unit Tests

**File**: `tests/unit/test_physical_validator.py`
- Test limb assignment logic
- Test conflict detection
- Test each constraint rule
- Test edge cases

**File**: `tests/unit/test_pattern_fixer.py`
- Test conflict resolution
- Test hi-hat to pedal conversion
- Test pattern preservation
- Test logging output

### Integration Tests

**File**: `tests/integration/test_composite_drummer_validation.py`
- Test composite drummer with validation
- Test full song generation
- Test all sections (verse, chorus, bridge, etc.)
- Test MIDI export validity

**File**: `tests/integration/test_genre_ride_hihat.py`
- Test ride/hi-hat switching per genre
- Test energy-based switching
- Test section-based switching
- Test foot pedal additions

### Validation Tests

**File**: `tests/validation/test_doom_blues_output.py`
- Load actual generated doom_blues_composite file
- Validate no physical conflicts
- Check all sections individually
- Verify MIDI note mappings

## Success Criteria

✅ **All generated patterns are physically playable by real drummers**
✅ **No ride + hi-hat (hand) conflicts in any output**
✅ **Hi-hat foot pedal used appropriately when on ride**
✅ **All tests pass with 100% success rate**
✅ **CI/CD pipeline validates all changes**
✅ **Documentation updated with new constraints**

## MIDI Note Reference

From `midi_drums/models/pattern.py`:

### Hi-Hat Instruments (Hand)
- `CLOSED_HH = 42` (GM standard)
- `CLOSED_HH_EDGE = 22` (EZDrummer specific)
- `CLOSED_HH_TIP = 61` (EZDrummer specific)
- `TIGHT_HH_EDGE = 62` (EZDrummer specific)
- `TIGHT_HH_TIP = 63` (EZDrummer specific)
- `OPEN_HH = 46` (GM standard)
- `OPEN_HH_1 = 24` (EZDrummer specific)
- `OPEN_HH_2 = 25` (EZDrummer specific)
- `OPEN_HH_3 = 26` (EZDrummer specific)
- `OPEN_HH_MAX = 60` (EZDrummer specific)

### Hi-Hat Foot Pedal
- `PEDAL_HH = 44` ✅ Can be used with ride simultaneously

### Ride Cymbal
- `RIDE = 51`
- `RIDE_BELL = 53`

### Conflict Detection Rule

```python
RIDE_INSTRUMENTS = {51, 53}  # RIDE, RIDE_BELL
HIHAT_HAND_INSTRUMENTS = {22, 24, 25, 26, 42, 46, 60, 61, 62, 63}
HIHAT_FOOT = {44}  # PEDAL_HH - NO CONFLICT with ride

# This is INVALID:
if RIDE in beats AND any(HIHAT_HAND_INSTRUMENTS) in beats:
    raise PhysicalConflict("Ride and hi-hat hand cannot play simultaneously")

# This is VALID:
if RIDE in beats AND HIHAT_FOOT in beats:
    # OK - right hand on ride, left foot on hi-hat pedal
    pass
```

## Progress Tracking

- [ ] Issue #1: Physical Feasibility Validator
- [ ] Issue #2: Pattern Conflict Resolver
- [ ] Issue #3: Composite Drummer Validation
- [ ] Issue #4: Ride/Hi-hat Switching Logic
- [ ] Issue #5: CI/CD GitHub Actions
- [ ] Issue #6: ML-Based Validation (Future)

## References

- [MusicRadar - How to program drums that sound like the real thing](https://www.musicradar.com/how-to/how-to-program-drums-that-sound-like-they-were-played-by-a-real-drummer)
- [Loopmasters - How to Program Realistic MIDI Drums](https://www.loopmasters.com/articles/4436-How-to-Program-Realistic-MIDI-Drums-5-advanced-tips-for-virtual-drummers)
- [Google Magenta - GrooVAE](https://magenta.tensorflow.org/groovae)
- [Groove MIDI Dataset](https://magenta.tensorflow.org/datasets/groove)
- [Sweetwater - 6 Tips for Programming Realistic Drums](https://www.sweetwater.com/insync/6-tips-for-programming-more-realistic-sounding-drums/)
- [MusicRadar - How to program realistic drum parts](https://www.musicradar.com/tuition/tech/how-to-program-realistic-drum-parts-humanising-and-variation-607733)
