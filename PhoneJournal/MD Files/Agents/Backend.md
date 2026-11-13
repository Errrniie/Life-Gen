# Backend (Architecture Notes)

This document captures everything in `workout_tracking_app_architecture_c2c01193.plan.md` that relates to **backend responsibilities** (data modeling, business logic, and persistence), without implementing anything yet.

## Scope & Intent

- **App type**: Android Jetpack Compose workout tracking app.
- **Backend meaning (in this project)**: In-app “backend” (domain + data layer + state/business logic) rather than a network server.
- **Persistence**: Not implemented yet; **Room** will be integrated later. Current state is **in-memory** (ViewModel state).
- **Architecture goal**: Compose-first UI, simple state management, minimal navigation complexity.

## Domain Model (Hierarchical)

The core data model is explicitly hierarchical:

**WorkoutSession → MuscleGroup → Exercise → SetEntry**

### `SetEntry`
- **Purpose**: Represents one set within an exercise.
- **Fields**:
  - `id: String`
  - `reps: Int` (default 0)
  - `weight: Float` (default 0.0f)
  - `comment: String?` (nullable, default null)
- **Persistence note**: Intended to become a Room Entity later.

### `Exercise`
- **Purpose**: Exercise within a muscle group.
- **Fields**:
  - `id: String`
  - `name: String`
  - `sets: MutableList<SetEntry>`
- **Domain operations**:
  - `addSet(...)`
  - `removeSet(index)` (bounds-checked)
  - optional `removeSetById(id)`

### `MuscleGroup`
- **Purpose**: Muscle group within a workout session.
- **Fields**:
  - `id: String`
  - `name: String`
  - `exercises: MutableList<Exercise>`
- **Domain operations**:
  - `addExercise(...)`
  - `removeExercise(id)`
  - `findExerciseById(id): Exercise?`

### `WorkoutSession`
- **Purpose**: Represents a complete workout session.
- **Fields**:
  - `id: String`
  - `name: String`
  - `date: Long` (timestamp)
  - `muscleGroups: MutableList<MuscleGroup>`
- **Domain operations**:
  - `addMuscleGroup(...)`
  - `removeMuscleGroup(id)`
  - `findMuscleGroupById(id): MuscleGroup?`
  - factory: `createNew(name)` sets id + `System.currentTimeMillis()` + empty groups

### Presets: `MuscleGroupPresets`
- **Purpose**: Provides predefined group names and validation/suggestions for UX.
- **Behavior**:
  - Preset list (e.g., Chest/Back/Legs/Shoulders/Arms/Core/Cardio/Full Body)
  - `getAllPresets()`
  - `isPreset(name)` case-insensitive
  - `getPresetSuggestions(query)` case-insensitive contains-filter

## Business Logic / State Ownership

All workout state and “backend logic” is centralized in `WorkoutViewModel` (app-level backend boundary for now).

### `WorkoutViewModel` responsibilities

- **State**:
  - `currentSession: StateFlow<WorkoutSession?>`
  - `allSessions: StateFlow<List<WorkoutSession>>`
  - `timerState: StateFlow<TimerState>`
- **Session management**:
  - `createNewSession(name)`
  - `loadSessions()` (in-memory for now)
  - `selectSession(id)`
- **CRUD over hierarchy**:
  - `addMuscleGroup(name)`, `removeMuscleGroup(groupId)`
  - `addExercise(groupId, exerciseName)`, `removeExercise(groupId, exerciseId)`
  - `addSet(groupId, exerciseId)`, `removeSet(groupId, exerciseId, setIndex)`
  - `updateSet(groupId, exerciseId, setIndex, reps, weight, comment)`
- **Timer control**:
  - `startTimer()`, `pauseTimer()`, `resetTimer()`

### Data mutation style

- The plan assumes **mutable lists** inside the domain objects for easy in-place edits.
- ViewModel operations mutate the current session tree, then expose updated state to UI for recomposition.
- Room integration later will replace/augment these mutations with DAO operations.

## Timer “Backend” Notes

- Timer is part of workout state; it is not persisted.
- Timer updates are intended to be driven by UI (Compose `LaunchedEffect`) observing `timerState`:
  - When running, elapsed time increments every second.
  - ViewModel exposes start/pause/reset controls via `timerState`.

## Persistence Roadmap (Room later)

Current phase is explicitly **no persistence**:

- All entities are plain Kotlin classes now.
- IDs are `String` (UUID suggested), with a note they can switch to `Long` when Room is added.
- When Room is added, `WorkoutViewModel` “data operations” will connect to DAO methods.

Practical implications for backend design later:

- The hierarchy implies either:
  - embedded relations (type converters / JSON blobs), or
  - normalized tables with one-to-many relationships across session/group/exercise/set,
  - plus careful ordering/indexing for stable set ordering (since UI uses `setIndex` now).

## Backend-Relevant Flows (as specified)

### Create new session
- User triggers create
- ViewModel creates new `WorkoutSession` with empty muscle groups
- Add to `allSessions`, set `currentSession`
- Navigate to session screen
- Timer may auto-start (optional)

### Add muscle group / exercise / set
- Dialog/UI collects name (for group/exercise)
- ViewModel adds node to the correct parent in the hierarchy
- UI updates via state observation

### Update set data
- Inline edit triggers `updateSet(...)` in ViewModel
- Updates `reps/weight/comment` for the indexed set

## Project Package Layout (Backend pieces)

- `com.journal.ernie.data.*`: Domain/data model classes (future Room entities).
- `com.journal.ernie.viewmodel.WorkoutViewModel`: Business logic, state, timer, CRUD.

## Non-goals / Explicit exclusions (for now)

- No server/backend API mentioned.
- No authentication, user accounts, or cloud sync in this plan.
- No Room schema/DAO defined yet—only “later” integration.

