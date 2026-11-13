# Architecture (Workout Tracking App)

## Purpose

This document is the architecture “source of truth” for the workout tracking portion of the app. It defines the intended screen flow, data model, state ownership, package structure, and how the app should evolve (notably: adding Room persistence later).

## Product Scope (Current Phases)

- **Compose-first Android UI** with a simple, maintainable structure.
- **Home screen** with **5 navigation boxes**.
  - Only the **center box** navigates to the **Workout** section.
  - The other 4 boxes are placeholders (“Coming Soon” / disabled).
- **Workout section** supports:
  - Managing multiple **workout sessions** (create/select/list).
  - Editing an active session using a strict hierarchy:
    - `WorkoutSession → MuscleGroup → Exercise → SetEntry`
  - Built-in **timer** to track workout duration.

## Non-Goals (For Now)

- No persistence yet (in-memory state only).
- No cloud sync/export.
- No complex navigation framework required (avoid Navigation Compose for now).
- No Room entities/DAOs until the “persistence phase”.

## Screen Map & Navigation

### Screen hierarchy

- `HomeScreen`
  - Displays 5 large tap targets.
  - Center tile navigates to the workout area.
- `WorkoutListScreen`
  - Shows list of workout sessions.
  - FAB to create a new session.
  - Selecting a session navigates to the active session screen.
- `WorkoutSessionScreen`
  - Main workout editor.
  - Timer + nested list editing (groups → exercises → sets).

### Navigation strategy

- Use a **simple state-based router** (enum/sealed class) and a `when` switch.
- Root navigation composable: `AppNavigation`.
- Back navigation returns to the prior screen:
  - `WorkoutSessionScreen` → `WorkoutListScreen` → `HomeScreen`.

This is intentionally minimal and should remain so until navigation needs justify a library.

## Data Model (Domain Layer)

The domain model is hierarchical and **editable**:

1. **WorkoutSession**
   - `id: String`
   - `name: String`
   - `date: Long` (epoch ms)
   - `muscleGroups: MutableList<MuscleGroup>`
   - Operations: `addMuscleGroup`, `removeMuscleGroup`, `findMuscleGroupById`
2. **MuscleGroup**
   - `id: String`
   - `name: String`
   - `exercises: MutableList<Exercise>`
   - Operations: `addExercise`, `removeExercise`, `findExerciseById`
3. **Exercise**
   - `id: String`
   - `name: String`
   - `sets: MutableList<SetEntry>`
   - Operations: `addSet`, `removeSet(index)`, `removeSetById`
4. **SetEntry**
   - `id: String`
   - `reps: Int`
   - `weight: Float`
   - `comment: String?`

### Presets

- `MuscleGroupPresets` provides:
  - A list of common group names (Chest, Back, Legs, etc.).
  - `getAllPresets()`
  - `isPreset(name)` (case-insensitive)
  - `getPresetSuggestions(query)` for dialog autocomplete.

### IDs

- IDs are **Strings** (UUID-style) for now.
- This is expected to be revisited when Room is introduced (String or Long both acceptable; choose based on Room schema design).

## State Ownership & Data Flow

### Single source of truth

All workout state and business logic lives in **one ViewModel**:

- `WorkoutViewModel`
  - `allSessions: StateFlow<List<WorkoutSession>>`
  - `currentSession: StateFlow<WorkoutSession?>`
  - `timerState: StateFlow<TimerState>`

The UI layer:

- Observes these flows (collect-as-state).
- Triggers mutations exclusively through ViewModel methods.

### Core flows

**Create new session**

- User taps FAB in `WorkoutListScreen`.
- ViewModel creates a new `WorkoutSession` (empty lists).
- Adds it to `allSessions`, sets `currentSession`.
- Navigate to `WorkoutSessionScreen`.
- Optionally auto-start timer.

**Add muscle group**

- User opens add-group dialog on `WorkoutSessionScreen`.
- ViewModel adds a `MuscleGroup` to `currentSession`.

**Add exercise**

- User opens add-exercise dialog from a `MuscleGroupCard`.
- ViewModel adds an `Exercise` under a muscle group by id.

**Add set / update set**

- User taps “Add Set” inside an `ExerciseCard`.
- ViewModel appends a default `SetEntry`.
- Editing reps/weight/comment calls `updateSet(...)`.

## Timer Architecture

Timer is part of workout state but does not need persistence yet.

- `TimerDisplay` renders elapsed time and controls.
- Controls call ViewModel functions:
  - `startTimer()`, `pauseTimer()`, `resetTimer()`
- UI updates by observing `timerState`.
- Compose can tick time via `LaunchedEffect` while running.

If/when timer persistence is needed, the design should move tick ownership into the ViewModel and store timestamps rather than relying on UI tick loops.

## UI Composition Strategy

Keep the `WorkoutSessionScreen` readable by composing it from focused child components:

- `TimerDisplay` (timer header + controls)
- `MuscleGroupCard` (group container)
- `ExerciseCard` (exercise container)
- `SetRow` (set editor row)
- Dialogs:
  - `AddMuscleGroupDialog` (with preset suggestions)
  - `AddExerciseDialog`

Avoid deeply nested state in composables; pass ids + callbacks that call the ViewModel.

## Package / Module Layout

Target package structure:

```
com.journal.ernie/
├── MainActivity.kt
├── data/
│   ├── SetEntry.kt
│   ├── Exercise.kt
│   ├── MuscleGroup.kt
│   ├── WorkoutSession.kt
│   └── MuscleGroupPresets.kt
├── viewmodel/
│   └── WorkoutViewModel.kt
└── ui/
    ├── AppNavigation.kt
    ├── HomeScreen.kt
    ├── WorkoutListScreen.kt
    ├── WorkoutSessionScreen.kt
    ├── components/
    │   ├── MuscleGroupCard.kt
    │   ├── ExerciseCard.kt
    │   ├── SetRow.kt
    │   └── TimerDisplay.kt
    └── dialogs/
        ├── AddMuscleGroupDialog.kt
        └── AddExerciseDialog.kt
```

## Future Evolution: Room Integration (Planned)

Room will be added later. When that happens:

- Convert domain models to Room entities (or introduce separate entity models + mappers).
- Introduce DAOs and a repository layer to decouple persistence from UI.
- Update ViewModel methods to operate through repository/DAO rather than in-memory lists.

Until then, keep the architecture small: domain models + ViewModel + Compose UI.

