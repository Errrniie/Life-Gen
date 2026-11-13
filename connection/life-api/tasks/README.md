# Task tracking

Tasks are stored in a dedicated `tasks` table rather than as activities. A task has a title and may include description, category, priority, a calendar `due_date` or offset-aware `due_at`, and an optional `session_id` link. Its status defaults to `pending`; completion records `completed_at` and sets status to `completed`. A revision supports conflict detection, and a unique client request UUID supports safe creation retries.

## Typical flow

- Create with `POST /tasks`; query all pages with `GET /tasks?limit=200&offset=...`, optionally filtering by exact status/category and including soft-delete rows.
- Update task details with `PATCH /tasks/{task_id}` and an `expected_revision`.
- Mark complete with `POST /tasks/{task_id}/complete`.
- Reopen with `POST /tasks/{task_id}/reopen`, which returns it to `pending` and clears `completed_at`.
- Delete and restore with the corresponding task routes. These operations use soft deletion.

A task linked to a session is related by a database foreign key. Session deletion logic described in the workout notes explicitly cascades to activities and records; task behavior on session deletion should be checked in the current route/schema implementation before assuming application-level cascade restoration.

## Source locations

- `routers/tasks.py`: task SQL and lifecycle endpoints.
- `models/task.py`: request and response shapes.
- `db.py`: table, index, and optional session foreign key.
- `API.md`: full endpoint contract.
