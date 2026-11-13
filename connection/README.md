# Journal ↔ life-api integration

`Journal` is a PyQt6 desktop client with local JSON storage; `life-api` is a separate FastAPI service backed by PostgreSQL. The client constructs one `APIClient` in `Journal/main.py`, using the API key saved in settings. `APIClient` targets the Life API Azure Container Apps URL defined in `Journal/features/API_Client.py` and sends the key as `x-api-key`. The service requires that header on every route except `GET /health`. The client does not read a configurable base URL, so its current target is fixed in source.

## What syncs

| Journal feature | life-api routes used by the client | Behavior |
|---|---|---|
| Journal pages | `GET /journal/page-types`, `GET /journal/by-date/{entry_date}`, `POST /journal/entries`, `POST /journal/pages`, `PATCH /journal/pages/{id}`, `DELETE /journal/pages/{id}`, `POST /journal/pages/{id}/restore` | Local pages are compared and imported before the cache is replaced. Page edits use a revision to detect conflicts. |
| Tasks | `GET /tasks`, `POST /tasks`, `PATCH /tasks/{id}`, `POST /tasks/{id}/complete`, `POST /tasks/{id}/reopen`, `DELETE /tasks/{id}`, `POST /tasks/{id}/restore` | Sync pages through all API tasks, including deletion markers, and files tasks by calendar due date. Local-only tasks from all stored dates are uploaded with retry IDs. |
| Workouts | `GET /workouts/full`, `POST /workouts`, `DELETE /sessions/{id}`, `POST /sessions/{id}/restore` | New workouts are created atomically with a retry ID. API workouts populate the local analytics cache; multiple sessions on one date produce an explicit conflict until Journal supports a list. |
| Sleep and workout templates | None | These remain in local JSON files. |

The JSON store remains important even when the API is enabled: it caches journal and task data and supplies local-only features, including sleep, templates, and analytics. Analytics reads local storage rather than an API analytics route. See [Journal feature notes](Journal/README.md) and [life-api feature notes](life-api/README.md).

## Contract gaps to keep in mind

- The server still uses one shared API key and has no user ownership. A phone client needs revocable device credentials and owner-scoped queries before it can safely access personal data.
- The desktop data model supports one workout per date. Sleep, workout templates, and rest/missed-day status remain local.
- The API accepts optional revision checks for compatibility. Phone clients should send them; requiring them for all clients is part of the rollout plan.
- Journal has API wrappers for creating page types and entries/pages, but the client sync flow creates entries/pages as needed and does not expose all API capabilities (for example, entry update/delete or page-type delete/restore).
- The `GET /exercises` catalog endpoint is documented and available in `life-api`, but Journal's current `APIClient` does not wrap it.

For exact request/response shapes, use [`life-api/API.md`](../life-api/API.md). Client methods and orchestration are in [`Journal/features/API_Client.py`](../Journal/features/API_Client.py), [`Journal/features/Journal_Sync_Service.py`](../Journal/features/Journal_Sync_Service.py), [`Journal/features/Task_Sync_Service.py`](../Journal/features/Task_Sync_Service.py), and [`Journal/features/Workout_Service.py`](../Journal/features/Workout_Service.py).

See [Database integration plan](Database_Integration_Plan.md) for the database rollout and remaining phone decisions.
