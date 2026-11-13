---
name: Workout Tracking App Architecture
overview: Design the architecture for a workout tracking app with a home screen (5 navigation boxes), workout session management, hierarchical data model (WorkoutSession → MuscleGroup → Exercise → SetEntry), and a built-in timer. Focus on Compose-first UI and simple state management.
todos: []
---

# Workout Tracking App Architecture Plan

## Feature Summary

Build a workout tracking app with a home screen containing 5 navigation boxes, where the center box leads to a Workout section. The Workout section manages multiple workout sessions, each containing muscle groups, exercises, and sets. Includes a timer for tracking workout duration. Data persistence will be added later via Room database.

## Architecture Overview

```
┌──────────────────┐
│   MainActivity   │
│  (Entry Point)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   HomeScreen     │
│  (5 Nav Boxes)   │
└────────┬─────────┘
         │
         ▼ (Center Box)
┌──────────────────┐
│ WorkoutListScreen│
│ (Session List)   │
└────────┬─────────┘
         │
         ▼ (Create/Select Session)
┌──────────────────┐
│WorkoutSessionScreen│
│ (Active Workout) │
└──────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│Workout │ │Workout   │
│ViewModel│ │DataModels│
└────────┘ └──────────┘
```

## Files to Create

### Data Models Layer

**File:** `src/main/java/com/journal/ernie/data/SetEntry.kt`

- **Responsibility:** Data class representing a single set within an exercise
- **Contains:** 
  - Properties: reps (Int), weight (Float), comment (String?)
  - Unique identifier for the set
- **Note:** Will become Room Entity later

**File:** `src/main/java/com/journal/ernie/data/Exercise.kt`

- **Responsibility:** Data class representing an exercise within a muscle group
- **Contains:**
  - Properties: name (String), sets (List<SetEntry>)
  - Unique identifier for the exercise
  - Methods: addSet(), removeSet(index)
- **Note:** Will become Room Entity later

**File:** `src/main/java/com/journal/ernie/data/MuscleGroup.kt`

- **Responsibility:** Data class representing a muscle group within a workout session
- **Contains:**
  - Properties: name (String), exercises (List<Exercise>)
  - Unique identifier for the muscle group
  - Methods: addExercise(), removeExercise(id)
- **Note:** Will become Room Entity later

**File:** `src/main/java/com/journal/ernie/data/WorkoutSession.kt`

- **Responsibility:** Data class representing a complete workout session
- **Contains:**
  - Properties: id, name/title (String), date (Long timestamp), muscleGroups (List<MuscleGroup>)
  - Methods: addMuscleGroup(), removeMuscleGroup(id)
- **Note:** Will become Room Entity later

**File:** `src/main/java/com/journal/ernie/data/MuscleGroupPresets.kt`

- **Responsibility:** Provides predefined muscle group names
- **Contains:**
  - Object/companion with list of common muscle groups (Chest, Back, Legs, Shoulders, Arms, Core, etc.)
  - Function to get all presets
  - Function to validate if a name is a preset

### ViewModel Layer

**File:** `src/main/java/com/journal/ernie/viewmodel/WorkoutViewModel.kt`

- **Responsibility:** Manages all workout-related state and business logic
- **Contains:**
  - State: currentSession (StateFlow<WorkoutSession?>), allSessions (StateFlow<List<WorkoutSession>>), timerState (StateFlow<TimerState>)
  - Functions:
    - createNewSession(name): Creates new workout session
    - loadSessions(): Loads all workout sessions (from memory for now)
    - selectSession(id): Sets current session
    - addMuscleGroup(name): Adds muscle group to current session
    - removeMuscleGroup(groupId): Removes muscle group
    - addExercise(groupId, exerciseName): Adds exercise to muscle group
    - removeExercise(groupId, exerciseId): Removes exercise
    - addSet(groupId, exerciseId): Adds set to exercise
    - removeSet(groupId, exerciseId, setIndex): Removes set
    - updateSet(groupId, exerciseId, setIndex, reps, weight, comment): Updates set data
    - Timer functions: startTimer(), pauseTimer(), resetTimer()
- **Note:** All data operations will later connect to Room DAO

### UI Layer - Navigation & Main

**File:** `src/main/java/com/journal/ernie/MainActivity.kt`

- **Responsibility:** App entry point, sets up Compose UI and navigation state
- **Contains:**
  - Class extending ComponentActivity
  - Navigation state management (enum or sealed class for screens)
  - ViewModel initialization
  - setContent { AppNavigation() }

**File:** `src/main/java/com/journal/ernie/ui/AppNavigation.kt`

- **Responsibility:** Root navigation composable, routes between Home and Workout screens
- **Contains:**
  - @Composable function
  - Navigation state (Home, WorkoutList, WorkoutSession)
  - Switch/When statement routing to appropriate screen
  - Passes ViewModel and navigation callbacks to screens

### UI Layer - Home Screen

**File:** `src/main/java/com/journal/ernie/ui/HomeScreen.kt`

- **Responsibility:** Displays 5 large tappable navigation boxes
- **Contains:**
  - @Composable function
  - Grid or Column layout with 5 boxes
  - Center box navigates to Workout section
  - Other 4 boxes are placeholders (disabled or show "Coming Soon")
  - Each box is a Card with clickable modifier
  - Navigation callback to AppNavigation

### UI Layer - Workout Screens

**File:** `src/main/java/com/journal/ernie/ui/WorkoutListScreen.kt`

- **Responsibility:** Displays list of all workout sessions
- **Contains:**
  - @Composable function
  - Observe allSessions from ViewModel
  - LazyColumn displaying session cards (name, date, summary)
  - FAB to create new session
  - Click on session: navigate to WorkoutSessionScreen
  - Empty state: message when no sessions exist
  - Back button to return to Home

**File:** `src/main/java/com/journal/ernie/ui/WorkoutSessionScreen.kt`

- **Responsibility:** Main workout screen with timer, muscle groups, exercises, and sets
- **Contains:**
  - @Composable function
  - Timer display and controls (start/pause/reset buttons)
  - LazyColumn of muscle groups
  - Each muscle group shows: name, list of exercises
  - Each exercise shows: name, list of sets with reps/weight/comment
  - Add muscle group button/dialog
  - Add exercise button per muscle group
  - Add set button per exercise
  - Edit/delete controls for sets
  - Back button to return to WorkoutListScreen
- **Note:** This is the most complex screen, will use multiple child composables

**File:** `src/main/java/com/journal/ernie/ui/components/MuscleGroupCard.kt`

- **Responsibility:** Reusable card component for displaying a muscle group
- **Contains:**
  - @Composable function
  - Parameters: muscleGroup, onAddExercise callback, onRemoveGroup callback
  - Displays muscle group name
  - List of exercises within the group
  - Add exercise button
  - Remove group button

**File:** `src/main/java/com/journal/ernie/ui/components/ExerciseCard.kt`

- **Responsibility:** Reusable card component for displaying an exercise
- **Contains:**
  - @Composable function
  - Parameters: exercise, onAddSet callback, onRemoveExercise callback
  - Displays exercise name
  - List of sets with reps/weight/comment
  - Add set button
  - Remove exercise button

**File:** `src/main/java/com/journal/ernie/ui/components/SetRow.kt`

- **Responsibility:** Reusable row component for displaying/editing a single set
- **Contains:**
  - @Composable function
  - Parameters: set, onUpdate callback, onDelete callback
  - TextFields or Text displays for reps, weight, comment
  - Edit mode toggle
  - Delete button

**File:** `src/main/java/com/journal/ernie/ui/components/TimerDisplay.kt`

- **Responsibility:** Reusable timer component
- **Contains:**
  - @Composable function
  - Parameters: elapsedTime (Long in seconds), isRunning (Boolean), callbacks (start, pause, reset)
  - Displays formatted time (MM:SS or HH:MM:SS)
  - Three buttons: Start, Pause, Reset
  - Uses LaunchedEffect to update timer when running

**File:** `src/main/java/com/journal/ernie/ui/dialogs/AddMuscleGroupDialog.kt`

- **Responsibility:** Dialog for adding a new muscle group
- **Contains:**
  - @Composable function
  - Parameters: onDismiss, onConfirm callback
  - TextField for muscle group name
  - Dropdown or suggestions showing preset muscle groups
  - Option to use preset or enter custom name
  - Confirm and Cancel buttons

**File:** `src/main/java/com/journal/ernie/ui/dialogs/AddExerciseDialog.kt`

- **Responsibility:** Dialog for adding a new exercise
- **Contains:**
  - @Composable function
  - Parameters: onDismiss, onConfirm callback
  - TextField for exercise name
  - Confirm and Cancel buttons

## Data Flow

### Creating a New Workout Session

1. User taps FAB in WorkoutListScreen
2. Dialog prompts for session name
3. ViewModel.createNewSession(name) called
4. New WorkoutSession created with empty muscleGroups list
5. Session added to allSessions list
6. currentSession set to new session
7. Navigation to WorkoutSessionScreen
8. Timer starts automatically (optional)

### Adding a Muscle Group

1. User taps "Add Muscle Group" in WorkoutSessionScreen
2. AddMuscleGroupDialog opens
3. User selects preset or enters custom name
4. ViewModel.addMuscleGroup(name) called
5. New MuscleGroup added to currentSession.muscleGroups
6. UI updates to show new muscle group

### Adding an Exercise

1. User taps "Add Exercise" in MuscleGroupCard
2. AddExerciseDialog opens
3. User enters exercise name
4. ViewModel.addExercise(groupId, name) called
5. New Exercise added to muscleGroup.exercises
6. UI updates to show new exercise

### Adding a Set

1. User taps "Add Set" in ExerciseCard
2. ViewModel.addSet(groupId, exerciseId) called
3. New SetEntry (with default reps=0, weight=0.0) added to exercise.sets
4. UI updates to show new set row

### Updating Set Data

1. User edits reps/weight/comment in SetRow
2. On text change, ViewModel.updateSet(groupId, exerciseId, setIndex, newReps, newWeight, newComment) called
3. SetEntry updated in data model
4. UI reflects changes

### Timer Flow

1. TimerDisplay observes timerState from ViewModel
2. User taps Start → ViewModel.startTimer() → timerState.isRunning = true
3. LaunchedEffect in TimerDisplay updates elapsedTime every second
4. User taps Pause → ViewModel.pauseTimer() → timerState.isRunning = false
5. User taps Reset → ViewModel.resetTimer() → elapsedTime = 0, isRunning = false

## UI Flow Description

### Screen Hierarchy

1. **HomeScreen**: 5 boxes in grid layout (2x3 or similar). Center box labeled "Workout" and functional. Others show "Coming Soon" or are disabled.
2. **WorkoutListScreen**: List of workout sessions. Each session card shows name, date, and summary (e.g., "3 muscle groups, 8 exercises"). FAB at bottom-right for new session.
3. **WorkoutSessionScreen**: 

   - Top section: Timer display with controls
   - Scrollable content: Muscle groups listed vertically
   - Each muscle group expandable/collapsible (optional) or always visible
   - Within each group: exercises listed
   - Within each exercise: sets listed as rows
   - Floating action buttons or inline buttons for adding groups/exercises/sets

### Navigation Flow

- Home → (tap center box) → WorkoutListScreen
- WorkoutListScreen → (tap session) → WorkoutSessionScreen
- WorkoutListScreen → (tap FAB) → Create dialog → WorkoutSessionScreen
- Any screen → (back button) → Previous screen

## Suggested Implementation Order

### Phase 1: Data Models & Basic Structure

1. Create data models (SetEntry, Exercise, MuscleGroup, WorkoutSession)
2. Create MuscleGroupPresets
3. Update MainActivity with basic Compose setup
4. Create AppNavigation with simple state management

## Phase 1: Detailed Implementation Breakdown

### Task 1.1: Create SetEntry Data Model

**File:** `src/main/java/com/journal/ernie/data/SetEntry.kt`

**Steps:**

1. Create package: `package com.journal.ernie.data`
2. Create data class `SetEntry` with:

   - Property `id: String` (use UUID or generate unique ID)
   - Property `reps: Int` (default: 0)
   - Property `weight: Float` (default: 0.0f)
   - Property `comment: String?` (nullable, default: null)

3. Add constructor with default values for all properties
4. Make it a `data class` for automatic equals/hashCode/toString
5. Add comment: `// TODO: Add @Entity annotation when Room is integrated`

**Key Details:**

- Use `java.util.UUID.randomUUID().toString()` for ID generation, or use a counter-based approach
- All properties should be mutable (var) or provide copy() method usage
- Consider adding a companion object with a factory function `createDefault()` that returns a SetEntry with default values

---

### Task 1.2: Create Exercise Data Model

**File:** `src/main/java/com/journal/ernie/data/Exercise.kt`

**Steps:**

1. Create package: `package com.journal.ernie.data`
2. Import `SetEntry` from same package
3. Create data class `Exercise` with:

   - Property `id: String` (unique identifier)
   - Property `name: String` (exercise name, e.g., "Bench Press")
   - Property `sets: MutableList<SetEntry>` (mutable list of sets)

4. Add method `addSet(set: SetEntry)` that adds a set to the list
5. Add method `removeSet(index: Int)` that removes set at index (with bounds checking)
6. Add method `removeSetById(id: String)` that removes set by ID
7. Add comment: `// TODO: Add @Entity annotation when Room is integrated`

**Key Details:**

- Use mutable list to allow in-place modifications
- Methods should handle edge cases (empty list, invalid index)
- Consider adding a method `getSetCount(): Int` for convenience

---

### Task 1.3: Create MuscleGroup Data Model

**File:** `src/main/java/com/journal/ernie/data/MuscleGroup.kt`

**Steps:**

1. Create package: `package com.journal.ernie.data`
2. Import `Exercise` from same package
3. Create data class `MuscleGroup` with:

   - Property `id: String` (unique identifier)
   - Property `name: String` (muscle group name, e.g., "Chest")
   - Property `exercises: MutableList<Exercise>` (mutable list of exercises)

4. Add method `addExercise(exercise: Exercise)` that adds an exercise to the list
5. Add method `removeExercise(id: String)` that removes exercise by ID
6. Add method `findExerciseById(id: String): Exercise?` that returns exercise by ID or null
7. Add comment: `// TODO: Add @Entity annotation when Room is integrated`

**Key Details:**

- Similar structure to Exercise but contains Exercise objects instead of SetEntry
- Methods should handle null cases gracefully
- Consider adding a method `getExerciseCount(): Int` for convenience

---

### Task 1.4: Create WorkoutSession Data Model

**File:** `src/main/java/com/journal/ernie/data/WorkoutSession.kt`

**Steps:**

1. Create package: `package com.journal.ernie.data`
2. Import `MuscleGroup` from same package
3. Create data class `WorkoutSession` with:

   - Property `id: String` (unique identifier)
   - Property `name: String` (session name/title)
   - Property `date: Long` (timestamp in milliseconds since epoch)
   - Property `muscleGroups: MutableList<MuscleGroup>` (mutable list of muscle groups)

4. Add method `addMuscleGroup(group: MuscleGroup)` that adds a muscle group
5. Add method `removeMuscleGroup(id: String)` that removes muscle group by ID
6. Add method `findMuscleGroupById(id: String): MuscleGroup?` that returns group by ID or null
7. Add companion object with factory function `createNew(name: String): WorkoutSession` that:

   - Generates new ID
   - Sets current timestamp using `System.currentTimeMillis()`
   - Initializes empty muscleGroups list

8. Add comment: `// TODO: Add @Entity annotation when Room is integrated`

**Key Details:**

- Use `System.currentTimeMillis()` for timestamp
- Factory function simplifies session creation
- Consider adding a method `getTotalExerciseCount(): Int` that sums exercises across all groups

---

### Task 1.5: Create MuscleGroupPresets

**File:** `src/main/java/com/journal/ernie/data/MuscleGroupPresets.kt`

**Steps:**

1. Create package: `package com.journal.ernie.data`
2. Create `object MuscleGroupPresets` (singleton object)
3. Add private property `PRESET_GROUPS: List<String>` with common muscle groups:

   - "Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Cardio", "Full Body"

4. Add public function `getAllPresets(): List<String>` that returns a copy of PRESET_GROUPS
5. Add public function `isPreset(name: String): Boolean` that checks if name exists in presets (case-insensitive)
6. Add public function `getPresetSuggestions(query: String): List<String>` that:

   - Filters presets that contain query (case-insensitive)
   - Returns filtered list

7. Consider making functions extension functions or keep as regular functions

**Key Details:**

- Use `object` for singleton pattern (no instances needed)
- Case-insensitive matching for better UX
- Suggestions function helps with autocomplete in dialogs

---

### Task 1.6: Update MainActivity with Compose Setup

**File:** `src/main/java/com/journal/ernie/MainActivity.kt`

**Steps:**

1. Change class to extend `ComponentActivity` (from `androidx.activity.ComponentActivity`)
2. Add import: `import androidx.activity.ComponentActivity`
3. Add import: `import androidx.compose.runtime.Composable`
4. Add import: `import androidx.compose.ui.platform.setContent`
5. Add import: `import androidx.compose.material3.MaterialTheme`
6. Add import: `import androidx.compose.material3.Surface`
7. Add import: `import com.journal.ernie.ui.AppNavigation`
8. Override `onCreate(savedInstanceState: Bundle?)`
9. Call `super.onCreate(savedInstanceState)`
10. Call `setContent { }` block
11. Inside setContent:

    - Wrap content in `MaterialTheme { }`
    - Inside MaterialTheme, add `Surface { }`
    - Inside Surface, call `AppNavigation()`

12. Add a sealed class or enum for navigation state (create in same file or separate):

    - Create `sealed class Screen` or `enum class Screen`
    - Values: `Home`, `WorkoutList`, `WorkoutSession`

13. Add state management using `remember` and `mutableStateOf`:

    - `var currentScreen by remember { mutableStateOf(Screen.Home) }`

14. Pass navigation state and setter to AppNavigation

**Key Details:**

- Use Material3 theme for modern look
- Navigation state should be remembered across configuration changes
- Import statements must be correct for Compose and Material3
- Consider using `rememberSaveable` if you want state to persist across process death

---

### Task 1.7: Create AppNavigation Composable

**File:** `src/main/java/com/journal/ernie/ui/AppNavigation.kt`

**Steps:**

1. Create package: `package com.journal.ernie.ui`
2. Create directory structure: `src/main/java/com/journal/ernie/ui/` (if not exists)
3. Add imports:

   - `import androidx.compose.runtime.Composable`
   - `import androidx.compose.runtime.getValue`
   - `import androidx.compose.runtime.setValue`
   - `import androidx.compose.runtime.mutableStateOf`
   - `import androidx.compose.runtime.remember`
   - Import Screen enum/sealed class from MainActivity (or create separate file)

4. Create `@Composable fun AppNavigation()`
5. Inside function:

   - Get navigation state from MainActivity (passed as parameter) or manage locally
   - Use `when` or `if` statement to route based on current screen:
     - `Screen.Home` → Show placeholder text "Home Screen" (HomeScreen will be added in Phase 2)
     - `Screen.WorkoutList` → Show placeholder text "Workout List Screen"
     - `Screen.WorkoutSession` → Show placeholder text "Workout Session Screen"

6. Add navigation callback parameter: `onNavigateTo: (Screen) -> Unit`
7. Pass callback to child screens (when they're created)

**Key Details:**

- For now, use placeholder Text composables for screens not yet implemented
- Navigation callback should update the state in MainActivity
- Consider creating a separate file for Screen sealed class if it gets complex
- Structure should be ready to accept ViewModel parameter in later phases

---

### Task 1.8: Create Package Directories

**Manual Step - Verify Directory Structure:**

Before coding, ensure these directories exist:

- `src/main/java/com/journal/ernie/data/` (for data models)
- `src/main/java/com/journal/ernie/ui/` (for UI composables)
- `src/main/java/com/journal/ernie/viewmodel/` (will be used in Phase 3)

**Steps:**

1. Check if `data` folder exists under `src/main/java/com/journal/ernie/`
2. Check if `ui` folder exists under `src/main/java/com/journal/ernie/`
3. Create folders if they don't exist (this is usually automatic when creating files)

---

## Phase 1 Implementation Order

**Recommended coding sequence:**

1. **First:** Create all data models in bottom-up order (SetEntry → Exercise → MuscleGroup → WorkoutSession)

   - This ensures dependencies are available when needed
   - Test each model independently if possible

2. **Second:** Create MuscleGroupPresets

   - Simple object, no dependencies on other models
   - Can be tested independently

3. **Third:** Update MainActivity

   - Sets up the foundation for the app
   - Establishes navigation state management

4. **Fourth:** Create AppNavigation

   - Depends on MainActivity's Screen enum
   - Provides routing structure

**Why this order:**

- Data models are the foundation - everything else depends on them
- MainActivity is the entry point - must be set up before navigation
- AppNavigation ties everything together - needs both data structure and activity setup

---

## Phase 1 Testing Checklist

After completing Phase 1, verify:

- [ ] All data classes compile without errors
- [ ] SetEntry can be instantiated with default values
- [ ] Exercise can add/remove sets
- [ ] MuscleGroup can add/remove exercises
- [ ] WorkoutSession can add/remove muscle groups
- [ ] MuscleGroupPresets returns correct preset list
- [ ] MainActivity compiles and runs (shows basic UI)
- [ ] AppNavigation displays placeholder text for each screen
- [ ] Navigation state changes when callback is invoked (test with hardcoded button)

---

## Phase 1 Dependencies & Notes

**Required Imports (will need these in Gradle later, but not modifying Gradle now):**

- Jetpack Compose (already assumed to be in project)
- Material3 (already assumed to be in project)
- No Room dependencies needed yet (data models are plain Kotlin classes)

**Important Notes:**

- All data models use mutable lists for now - will be replaced with Room entities later
- IDs are String type - can be changed to Long when Room is added
- No data persistence yet - all data is in-memory
- Navigation is simple state-based - no Navigation Compose library needed
- Placeholder screens will be replaced in later phases

### Phase 2: Home Screen

5. Create HomeScreen with 5 placeholder boxes
6. Wire up center box navigation to Workout section

### Phase 3: ViewModel

7. Create WorkoutViewModel with basic state management
8. Implement session management functions (create, load, select)
9. Implement timer functions

### Phase 4: Workout List Screen

10. Create WorkoutListScreen
11. Wire up FAB to create new sessions
12. Display list of sessions

### Phase 5: Workout Session Screen - Basic

13. Create WorkoutSessionScreen layout
14. Add TimerDisplay component
15. Display muscle groups (static data first)

### Phase 6: Muscle Group Management

16. Create MuscleGroupCard component
17. Create AddMuscleGroupDialog
18. Implement add/remove muscle group in ViewModel
19. Wire up UI

### Phase 7: Exercise Management

20. Create ExerciseCard component
21. Create AddExerciseDialog
22. Implement add/remove exercise in ViewModel
23. Wire up UI

### Phase 8: Set Management

24. Create SetRow component
25. Implement add/remove/update set in ViewModel
26. Wire up UI for set editing

### Phase 9: Polish & Integration

27. Add empty states
28. Add validation (e.g., prevent empty names)
29. Test full workflow
30. Prepare for Room database integration (add TODO comments)

## Package Structure

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

## Implementation Notes

- All data is stored in memory (ViewModel state) for now. Room database integration will be added later.
- Timer uses a simple counter approach with LaunchedEffect. Timer state is UI-level only (not persisted).
- Navigation uses simple state-based routing (enum/sealed class) rather than Navigation Compose library for simplicity.
- Muscle group presets provide common names but users can create custom groups.
- Set entries start with default values (0 reps, 0.0 weight, empty comment) and can be edited inline.
- All CRUD operations update the ViewModel state, which triggers recomposition in Compose.
- Consider using rememberSaveable for dialog state to preserve input on configuration changes.