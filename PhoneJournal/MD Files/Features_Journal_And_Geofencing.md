# Feature Notes — Journal API & Gym Geofencing

**Date:** June 17, 2026  
**Scope:** Features implemented during this chat (Journal ↔ life-api wiring, multi-gym auto-stop)

---

## 1. Journal ↔ life-api Integration

### Overview
- Journal moved from **local-only Room** to **API-first with local cache**.
- Uses the existing `ApiKeyStore` + `LifeApiClient` pattern from Tasks.
- Still works in **local-only mode** when no API key is configured.

### API Models (`JournalApiModels.kt`)
- `ApiJournalPageType`
  - `type_key: String`
  - `display_name: String`
  - `page_order: Int`
- `ApiJournalPage`
  - `id: String`
  - `journal_entry_id: String`
  - `page_type: String`
  - `title: String?`
  - `content: String`
  - `page_order: Int`
- `ApiJournalEntryWithPages`
  - `id: String`
  - `entry_date: String` (ISO date, e.g. `"2026-06-14"`)
  - `mood: String?`
  - `pages: List<ApiJournalPage>`
- Requests:
  - `CreateJournalEntryRequest(entry_date, mood?)`
  - `CreateJournalPageRequest(journal_entry_id, page_type, title?, content, page_order)`
  - `UpdateJournalPageRequest(title?, content?, page_order?)`
- `JournalApiException(httpCode, message, body?)` with helpers:
  - `HTTP_NOT_FOUND = 404`
  - `HTTP_BAD_REQUEST = 400`
  - `HTTP_CONFLICT = 409`

### `LifeApiClient` Journal Methods
- `getJournalPageTypes(apiKey)`
  - `GET /journal/page-types`
  - Returns `List<ApiJournalPageType>`.
- `getJournalByDate(apiKey, entryDateIso)`
  - `GET /journal/by-date/{entry_date}`
  - Returns `ApiJournalEntryWithPages?` (`null` on 404).
- `createJournalEntry(apiKey, CreateJournalEntryRequest)`
  - `POST /journal/entries`
  - **Response:** `{ "journal_entry_id": "<uuid>" }` only (not a full entry object).
  - Client parses `journal_entry_id` and builds a minimal `ApiJournalEntryWithPages` (`pages` empty).
- `createJournalPage(apiKey, CreateJournalPageRequest)`
  - `POST /journal/pages`
  - **Response:** `{ "journal_page_id": "<uuid>" }` only (not a full page object).
  - Client parses `journal_page_id`; never generates a random UUID for API-created pages.
  - 409 → throws `JournalApiException` with “This page type already exists for today”.
  - 400 → throws `JournalApiException` with “Invalid page type — refresh page types and try again”.
- `updateJournalPage(apiKey, pageId, UpdateJournalPageRequest)`
  - `PATCH /journal/pages/{id}`
  - Returns full `ApiJournalPage` (PATCH response includes page fields).
- `deleteJournalPage(apiKey, pageId)`
  - `DELETE /journal/pages/{id}`

All use the existing `apiRequest()` / `apiRequestWithStatus()` helpers with `x-api-key`.

### Room Schema (Journal)

**Entities:**
- `JournalEntry`
  - `id: String`
  - `entryDate: Long` (start-of-day epoch millis)
  - `remoteEntryId: String?`
  - `mood: String?`
- `JournalPage`
  - `id: String` (UUID by default; remote id when synced)
  - `date: Long` (start-of-day epoch millis)
  - `name: String` (legacy label; de-emphasized)
  - `content: String`
  - `createdAt: Long`
  - `pageType: String?` (`page_type` from API)
  - `title: String?`
  - `remotePageId: String?`
  - `journalEntryId: String?` (remote entry id)
  - `pageOrder: Int`
  - Helper: `tabLabel(typeLookup)` chooses:
    1. Display name from `JournalPageType` for `pageType`
    2. `title`
    3. Capitalized `pageType`
    4. Legacy `name`
- `JournalPageType`
  - `typeKey: String` (PK)
  - `displayName: String`
  - `pageOrder: Int`

**DAOs:**
- `JournalEntryDao`
  - `getEntryByDate(dateStart)`
  - `upsert(entry)`
  - `deleteEntryByDate(dateStart)`
- `JournalPageDao`
  - `getPagesByDate(dateStart)` (ordered by `page_order`, `created_at`)
  - `insertPages(pages)`
  - `insertPage(page)`
  - `getPageById(id)`
  - `updatePage(page)`
  - `deletePage(page)`
  - `deletePagesByDate(dateStart)`
- `JournalPageTypeDao`
  - `getAllTypes()`
  - `upsertAll(types)`
  - `deleteAll()`

**Migration `MIGRATION_17_18`:**
- Adds `journal_entries`, `journal_page_types`.
- Extends `journal_pages` with:
  - `page_type`, `title`, `remote_page_id`, `journal_entry_id`, `page_order`.
- Adds index on `journal_pages(journal_entry_id)`.

### `JournalViewModel` Behavior

**State:**
- `currentDate: StateFlow<Long>` (start-of-day millis).
- `pages: StateFlow<List<JournalPage>>`.
- `pageTypes: StateFlow<List<JournalPageType>>`.
- `currentEntry: StateFlow<JournalEntry?>`.
- `selectedPageId: StateFlow<String?>`.
- `syncError: StateFlow<String?>` (global sync failures).
- `actionError: StateFlow<String?>` (add/delete errors).
- `isLoading: StateFlow<Boolean>`.
- `hasApiKey: StateFlow<Boolean>`.
- `saveState: StateFlow<JournalSaveState>` (`Idle`, `Saving`, `Saved`, `Failed`).

**Page types:**
- `loadPageTypes()`
  - With API key:
    - `getJournalPageTypes(apiKey)` → map to `JournalPageType` → `deleteAll()` + `upsertAll()`.
    - Falls back to local cache on error; 400 populates `syncError`.
  - Without API key:
    - Uses cached `journal_page_types` only.
- `availablePageTypesForDay()`
  - Filters out any `pageType` already used for the current day (case-insensitive).

**Day loading:**
- `loadDay(dateMillis)`
  - Normalizes to start-of-day and updates `currentDate`.
  - API ISO date comes from `isoDateForUiDay()` — same device timezone as the journal header.
  - When API key present:
    - `syncDayFromApi(apiKey, dateStart)`:
      - `GET /journal/by-date/{iso}`.
      - On **404**: keeps local/unsynced pages (does **not** wipe Room).
      - On **200**: `cacheEntryFromApi()` merges server pages **by server UUID**, preserves local-only pages, then `refreshLocalState()`.
  - Without API key:
    - Directly `refreshLocalState(dateStart)`.
  - On any failure: logs, `refreshLocalState`, and shows `"Could not sync journal — showing local data"`.

**Mutations:**
- `addPage(pageTypeKey)`
  - Validates key is non-blank and not already in use for today.
  - With API key:
    - Ensures entry exists:
      - `GET /journal/by-date/{iso}`; if null → `POST /journal/entries` (parses `journal_entry_id`).
    - `POST /journal/pages` (parses `journal_page_id`; no random IDs).
    - Re-syncs day from API; selects the new page by **refreshed server UUID** (`selectPageAfterResync`).
    - On 409: sets `"This page type already exists for today"`.
    - On 400: sets API message and reloads page types.
  - Without API key:
    - `addPageLocalOnly(dateStart, key)` creates a `JournalPage` row and selects it.
- `updatePageContent(pageId, content)`
  - Updates in-memory list immediately.
  - Debounced (≈500ms) `persistPageContent(pageId, content)`:
    - Updates Room.
    - With API key:
      - `PATCH /journal/pages/{remoteId}` with `content`.
      - On success: clears `syncError`, marks `Saved`.
      - On error: sets `"Could not save to server"`, marks `Failed`.
    - Without API key:
      - Marks `Saved` (local-only).
- `applyBoldFormatting` / `applyItalicFormatting`
  - Load from DAO, call `TextFormatter`, then persist via `applyFormattingAndPersist`.
- `deletePage(pageId)`
  - With API key: `DELETE` on server first; on success, delete from Room and re-sync.
  - Without API key: local delete only.
  - Main page delete is blocked in UI and ViewModel.

**Navigation helpers:**
- `navigateToPreviousDay()`, `navigateToNextDay()`, `navigateToToday()` adjust `currentDate` and call `loadDay()`.
- `pullJournalFromServer()` (used in `MainActivity.onResume`) runs `loadPageTypes()` + `loadDay(currentDate)`.

### UI: `JournalScreen`
- Date header with left/right chevrons and “Today” shortcut.
- Tabs:
  - `JournalPageTab` uses `page.tabLabel(typeLookup)` so labels come from page types / titles.
- Editor:
  - `JournalEditor` with bold/italic controls and a debounced save pipeline.
- FAB opens `AddJournalPageTypeDialog`:
  - Shows page types from API (or cache).
  - Hides types already used for that day.
  - Shows hints when:
    - No API key (suggests setting API key).
    - Types failed to load.
    - All types already used.
- Banners:
  - Sync banner for journal-level issues (network / API errors).
  - Action banner for add/delete specific failures (409, 400, etc.).

**Result:** With an API key set, opening Journal loads page types and the current day from life-api. Creating pages, editing content, and deleting pages all go through the API with Room as a local cache. Without an API key, behavior falls back to local-only.

---

## 2. Multi-Gym Geofencing Auto-Stop

### Goals
- Support **multiple gym locations** (e.g., “LA Fitness”, “Home gym”).
- Only auto-stop a workout when:
  1. The user **entered** at least one saved gym during the current session, and
  2. Later **exited** that gym’s geofence.
- Avoid false stops:
  - Starting a workout at home, never near a gym.
  - Resuming the app while outside before ever entering.
- Keep **circular geofences** and reuse one shared `PendingIntent`.

### Room Schema (Gyms & Sessions)

**`GymLocation` (multi-row)**
- `id: String` (UUID PK; legacy `"default"` preserved on migration)
- `name: String?` (e.g., “LA Fitness”, “Home Gym”)
- `latitude: Double`
- `longitude: Double`
- `radiusMeters: Float` (default ~75m)
- `autoStopEnabled: Boolean` (per-location toggle)
- `isEnabled: Boolean` (include in geofence set; default `true`)
- `updatedAt: Long`

**`GymLocationDao`**
- `getAllLocations() : List<GymLocation>`
- `observeAllLocations() : Flow<List<GymLocation>>`
- `getLocationById(id)`
- `getGeofenceEnabledLocations()`:
  - `WHERE is_enabled = 1 AND auto_stop_enabled = 1`
  - Ordered by `updated_at DESC`.
- `upsert(gym)`
- `delete(id)`

**`WorkoutSession` extension**
- Existing:
  - `stoppedByGeofence: Boolean`
  - `geofenceActive: Boolean`
- New:
  - `hasEnteredGymThisSession: Boolean`
    - Set `true` on first **ENTER** event for this session.
    - Cleared on timer reset / new session.

**Migration `MIGRATION_18_19`**
- Adds `is_enabled` to `gym_locations` (default 1).
- Adds `has_entered_gym_this_session` to `workout_sessions` (default 0).

### Geofence Manager (`GymGeofenceManager`)

**Responsibilities:**
- Register one circular geofence per enabled gym location.
- Handle ENTER + EXIT transitions.
- Use a shared `PendingIntent` targeting `GymGeofenceBroadcastReceiver`.

**Key behavior:**
- `registerGymGeofences(locations, sessionId)`
  - Builds `Geofence` objects:
    - `requestId = "gym_{locationId}"`
    - Circular region at `latitude`, `longitude`, radius clamped between `25m` and `5000m`.
    - `transitionTypes = ENTER | EXIT`.
  - Request:
    - `GeofencingRequest.Builder()`
      - `setInitialTrigger(INITIAL_TRIGGER_ENTER)`
      - `addGeofences(geofences)`
  - Removes any existing geofences for that `PendingIntent` before adding.
- `removeGeofences()`
  - Removes all geofences associated with this feature.
  - Legacy `removeGeofence()` kept as a wrapper for call sites.
- Request/response IDs:
  - `requestIdForLocation(locationId)` → `"gym_{locationId}"`.
  - `locationIdFromRequestId(requestId)` strips the prefix if present.

### Broadcast Receiver (`GymGeofenceBroadcastReceiver`)

**Core logic:**
- Parses `GeofencingEvent` from the `Intent`.
- Ignores errors and non-ENTER/EXIT transitions.
- Reads `sessionId` from `EXTRA_SESSION_ID`.
- For each triggering geofence:
  - Derives `locationId` from `requestId`.
  - On **ENTER**:
    - Calls `GeofenceWorkoutStopper.markSessionEnteredGym(sessionId, locationId)`.
  - On **EXIT**:
    - Calls `GeofenceWorkoutStopper.stopWorkoutDueToGeofence(sessionId)`.

Uses a `CoroutineScope` + `goAsync()` for safe async handling.

### Geofence Stopper (`GeofenceWorkoutStopper`)

**Interface:**
- `markSessionEnteredGym(sessionId, locationId): Boolean`
  - Loads session.
  - If timer is running and `hasEnteredGymThisSession == false`, updates:
    - `hasEnteredGymThisSession = true`.
- `stopWorkoutDueToGeofence(sessionId): WorkoutSession?`
  - Loads session; returns `null` if:
    - No session found.
    - Timer not running.
    - `stoppedByGeofence == true`.
    - **`hasEnteredGymThisSession == false` (critical guard).**
  - Computes elapsed seconds (uses `liveElapsedProvider` when available).
  - Updates session:
    - `elapsedTimeSeconds = accumulated`
    - `isTimerRunning = false`
    - `stoppedByGeofence = true`
    - `geofenceActive = false`
  - Persists to DB, removes geofences, posts notification, and notifies `JournalErnieApplication` for UI sync.

### Workout ViewModel Integration (`WorkoutViewModel`)

**Gym APIs (multi-location facing):**
- `allGymLocations: StateFlow<List<GymLocation>>`
  - Backed by `gymLocationDao.observeAllLocations()`.
- `upsertGymLocation(gym: GymLocation)`
  - Writes with updated `updatedAt`.
- `deleteGymLocation(id: String)`
  - Deletes, then `gymGeofenceManager.removeGeofences()`.
- `setLocationAutoStop(id: String, enabled: Boolean)`
  - Loads location, toggles `autoStopEnabled`, persists.

**Timer hooks:**
- `startTimer()`
  - Marks session as running, persists to DB.
  - `maybeRegisterGymGeofence(session)`:
    - `getGeofenceEnabledLocations()`
    - If none or permissions missing → skip.
    - Else `registerGymGeofences(session, locations)` and mark `geofenceActive = true`.
- `pauseTimer()`
  - Stops timer, persists `isTimerRunning = false`.
  - `clearGeofenceForSession(session)`:
    - `removeGeofences()`
    - If `geofenceActive`, sets `geofenceActive = false`.
- `resetTimer()`
  - Sets `elapsedTimeSeconds = 0`, `isTimerRunning = false`, `stoppedByGeofence = false`, `hasEnteredGymThisSession = false`.
  - Clears geofences similarly.

**Resume reconciliation (`reconcileGeofenceOnResume()`)**
- Called from `MainActivity.onResume`.
- Steps:
  1. `refreshTimerFromTimestamp()` for accurate elapsed time.
  2. Choose session:
     - In-memory running session if any.
     - Else current DB running session if any.
  3. If no session → return.
  4. Sync in-memory timer from session row.
  5. If timer not running or `stoppedByGeofence` → `removeGeofences()` and return.
  6. Load enabled, auto-stop locations.
     - If none → return.
     - If location permissions missing → return.
  7. Refresh session from DB (in case of concurrent updates).
  8. If still running and not stopped-by-geofence → re-register geofences and restart timer job.

**Important:** The old behavior (`maybeStopIfOutsideGym`) that stopped the workout based solely on current GPS position on resume has been removed. Auto-stop now depends entirely on ENTER → EXIT sequences reported by the geofence API.

### Gym Location UI

**Settings (`SettingsScreen`)**
- Shows a **“Gym locations”** section:
  - Lists each saved `GymLocation` with:
    - Name (or “Unnamed gym”).
    - Radius.
    - Per-location **auto-stop** switch:
      - Tied to `setLocationAutoStop(id, enabled)`.
  - Shows warnings when:
    - Auto-stop is enabled but location permissions are missing.
    - Notifications are disabled while any auto-stop is enabled.
  - Provides:
    - “Edit on map” for each gym (`onNavigateToGymMap(locationId)`).
    - “Delete” button per gym (with confirmation).
    - “Add gym on map” (navigates with `locationId = null`).

**Gym Map (`GymLocationMapScreen`)**
- `Screen.GymLocationMap(locationId: String?)`:
  - `null` → creating a new location (generates UUID).
  - Non-null → editing existing location.
- Uses OSMDroid map:
  - Tap to place pin and radius circle.
  - Slider for radius (50–150m).
  - Optional gym name.
  - “Use my location” (fused location).
  - Per-location auto-stop switch (“Auto-stop when I leave this gym”).
- `saveGym()` calls `GymLocationViewModel.saveGym(locationId, ...)` to upsert.

### Net Behavior (Acceptance)

- Start workout **at home**, never near any saved gym:
  - Timer runs normally, **no auto-stop**, no “left gym” notification.
- Enter radius of any enabled gym during a running session:
  - `hasEnteredGymThisSession` set to `true` on ENTER.
  - Timer continues to run.
- Leave that gym’s radius:
  - On EXIT, `stopWorkoutDueToGeofence` stops the timer, persists elapsed time, and shows notification.
- Resume app **outside** before ever entering:
  - No auto-stop; only re-registration of geofences for active session.
- Multiple gyms:
  - ENTER of any enabled location arms EXIT logic for that session.
  - EXIT from a gym you never entered in this session is **ignored**.

