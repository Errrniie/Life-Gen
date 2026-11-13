# PhoneJournal (JournalErnie)

## What this project is

**PhoneJournal** is a native Android app (Kotlin + Jetpack Compose) intended to act as a **personal daily companion**:

- **Workout tracking**: create workout sessions, structure them into blocks (exercises/cardio/warmups), record sets (reps/weight/notes), and track time.
- **Journal**: create day-based pages and write notes/reflections.
- **Tasks**: create and manage tasks (with completion state, priority, optional due date/notes).
- **Exercise library & tagging**: maintain a library of exercises and attach tags/combos to organize sessions/exercises.
- **Settings**: configure app-related settings and integrations (via an API key store + an API client).

The app uses **Jetpack Compose** for UI, **ViewModels** for state/business logic, and **Room** for local persistence.

---

## Tech stack (what an agent needs to know)

- **Platform**: Android (native)
- **Language**: **Kotlin**
- **UI**: **Jetpack Compose** + Material 3
- **State / architecture**:
  - ViewModels for business logic
  - State is exposed via `StateFlow` and/or Compose `State` (`mutableStateOf`) depending on the screen’s needs
- **Persistence**: **Room** (SQLite) with many entities and an active migration history
- **Networking**: OkHttp + JSON parsing via `org.json` (no Retrofit/Moshi/Gson in the current API layer)
- **Coroutines**: used for async work (DB, network, timers)

---

## Workspace structure

At the repository root (`/home/LxSparda/Desktop/PhoneJournal`):

- `JournalErnie/`: the Android project folder (app module, source, etc.)
- `workout_tracking_app_architecture_c2c01193.plan.md`: a planning/architecture document used to build features in phases.
- `JournalErnie/PHASE_*_IMPLEMENTATION_GUIDE.md`: step-by-step implementation guides used during development.

---

## App entry point and navigation

### `MainActivity`
File: `JournalErnie/app/src/main/java/com/journal/ernie/MainActivity.kt`

Responsibilities:

- Defines a sealed `Screen` model (Home, WorkoutList, WorkoutSession, Library, Tasks, Journal, Settings).
- Creates the Room database via `WorkoutDatabase.getDatabase(this)`.
- Constructs ViewModels using `ViewModelProvider` and factory classes.
- Hosts the Compose UI via `setContent { ... }`.
- Owns the **simple in-app navigation state** as `currentScreen` (a `Screen` instance).
- Refreshes data on resume (timer refresh + pulling tasks from server):
  - `workoutViewModel.refreshTimerFromTimestamp()`
  - `tasksViewModel.pullTasksFromServer()`

### `AppNavigation`
File: `JournalErnie/app/src/main/java/com/journal/ernie/ui/AppNavigation.kt`

Responsibilities:

- Routes to the correct screen composable depending on `currentScreen`.
- Implements a **custom back behavior** using `BackHandler` so the app returns to the correct parent screen (e.g., WorkoutSession → WorkoutList → Home).
- Wires screens to their respective ViewModels.

Navigation style:

- This project currently uses **state-driven navigation** (a sealed class + `when`) rather than Jetpack Navigation Compose.
- This keeps dependencies minimal, but means:
  - There is no deep linking yet.
  - Back stack is implemented manually.
  - Screen arguments are handled via shared ViewModel state (e.g., “current session” in `WorkoutViewModel`).

---

## “Single source of truth” patterns

This project largely follows:

- **Room DB as the source of truth** for persisted entities (sessions/tasks/pages/etc.)
- ViewModels maintain **in-memory UI state** derived from DB queries and synchronize with the DB after mutations
- Some flows perform **server snapshot replacement** (tasks) rather than merge

When debugging UI “not updating”, check:

- Whether state is exposed as `StateFlow` vs Compose `State`
- Whether the screen uses `collectAsState()` / observes the right state source

---

## UI layer (Jetpack Compose)

UI is primarily under:

- `JournalErnie/app/src/main/java/com/journal/ernie/ui/`
- `JournalErnie/app/src/main/java/com/journal/ernie/ui/components/`
- `JournalErnie/app/src/main/java/com/journal/ernie/ui/dialogs/`

### Screens (high level)

- **Home**
  - File: `.../ui/HomeScreen.kt`
  - Purpose: “launchpad” to the major features (Journal, Tasks, Workout, Settings).

- **Workout list**
  - File: `.../ui/WorkoutListScreen.kt`
  - Purpose: show existing workout sessions; create/select a session.

- **Workout session**
  - File: `.../ui/WorkoutSessionScreen.kt`
  - Purpose: run/track a workout session:
    - timer controls
    - muscle groups / exercises / sets editing
    - navigation to the exercise library

- **Exercise library**
  - File: `.../ui/ExerciseLibraryScreen.kt`
  - Purpose: browse/search/manage exercises and their tags (library used by workouts).

- **Tasks**
  - File: `.../ui/TasksScreen.kt`
  - Purpose: daily task management UI (create/edit/complete tasks, etc.)

- **Journal**
  - File: `.../ui/JournalScreen.kt`
  - Purpose: create pages and write content for a day.

- **Settings**
  - File: `.../ui/SettingsScreen.kt`
  - Purpose: configure app preferences and external integration settings (API key, etc.)

### Components

Reusable pieces include:

- `TimerDisplay` (`.../ui/components/TimerDisplay.kt`): formats time and exposes Start/Pause/Reset controls.
- `WorkoutSessionCard` (`.../ui/components/WorkoutSessionCard.kt`): list item summarizing a session.
- `MuscleGroupCard`, `ExerciseCard`, `SetRow` (`.../ui/components/...`): nested workout editing UI (group → exercise → sets).
- Journal/task-specific components such as `JournalEditor`, `TaskCard`, `WorkoutBlockCard`, and other expanders/editors.

### Dialogs

Dialogs live under `.../ui/dialogs/` and are used for creation/edit flows (e.g., creating sessions/pages/tasks, picking exercises, editing warmup items, etc.).

---

## State & business logic (ViewModels)

ViewModels are under:

`JournalErnie/app/src/main/java/com/journal/ernie/viewmodel/`

Key ideas:

- **UI observes state** (commonly using `StateFlow` or Compose state collection) and renders accordingly.
- **User actions call ViewModel functions** which update local state and/or persist to Room and/or sync to a server.

Examples:

- `WorkoutViewModel`: central state for sessions, workout blocks/sets, and timer behaviors.
- `TasksViewModel`: handles task CRUD and any remote pull/sync.
- `JournalViewModel`: handles journal pages and content.
- `SettingsViewModel`: handles settings + API-related configuration.

Factories (e.g., `WorkoutViewModelFactory`) exist to provide dependencies like:

- the Room database
- API key storage
- API client(s)

---

## Data layer (Room database)

Database and entities are under:

`JournalErnie/app/src/main/java/com/journal/ernie/data/`

### `WorkoutDatabase`
File: `.../data/WorkoutDatabase.kt`

- Defines the Room database with many entities (sessions, blocks, sets, tasks, journal pages, tags, exercises, cardio, warmups, etc.).
- Includes a long set of migrations (`MIGRATION_1_2` → `MIGRATION_15_16`) indicating iterative schema evolution.
- Exposes DAO entry points:
  - `workoutSessionDao()`
  - `workoutDao()`
  - `setEntryDao()`
  - `taskDao()`
  - `journalPageDao()`
  - `workoutTagDao()`
  - `exerciseLibraryDao()`
  - `cardioDao()`
  - `warmupDao()`

### DAOs
DAOs are under:

`.../data/dao/`

They provide the query surface for each feature area (tasks, sessions, workouts/sets, tags, journal pages, cardio/warmups, exercise library).

### Relations
Room “view” models that join related entities are under:

`.../data/relations/`

Examples include session-with-workouts, workout-with-sets, block-with-warmups/cardio, etc.

### Converters
File: `.../data/Converters.kt`

Used for converting non-primitive types into Room-storable formats via `@TypeConverters`.

---

## Backend API integration (current behavior)

### API key storage

- API key is stored in `ApiKeyStore` using Android DataStore:
  - File: `JournalErnie/app/src/main/java/com/journal/ernie/data/ApiKeyStore.kt`
- The key is injected into ViewModels via factories (see `MainActivity.kt`).

### API client

- File: `JournalErnie/app/src/main/java/com/journal/ernie/data/LifeApiClient.kt`
- Base URL:
  - `https://life-api.bravedesert-0d7c33d5.northcentralus.azurecontainerapps.io`
- Auth:
  - Header `x-api-key: <apiKey>`
- Requests are made with OkHttp. JSON is constructed/parsed via `JSONObject` / `JSONArray`.

### Endpoints used by the app (high level)

Workouts:
- `GET /workouts/full` (pull full nested workouts; used during session load when API key exists)
- `POST /sessions` (create remote workout session)
- `POST /activities` (create remote activity for a workout block)
- `POST /records` (create remote record for a completed set)
- `DELETE /sessions/{session_id}` (delete remote session when deleting locally)
- `POST /sessions/{session_id}/restore` (restore remote session when undoing delete)

Tasks:
- `GET /tasks` (server snapshot pulled on startup/on resume and after mutations)
- `POST /tasks` (create a task)
- `DELETE /tasks/{task_id}` (delete a task)
- (Client supports `POST /tasks/{task_id}/complete` and `POST /tasks/{task_id}/restore`, but ViewModel usage may vary.)

### Remote ID mapping (important)

The local DB stores remote identifiers so local entities can be synced:

- `WorkoutSession.remoteSessionId` ↔ API `session_id`
- `WorkoutBlock.remoteActivityId` ↔ API `activity_id`
- `SetEntry.remoteRecordId` ↔ API `record_id`

If sync “does nothing”, usually one of these is missing/blank.

---

## Workout domain model (conceptual)

The workout feature is structured roughly as:

- **WorkoutSession**: a single session instance for a date/time, includes metadata (type/notes/deleted state depending on schema).
- **WorkoutBlock**: a “block” within a session (e.g., an exercise block, cardio group, warmup group).
- **SetEntry**: a single set record attached to a block (reps/weight/comment/timestamps, etc.).
- **Exercise library**: reusable exercises that blocks can reference.
- **Tags / combos**: organization layer for sessions and exercises.

The UI tends to be nested:

`Session → Muscle Group / Blocks → Exercise → Sets`

Depending on which portion of the app is active, you may see either “muscle-group style” editing or “block-based” editing.

---

## Validation & UX safeguards

The project includes input validation to prevent invalid user data from being saved, such as:

- non-empty names (session/group/exercise)
- maximum name length (commonly 50 chars)
- set value bounds (e.g., reps/weight between 0 and 1000)
- disabled confirmation buttons when invalid
- inline error messages for invalid fields

Validation is implemented both:

- **UI level** (dialogs + input fields)
- **ViewModel level** (defensive validation before applying updates)

---

## External integration (API client + key storage)

Some features pull/sync to an external service:

- `ApiKeyStore` (`.../data/ApiKeyStore.kt`): stores API keys or tokens locally.
- `LifeApiClient` (`.../data/LifeApiClient.kt`): API client used by ViewModels for remote operations.

This allows:

- pulling tasks from a server
- associating sessions/records with remote IDs (seen in schema migrations: `remote_session_id`, `remote_activity_id`, `remote_record_id`)

---

## What’s “done” vs what’s evolving

This codebase has been developed through phase-based guides. As a result:

- Some systems are mature (Room schema + migrations, multi-feature navigation, core screens).
- Some screens/components are still being iterated on (UX polish, consistency, timer behavior, layout centering, etc.).
- Some older patterns may co-exist with newer patterns (e.g., early “in-memory only” approach vs newer Room-backed entities).

---

## How to run (developer workflow)

Typical workflow:

1. Open `JournalErnie/` in Android Studio.
2. Run the `app` configuration on an emulator or device.
3. Use the Home screen to navigate to:
   - Workout
   - Journal
   - Tasks
   - Settings

Notes:

- Data persistence is handled via Room, so most entities should persist across restarts.
- If you change entities/migrations, the schema version and migrations must remain consistent.

---

## Development conventions / gotchas

- **Time values**:
  - Room entities frequently store timestamps as epoch millis.
  - The API frequently expects/returns ISO-8601 timestamps (UTC).
- **Timer**:
  - Timer state is managed in `WorkoutViewModel` and periodically persisted back into the session row.
  - UI timer display is purely presentational; correctness depends on ViewModel state updates.
- **Tasks server sync**:
  - Current approach is “server snapshot wins”:
    - `GET /tasks` replaces the entire local tasks table, rather than merging.
- **Room migrations**:
  - `WorkoutDatabase.kt` includes many migrations and a non-trivial schema. Be careful when adding columns/tables.

---

## Key file map (quick reference)

- **Entry + navigation**
  - `JournalErnie/app/src/main/java/com/journal/ernie/MainActivity.kt`
  - `JournalErnie/app/src/main/java/com/journal/ernie/ui/AppNavigation.kt`

- **Workout**
  - `.../viewmodel/WorkoutViewModel.kt`
  - `.../ui/WorkoutListScreen.kt`
  - `.../ui/WorkoutSessionScreen.kt`
  - `.../ui/components/TimerDisplay.kt`
  - `.../ui/components/SetRow.kt`

- **Tasks**
  - `.../viewmodel/TasksViewModel.kt`
  - `.../ui/TasksScreen.kt`
  - `.../data/dao/TaskDao.kt`

- **Journal**
  - `.../viewmodel/JournalViewModel.kt`
  - `.../ui/JournalScreen.kt`
  - `.../data/JournalPage.kt`
  - `.../data/dao/JournalPageDao.kt`

- **Settings / integration**
  - `.../viewmodel/SettingsViewModel.kt`
  - `.../ui/SettingsScreen.kt`
  - `.../data/ApiKeyStore.kt`
  - `.../data/LifeApiClient.kt`

- **Room**
  - `.../data/WorkoutDatabase.kt`
  - `.../data/Converters.kt`
  - `.../data/dao/*`
  - `.../data/relations/*`

---

## Design goals (guiding principles)

- **Fast logging**: minimal friction to add a set, note, or task.
- **Strong offline story**: Room persistence first; remote sync where helpful.
- **Clear state**: ViewModels own state; UI renders from state and emits user intents back upward.
- **Incremental evolution**: schema and features evolve via migrations + phased implementation guides.

---

## Where to look first (agent onboarding)

If you are new to the project, start here:

1. `JournalErnie/app/src/main/java/com/journal/ernie/MainActivity.kt` (composition root + ViewModel wiring)
2. `JournalErnie/app/src/main/java/com/journal/ernie/ui/AppNavigation.kt` (screen routing + back behavior)
3. `JournalErnie/app/src/main/java/com/journal/ernie/data/WorkoutDatabase.kt` (Room schema + migrations)
4. `JournalErnie/app/src/main/java/com/journal/ernie/data/LifeApiClient.kt` (backend contract + parsing)
5. Feature ViewModels:
   - `.../viewmodel/WorkoutViewModel.kt`
   - `.../viewmodel/TasksViewModel.kt`
   - `.../viewmodel/JournalViewModel.kt`


