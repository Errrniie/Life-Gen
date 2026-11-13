# Tasks

The Tasks tab displays tasks for the selected date and supports creating, editing, completing, deleting, notes, clearing completed items, and manual/automatic sync. UI behavior is in [`TasksWidget`](../../../Journal/GUI/components/Tasks_Widget.py); local task operations are in [`TaskService`](../../../Journal/features/Task_Service.py).

## Local and remote behavior

Tasks are part of each dated `DailyEntry` and are represented by [`Task`](../../../Journal/Models/Task.py), including name, completion state, priority, due date, notes, API ID, revision, and a retry UUID. [`TaskSyncService`](../../../Journal/features/Task_Sync_Service.py) reads every API task page, including soft-delete rows, and reconciles only IDs observed in that response. It pushes local-only tasks from every stored date with stable retry IDs. Remote tasks are grouped by calendar due date, falling back to creation date and then today.

API-backed create, note edit, complete, reopen, and delete operations are followed by a refetch. Revision values detect stale edits. With no configured API key, local-only task operations remain available through `TaskService` and JSON storage; synced tasks require a connection to edit. See the [cross-project integration overview](../../README.md) for the remaining phone design decisions.

## Source map

- `Journal/GUI/components/Tasks_Widget.py` — task list, controls, auto-sync timer.
- `Journal/features/Task_Service.py` — validation and local task CRUD.
- `Journal/features/Task_Sync_Service.py` — API mapping, reconciliation, mutations.
- `Journal/features/API_Client.py` — task endpoint wrappers.
- `Journal/Models/Task.py` and `Journal/Storage/json_storage.py` — task shape and persistence.
