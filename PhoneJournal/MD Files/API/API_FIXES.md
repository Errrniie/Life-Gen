# API Fixes — PhoneJournal App

Changes made to align the Android app with `MD Files/API.md` and `MD Files/life_engine_table_explanation.md` after an API compliance audit.

**Date:** June 3, 2026

---

## Summary

| Area | Status |
|------|--------|
| Workout sync | Fixed — batch upload on leave; remote deletes; import parsing |
| Tasks | Fixed — complete endpoint, query param, ID handling |
| Journal | No changes — correctly local-only (no API) |

---

## Workout (`LifeApiClient.kt`, `WorkoutViewModel.kt`, `AppNavigation.kt`)

### Deferred sync until workout ends

**Problem:** The app called `POST /sessions`, `POST /activities`, and `POST /records` while the user was still editing (on session create, add block, and finish set). The life-engine doc recommends building locally during the workout and syncing when finished.

**Fix:**
- Removed immediate `ensureRemoteSession` from `createNewSession`.
- Removed immediate `ensureRemoteActivity` from `addBlock`.
- Removed per-set `syncRemoteRecord` from `finishSet`.
- Added `syncCurrentWorkoutToRemote()` / `syncWorkoutStateToRemote()` to batch-create session, activities, and completed sets.
- Called when navigating back from `WorkoutSessionScreen` and from `clearCurrentSession()`.

### Session restore response

**Problem:** `restoreWorkout()` parsed the restore body as `/workouts/full` JSON. The API returns `{ "session_id", "status": "restored" }`.

**Fix:** Call restore, then reload the session from `GET /workouts/full` by `session_id`.

### Record import (`GET /workouts/full`)

**Problem:** Parser only read `weight`, not `weight_kg` (used in API examples).

**Fix:** Added `parseRecordData()` to accept `weight` or `weight_kg`, and `set` or `sets`.

### Remote soft-delete for activities and records

**Problem:** Local removal of exercises/sets did not call `DELETE /activities/{id}` or `DELETE /records/{id}`, leaving orphan rows on the server.

**Fix:**
- Added `deleteActivity()` and `deleteRecord()` to `LifeApiClient`.
- `removeWorkout` / `removeSet` / `removeSetById` call these when `remoteActivityId` / `remoteRecordId` are set (skips placeholder `"sent"`).

### Session `source` and activity metadata

**Problem:** `POST /sessions` did not send `source`. Activity `metadata` was always empty despite session tags in Room.

**Fix:**
- `createSession` sends `source: "phone"`.
- `buildActivityMetadata()` sends `{ "tags": ["chest", ...] }` from session tag IDs when creating activities.

---

## Tasks (`LifeApiClient.kt`, `TasksViewModel.kt`)

### Toggle complete reverted after sync

**Problem:** `toggleTaskCompletion` updated Room locally, then `pullTasksFromServer()` replaced the list with server data that still had `pending` status — because `POST /tasks/{id}/complete` was never called.

**Fix:** When marking complete and API key is set, call `completeTask()` then `pullTasksFromServer()`. Uncompleting remains local-only (no uncomplete endpoint in the API).

### Task updates overwritten by pull

**Problem:** `updateTask` pulled from the server after local edits. There is no PATCH/update endpoint, so edits were lost.

**Fix:** `updateTask` only updates Room and refreshes UI — no pull after edit.

### Wrong query parameter for deleted tasks

**Problem:** Client sent `includeDeleted`; API expects `include_deleted`.

**Fix:** Query string uses `include_deleted`.

### Create/delete ID race

**Problem:** New tasks used a local UUID until pull; quick delete could `DELETE` the wrong id.

**Fix:** After `POST /tasks`, replace the local row with the server `task_id` before refresh.

### Action response parsing (`complete` / `restore`)

**Problem:** `parseTaskFromJson` expected full task objects; complete/restore return `{ task_id, status }`.

**Fix:** `parseTaskFromJson` accepts `task_id`, merges with optional `existing` task, and maps `status` correctly (`completed`, `restored`, etc.).

---

## Journal

### Add Page availability after delete

**Problem:** After a page was deleted, page-type availability could become inconsistent (and the app could reuse old IDs indirectly via cached state).

**Fix:** Page-type availability is computed from the day’s current active pages (synced from the API). After a successful delete + resync, the deleted page type becomes available again and adding it creates a brand-new page with the new server ID.

### Safer deletion order (API first)

**Problem:** The app deleted the page from Room first and then attempted the API delete, which could leave the phone and server inconsistent if the API call failed.

**Fix:** With an API key set, deletion now follows:

1. `DELETE /journal/pages/{id}`  
2. If successful, delete from Room  
3. Re-sync the day

If the API delete fails, the local page remains and an error is shown.

### Do not revive deleted pages after refresh

After delete + resync, Room is rebuilt from the API response (active pages only). The deleted page’s old ID is not retained for that type, and a replacement page uses the new server ID returned by `POST /journal/pages`.

### Protect unsaved text from refresh overwrites

**Problem:** A full refresh could overwrite local edits while a PATCH was pending or had failed.

**Fix:** The phone tracks:

- pending save page IDs
- failed save page IDs
- pending deletion page IDs

Refreshing a day preserves the local content for pending/failed-save pages instead of overwriting with server text.

### Main page deletion

The phone now disables/hides delete for the `main` page type and returns a user-facing error if deletion is attempted programmatically.

### Create response parsing (ID-only)

**Problem:** `POST /journal/entries` and `POST /journal/pages` return ID-only JSON (`journal_entry_id`, `journal_page_id`), but the client parsed them like full GET objects. Page create could assign a **random UUID**, breaking selection and sync.

**Fix:**
- `parseJournalEntryCreateResponse()` reads `journal_entry_id`.
- `parseJournalPageCreateResponse()` reads `journal_page_id`.
- Full GET/PATCH parsers require a real `id` (no random fallback).
- After create + resync, `selectPageAfterResync()` selects by refreshed server UUID.

### 404 must not wipe local journal data

**Problem:** `GET /journal/by-date` returning 404 deleted all local pages for that day (including offline-only pages).

**Fix:** On 404, refresh local state only; do not delete Room rows.

### Merge sync by server UUID

**Problem:** Sync wiped the day and re-inserted pages, losing local-only rows and matching only loosely by type.

**Fix:** `cacheEntryFromApi()` merges server pages by **server UUID**, keeps local-only pages (`remotePageId == null`), and preserves dirty pending/failed-save content.

### ISO date matches UI day

**Fix:** `isoDateForUiDay()` derives the API `entry_date` from the same start-of-day anchor as `currentDate` (device timezone).

---

## Known limitations (not fixed — API gaps)

1. **Task uncomplete** — No server endpoint; toggling back to incomplete is local-only and will not sync to other clients.
2. **Task field updates** — No PATCH; title/priority/due edits stay on-device until the API adds an update route.
3. **Task recreate on edit** — Not implemented; would require delete + create to force server parity.

---

## Files modified

- `JournalErnie/app/src/main/java/com/journal/ernie/data/LifeApiClient.kt`
- `JournalErnie/app/src/main/java/com/journal/ernie/viewmodel/WorkoutViewModel.kt`
- `JournalErnie/app/src/main/java/com/journal/ernie/viewmodel/TasksViewModel.kt`
- `JournalErnie/app/src/main/java/com/journal/ernie/ui/AppNavigation.kt`
