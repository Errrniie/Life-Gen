# Workout Section — Agent Handoff (Live Edit)

**Date:** June 17, 2026  
**App:** JournalErnie (`/home/LxSparda/Desktop/PhoneJournal/JournalErnie`)  
**Audience:** Another Cursor agent working with **Live Edit** / Apply Changes on a running debug build.

---

## Critical rule for the next agent

**Prefer changes that hot-reload.** The user will turn on live editing and expects to see UI tweaks without a full reinstall.

### Safe for live edit (usually Apply Changes / Live Edit is enough)

- `@Composable` UI: layout, colors, text, padding, `Modifier`, Material3 components
- Compose logic inside existing screens (`WorkoutListScreen`, `WorkoutSessionScreen`, `SetRow`, pickers)
- Tweaking constants (hold delay, swipe threshold, label copy) in Kotlin files that are already loaded
- `ViewModel` logic **if** the app is restarted or the screen is re-entered (state may need navigation away/back)

### Requires a proper rebuild / reinstall (avoid unless user asks)

Do **not** change these casually while the user is live-editing:

| Change type | Why |
|-------------|-----|
| **Room schema** — new/changed `@Entity`, migrations, DAO signatures | KSP regenerates; DB may need clear data |
| **`build.gradle.kts` / new dependencies** | Gradle sync + full build |
| **`AndroidManifest.xml`** — permissions, receivers, services | Full rebuild |
| **New `BroadcastReceiver` / `Application` hooks** | Not hot-swappable |
| **New drawable/mipmap/XML resources** | Often needs rebuild; vector XML sometimes OK |
| **New files that other modules must import before first compile** | First compile always needs build |
| **OSMDroid / `AndroidView` map setup** in `JournalErnieApplication` | Native view + config at app start |
| **Geofence registration** (`GymGeofenceManager`, fused location) | Needs reinstall + permissions on device |

If you must do a rebuild-only change, **tell the user explicitly** before doing it.

**Compile check (when needed):** from `JournalErnie/`:

```bash
./gradlew :app:compileDebugKotlin
```

---

## How navigation works

No Navigation Compose library. Routing is a **sealed class** + `when` in `AppNavigation.kt`.

**Defined in** `MainActivity.kt`:

```
Home → WorkoutList → WorkoutSession
                 → Library
                 → GymLocationsList → GymLocationMap
Home → Settings → GymLocationMap (secondary gym entry)
Home → TestArea → TestWorkoutList → TestWorkoutSession
```

Back handling is in `AppNavigation.kt` `BackHandler`.

**UI background color** used across workout-related screens: `Color(0xFFB0B0B0)` (gray).

---

## Production workout flow (what “Workout” tab is)

### `WorkoutListScreen.kt`

- Lists sessions grouped by **month → week** (`WorkoutWeek.kt` helpers).
- Expandable month/week sections; current month/week auto-expanded.
- **FAB (+)** context menu: Start Workout, Rest Day, Missed Day.
- **Top app bar actions (left to right):** Trash (deleted sessions undo) | **Locations** (`Screen.GymLocationsList`) | Library.
- Session cards: workout / rest / missed types (`SessionType`).
- Create session via `CreateSessionDialog` + tags from `WorkoutViewModel`.

### `WorkoutSessionScreen.kt`

- Active session: timer (`TimerDisplay`), muscle groups, exercises, sets.
- Uses `WorkoutBlockCard`, `MuscleGroupCard`, `SetRow`.
- **Geofence snackbar:** listens for auto-stop when leaving gym (`geofenceStopEvents` from `JournalErnieApplication`).
- Bottom actions: reorder exercises, add muscle group, library link, etc.
- Back syncs session to remote via `workoutViewModel.syncCurrentWorkoutToRemote()`.

### Data layer (production)

- **Room** via `WorkoutDatabase.kt`
- Hierarchy: `WorkoutSession` → `WorkoutBlock` (muscle group) → `Workout` (exercise) → `SetEntry`
- State: `WorkoutViewModel.kt` (large file — session CRUD, timer, tags, library, gym locations, API sync)

---

## Set editing UI (recent work — shared by production + test workout)

**File:** `app/src/main/java/com/journal/ernie/ui/components/SetRow.kt`

### Interaction model

- Tap collapsed set row → expand edit mode.
- **Tap “Set #” / “Dropset” header** → saves (`onUpdate`) and collapses (Finish/Close buttons were removed).
- Trash icon deletes set.
- **Dropset** button (left) + **Comment** toggle (right) on same row.
- Reps and weight are pickers, not text fields.

### `RepsPickerWheel.kt`

- **Horizontal** snap scroll wheel (`LazyRow` + `rememberSnapFlingBehavior`).
- Range **1–20**; anchor values **1, 5, 10, 15, 20** styled slightly bolder.
- Center highlight band; nested scroll blocked so parent list doesn’t steal vertical scroll.
- `resetSession` int bumps scroll position when edit mode opens (avoids jump fights).
- `defaultRepsForPicker(storedReps)` — defaults to 8 if out of range.

### `WeightRingPicker.kt`

Circular grey **outer ring** with tier anchors + white **center disc** showing current weight.

**Weight tiers** (swipe / arrow buttons change tier, not single lb on center):

| Tier | Range (lb) | Ring anchor labels |
|------|------------|-------------------|
| 0 | 1–120 | 20, 40, 60, 80, 100 |
| 1 | 120–219 | 120, 140, 160, 180, 200 |
| 2+ | +100 per tier | anchors offset by +100 per tier up to 1000 lb max |

**Center disc swipe** (tier change — same idea as side arrows):

- **Swipe left** → next tier (higher range), jumps to `tierMinLb(newTier)`
- **Swipe right** → previous tier, weight clamped into that tier’s range
- Threshold: `SWIPE_TIER_THRESHOLD_DP = 20f`
- `weightTier` is updated explicitly on swipe (don’t rely only on `weightLb` at boundary **120**).

**Grey ring hold** (fine pick):

- Hold **200 ms** (`HOLD_THRESHOLD_MS = 200L`) on ring band (not center).
- Opens fullscreen dim overlay + smaller fine ring (`FINE_PICK_RING_SIZE = 88.dp`).
- Drag around fine ring for ±19 lb around tapped anchor; labels every 10 lb.
- Release to confirm.
- Center swipe and ring hold use **separate touch zones** (center = tier swipe, ring = fine pick).

**Side arrow buttons:** lower / raise weight **tier** (same as swipe).

**Touch geometry:** inner no-touch disc radius `TOUCH_INNER_RADIUS = 45.dp`; grey ring aligned to touch band.

**Known quirk:** Weight **120** is the boundary between tier 0 and tier 1. `weightTierFor()` uses `weight < 120` → tier 0, else tier 1+. `LaunchedEffect` only auto-syncs tier when weight falls **outside** current tier min/max.

---

## Gym locations (workout-adjacent)

### Primary entry (Workout tab)

- `WorkoutListScreen` → Locations icon → `GymLocationsListScreen.kt`
- List all saved gyms; edit (map) / delete; **Add gym on map**
- Edit/add uses `GymLocationMapScreen.kt` (OSMDroid `MapView` via `AndroidView`)

### Secondary entry

- `SettingsScreen.kt` still has full gym section (auto-stop toggles, permissions, edit/delete).

### Navigation detail

`Screen.GymLocationMap(locationId, fromSettings)`:

- `locationId = null` → new gym
- `locationId = "<uuid>"` → edit existing
- `fromSettings = false` → back goes to `GymLocationsList`
- `fromSettings = true` → back goes to `Settings`

### Backend

- `GymLocation` entity + `GymLocationDao` in Room
- `GymLocationViewModel` — upsert, delete, `saveGym()`, auto-stop toggle
- Geofences: `GymGeofenceManager`, `GymGeofenceBroadcastReceiver`, `GeofenceWorkoutStopper`
- **Do not change geofence/permission flow** during live UI edits unless user requests it.

---

## Test Area workout (isolated from production DB)

**Purpose:** Try exercise picker + set UI without persisting to production Room.

| File | Role |
|------|------|
| `TestWorkoutFlowViewModel.kt` | In-memory sessions/blocks/sets |
| `TestWorkoutListScreen.kt` | Premade + custom test sessions |
| `TestWorkoutSessionScreen.kt` | Same `WorkoutBlockCard` + `SetRow` as production |
| `EquipmentExerciseWheelOverlay.kt` | 3-layer picker: muscle chips, equipment ring, exercise wheel |
| `SessionMuscleGroupFilterBar.kt` | Muscle filter chips on Add Exercise dialog |

Test workout **reuses** `SetRow`, `RepsPickerWheel`, `WeightRingPicker` — picker changes affect both flows.

---

## Exercise library & catalog

- `ExerciseLibraryScreen.kt` — production library from `WorkoutViewModel.loadLibrary()`
- `MuscleGroupCatalog.kt` — API muscle keys, subgroup expansion, exercise matching
- Equipment icons on wheel: `ic_equipment_*.webp` in `res/drawable/`

---

## Styling conventions

- Gray scaffold background: `Color(0xFFB0B0B0)`
- Material3 (`MaterialTheme.colorScheme`)
- Active weight ring segment: `Color(0xFF5C7A9E)`
- Error/delete accent: `Color(0xFFB85C5C)`
- Rest day tint: `Color(0xFF5A9A7A)`

---

## Key files quick reference

```
MainActivity.kt              — Screen sealed class, ViewModel wiring
ui/AppNavigation.kt          — All routes + BackHandler
ui/WorkoutListScreen.kt      — Session list, FAB, top bar actions
ui/WorkoutSessionScreen.kt   — Live workout + timer + geofence snackbar
ui/components/SetRow.kt      — Set expand/edit, reps + weight pickers
ui/components/RepsPickerWheel.kt
ui/components/WeightRingPicker.kt
ui/GymLocationsListScreen.kt
ui/GymLocationMapScreen.kt
viewmodel/WorkoutViewModel.kt
viewmodel/GymLocationViewModel.kt
viewmodel/TestWorkoutFlowViewModel.kt
data/WorkoutDatabase.kt
data/GymLocation.kt
```

---

## What was done in this chat (workout-focused summary)

1. **Reps picker** — evolved from vertical scroll → horizontal bar attempt → final **horizontal snap wheel** (1–20).
2. **Weight picker** — ring + fine-pick overlay; center **tier swipe** (left = up); hold ring 200 ms for fine menu; tier boundary fix at 120 lb.
3. **SetRow** — tap set header to save/close; dropset + comment row; weight/reps pickers instead of text fields.
4. **Gym locations** — `GymLocationsListScreen`; Locations button on workout list app bar; map screen reused for add/edit with `locationId`.
5. **Test workout** — production set UI wired into test flow; equipment/muscle exercise overlay (separate from production session screen).

---

## Suggested workflow for live-editing agent

1. Read this file + skim the specific component you’re editing.
2. Make **small, composable-only** diffs when possible.
3. If editing pickers, test on **both** production session and **Test Area → Test Workout** (shared components).
4. Avoid Room, Gradle, manifest, new permissions, and map/geofence infrastructure unless the user explicitly wants a full rebuild.
5. Do **not** commit unless the user asks.

---

## Related docs (older / broader context)

- `MD Files/GUI.md` — original UI spec (some details superseded by current implementation)
- `MD Files/Architecture.md` — app architecture
- `MD Files/Features_Journal_And_Geofencing.md` — journal API + geofencing (journal is separate tab)
