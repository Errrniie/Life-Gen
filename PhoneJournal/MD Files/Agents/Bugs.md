# Bugs (Architecture-Derived Risk List)

This document lists **likely bugs and failure modes** implied by `workout_tracking_app_architecture_c2c01193.plan.md`, focusing on areas that commonly break in a Compose-first, mutable in-memory, hierarchical workout editor with a timer.

## Highest-risk bug clusters

### Timer (lifecycle, recomposition, drift)
- **Multiple timer coroutines**: If `TimerDisplay` uses `LaunchedEffect` keyed incorrectly (or keyed to a changing value), recomposition can accidentally start multiple loops, causing time to advance too fast.
- **Timer keeps running in background**: Navigating away from `WorkoutSessionScreen` without cancelling work can keep incrementing elapsed time (battery drain, unexpected timer state).
- **Drift / skipped seconds**: Using `delay(1000)` loop in UI scope can drift under load. A monotonic clock approach (compute \(now - start\)) avoids drift.
- **State source-of-truth mismatch**: If elapsed time is updated in UI *and* ViewModel, they can fight (jumping time, stutters).
- **Reset/start edge cases**: Rapid tapping Start/Pause/Reset can produce negative elapsed time, duplicate start timestamps, or “running=false but still ticking”.

### Mutable nested lists (Compose state not updating)
- **UI doesn’t refresh after edits**: Mutating a `MutableList` nested inside a state object often won’t trigger recomposition unless the outer state reference changes. Symptoms: add/remove set “works” in data but UI doesn’t change.
- **In-place mutation breaks StateFlow expectations**: If `StateFlow` emits the same instance with mutated internals, collectors may not recompose depending on how state is exposed/collected.
- **Accidental shared references**: Copying sessions/groups/exercises shallowly can cause edits in one place to mutate another session unexpectedly.

### ID vs index correctness
- **Wrong item edited/deleted**: Using list index for identity (especially inside LazyColumn) causes “edit set A changes set B” after insert/remove.
- **Out-of-bounds crashes**: `removeSet(index)` / `updateSet(..., setIndex, ...)` can crash when the UI sends a stale index after list changes.
- **Duplicate IDs**: If UUID generation is inconsistent (or replaced by counter later), duplicates break find/remove operations.

### Navigation and “current session” validity
- **Null currentSession crashes**: `WorkoutSessionScreen` may assume `currentSession != null` and crash when navigating quickly or after deleting a session.
- **Stale selection**: Deleting a session from `allSessions` but not clearing `currentSession` leads to editing an object no longer present in the list.
- **Back navigation resets state unexpectedly**: If navigation is a simple enum without saving state, returning to `WorkoutSessionScreen` might recreate state and lose edits/timer.

### Dialog input validation
- **Empty/whitespace names allowed**: Leads to unreadable lists, duplicate-looking items, and invalid “preset match” behavior.
- **Case-insensitive duplicates**: “Chest” vs “chest” duplicates if validation isn’t normalized.
- **Dismiss/confirm race**: If dialog state isn’t `rememberSaveable`, rotation/process recreation can drop user input mid-entry.

## Data-model-specific pitfalls (from the plan)

### `SetEntry` (reps/weight/comment)
- **Negative values**: reps/weight can become negative via free-text input unless validated.
- **Float parsing crashes**: Entering “.” or “1..2” in weight field can crash if parsed eagerly.
- **Locale decimal separator**: Some locales use comma (`,`) and parsing can fail.

### `Exercise` / `MuscleGroup` / `WorkoutSession`
- **Remove methods silently fail**: Removing by ID without feedback can make UI look broken when ID isn’t found.
- **Summary counts wrong**: `WorkoutListScreen` summary (“3 muscle groups, 8 exercises”) can desync if computed from stale snapshots or shared references.
- **Timestamp units mismatch**: Plan mentions “Long timestamp” and also “milliseconds since epoch”; mixing seconds vs millis causes wrong dates.

## Compose UI pitfalls likely to surface

### Lazy lists and keys
- **Item recycling bugs**: Without stable `key` in `LazyColumn`, text fields can show values from other rows after scrolling.
- **TextField state resets**: Using local `remember` state per row without a stable key can reset inputs on recomposition/scroll.

### Editable rows
- **Two-way binding loops**: If `onValueChange` updates ViewModel on every keystroke and ViewModel emits state that overwrites the field, typing can become jittery or impossible.
- **Performance degradation**: Large nested lists with immediate state updates can cause jank; this appears as “laggy typing” in set rows.

## Room migration “future bug” list (design decisions now affect later)
- **Mutable lists don’t map cleanly**: Room prefers normalized tables; direct `List<SetEntry>` fields require converters or relations. Early APIs that assume nested lists can become expensive to migrate.
- **String IDs vs Long PK**: If IDs later switch types, any code using string comparisons (or UI keys) will require careful migration.
- **Cascade delete expectations**: Users expect deleting a session deletes groups/exercises/sets; Room needs explicit relations and delete strategy.

## Quick “bug smell” checklist for this project
- **Timer**: Does elapsed time ever increment faster than real time? Does it keep running after leaving the screen?
- **CRUD**: After add/remove/edit, does the UI immediately reflect the change without needing to navigate away and back?
- **Editing**: Do edits apply to the correct row after inserting/deleting above it?
- **Stability**: Can rapid tapping (add/remove/start/pause) crash the app?
- **Scrolling**: Do TextFields keep their own values while scrolling (no value swapping)?

## Suggested priorities (when fixing bugs)
1. **Crashes/data corruption**: index out-of-bounds, null current session, wrong item edited/deleted.
2. **Timer correctness**: multiple loops, background running, drift.
3. **State consistency**: ensure updates actually recompose and persist across navigation.
4. **Input robustness**: parsing/validation for reps/weight/comment.

