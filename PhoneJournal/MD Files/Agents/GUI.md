# GUI (Compose) – Workout Tracking App

This document extracts **GUI/UI responsibilities** from `workout_tracking_app_architecture_c2c01193.plan.md` and reframes them as a UI-facing specification for implementation in **Jetpack Compose (Material3)**.

## UI goals

- **Compose-first UI** with Material3 components where reasonable.
- **Simple, state-based navigation** (no Navigation Compose library required).
- **Clear CRUD workflow** for workout data: `WorkoutSession → MuscleGroup → Exercise → SetEntry`.
- **Timer built into the workout session screen** (in-memory; not persisted).
- **Data persistence later** (Room planned; UI should not assume persistence exists yet).

## Screen hierarchy & routing

Navigation is a simple state machine (enum/sealed class suggested in the plan):

- `Home` → `WorkoutList` → `WorkoutSession`

Back behavior:

- **Back** returns to the previous screen (WorkoutSession → WorkoutList → Home).

Root navigation composable:

- **File**: `src/main/java/com/journal/ernie/ui/AppNavigation.kt`
- Uses a `when` on current screen and renders the corresponding screen composable.

## Screens

### `HomeScreen`

- **File**: `src/main/java/com/journal/ernie/ui/HomeScreen.kt`
- **Layout**: 5 large tappable navigation boxes (grid-like layout: “2x3 or similar”).
- **Behavior**:
  - **Center box** labeled **“Workout”** and navigates to `WorkoutListScreen`.
  - Other 4 boxes are placeholders: **disabled** or show **“Coming Soon”**.
- **UI components**:
  - Each box is a **Card** with `clickable` modifier.
- **Inputs/Outputs**:
  - Accepts navigation callback(s) from `AppNavigation`.

### `WorkoutListScreen` (Workout sessions list)

- **File**: `src/main/java/com/journal/ernie/ui/WorkoutListScreen.kt`
- **Purpose**: List all workout sessions.
- **Layout**:
  - `LazyColumn` of **session cards**.
  - **FAB** (bottom-right) to create a new session.
- **Session card content**:
  - **Name**
  - **Date**
  - **Summary** example: “3 muscle groups, 8 exercises”
- **States**:
  - **Empty state** when no sessions exist (message/CTA).
- **Interactions**:
  - Tap session → select session + navigate to `WorkoutSessionScreen`.
  - Tap FAB → show “Create session” dialog → create session → navigate to session.
  - Back → return to `HomeScreen`.

### `WorkoutSessionScreen` (Active workout)

- **File**: `src/main/java/com/journal/ernie/ui/WorkoutSessionScreen.kt`
- **Purpose**: Primary workout editing surface: timer + muscle groups + exercises + sets.
- **Layout**:
  - **Top section**: timer display + controls (start/pause/reset).
  - **Scrollable content**: muscle groups listed vertically (`LazyColumn` recommended).
- **Muscle group section**:
  - Shows muscle group **name**
  - Shows list of exercises within the group
  - Optional: expandable/collapsible per group (explicitly “optional” in plan)
- **Exercise section**:
  - Shows exercise **name**
  - Shows list of set rows
- **Set rows**:
  - Inline editing for **reps**, **weight**, **comment**
  - Edit/delete controls
- **Add actions**:
  - Add muscle group (screen-level button) → dialog with presets/suggestions
  - Add exercise (per muscle group)
  - Add set (per exercise; default reps=0, weight=0.0, comment empty/null)
- **Navigation**:
  - Back → return to `WorkoutListScreen`

## Reusable UI components (child composables)

### `TimerDisplay`

- **File**: `src/main/java/com/journal/ernie/ui/components/TimerDisplay.kt`
- **Inputs**:
  - `elapsedTime: Long` (seconds)
  - `isRunning: Boolean`
  - callbacks: `start`, `pause`, `reset`
- **Behavior**:
  - Formats time as **MM:SS** or **HH:MM:SS**.
  - Uses `LaunchedEffect` to tick while running (timer state owned by ViewModel).
- **Controls**:
  - 3 buttons: Start, Pause, Reset

### `MuscleGroupCard`

- **File**: `src/main/java/com/journal/ernie/ui/components/MuscleGroupCard.kt`
- **Inputs**:
  - `muscleGroup`
  - `onAddExercise`
  - `onRemoveGroup`
- **Displays**:
  - Muscle group name
  - List of exercises within the group
  - Add Exercise button
  - Remove Group button

### `ExerciseCard`

- **File**: `src/main/java/com/journal/ernie/ui/components/ExerciseCard.kt`
- **Inputs**:
  - `exercise`
  - `onAddSet`
  - `onRemoveExercise`
- **Displays**:
  - Exercise name
  - List of set rows
  - Add Set button
  - Remove Exercise button

### `SetRow`

- **File**: `src/main/java/com/journal/ernie/ui/components/SetRow.kt`
- **Inputs**:
  - `set`
  - `onUpdate(reps, weight, comment)`
  - `onDelete`
- **Behavior**:
  - Either always-editable fields or an **edit mode toggle** (plan mentions toggle).
  - Fields: reps, weight, comment (TextFields or Text displays).
  - Delete action available per row.

## Dialogs

### `AddMuscleGroupDialog`

- **File**: `src/main/java/com/journal/ernie/ui/dialogs/AddMuscleGroupDialog.kt`
- **Inputs**:
  - `onDismiss`
  - `onConfirm(name)`
- **UI requirements**:
  - TextField for muscle group name
  - Dropdown / suggestions based on presets
  - Allow preset selection OR custom input
  - Confirm + Cancel buttons
- **Presets source**:
  - `MuscleGroupPresets` (Chest, Back, Legs, Shoulders, Arms, Core, etc.)

### `AddExerciseDialog`

- **File**: `src/main/java/com/journal/ernie/ui/dialogs/AddExerciseDialog.kt`
- **Inputs**:
  - `onDismiss`
  - `onConfirm(name)`
- **UI requirements**:
  - TextField for exercise name
  - Confirm + Cancel buttons

## UI ↔ ViewModel contract (what the GUI calls)

The GUI layer should only invoke ViewModel functions and render state:

- **Session management**
  - `createNewSession(name)`
  - `loadSessions()`
  - `selectSession(id)`
- **Muscle groups**
  - `addMuscleGroup(name)`
  - `removeMuscleGroup(groupId)`
- **Exercises**
  - `addExercise(groupId, exerciseName)`
  - `removeExercise(groupId, exerciseId)`
- **Sets**
  - `addSet(groupId, exerciseId)`
  - `removeSet(groupId, exerciseId, setIndex)`
  - `updateSet(groupId, exerciseId, setIndex, reps, weight, comment)`
- **Timer**
  - `startTimer()`, `pauseTimer()`, `resetTimer()`

Observed state for rendering:

- `allSessions: StateFlow<List<WorkoutSession>>`
- `currentSession: StateFlow<WorkoutSession?>`
- `timerState: StateFlow<TimerState>`

## UX notes & constraints from the plan

- **In-memory only**: UI must tolerate app restarts losing data until Room is integrated.
- **Validation/polish planned**:
  - prevent empty names (phase 9 in plan)
  - empty states on list screens
- **Editing sets**: set entries default to (0 reps, 0.0 weight, empty comment) and are edited inline.
- **Remembering input**: consider `rememberSaveable` for dialog input state (explicitly suggested).

