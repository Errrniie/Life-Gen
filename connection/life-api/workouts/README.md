# Workout logging

## Data model

A workout is a `sessions` row with `type = workout`. Each activity or exercise belongs to a session, and each logged measurement belongs to an activity:

```text
sessions → activities → records
```

Session fields include start/end times, name, source, notes, and JSON metadata. Activities hold a type, optional name, and metadata. Records hold a database-timestamped `record_time` and JSON `data` for flexible measurements such as sets, reps, or weight. The API also exposes `GET /workouts/full` as a nested export of active workout sessions, activities, and records.

## Typical flow

1. `POST /workouts` creates a session, exercises, and sets in one transaction with a retry UUID.
2. Read via `GET /workouts/full` or the session/activity list routes.

The lower-level `POST /sessions`, `POST /activities`, and `POST /records` routes remain available for other clients. A sequence of those calls is not atomic.

`POST /activities` rejects `type: task`; tasks have their own resource and endpoints. Activity names are normalized against the exercise alias catalog before storage, falling back to title casing when no alias matches.

## Delete and restore

Deleting a session soft-deletes the session and marks active activities and records as cascade-deleted. Restoring the session restores only children whose delete reason is `cascade`; independently manually deleted children remain deleted. Individual activities and records can also be soft-deleted. `include_deleted` query options are available on relevant list routes.

## Source locations

- `routers/sessions.py`: session create/list/get/delete/restore and `/workouts/full`.
- `routers/activities.py`: activity create/list/delete and exercise-name normalization.
- `routers/records.py`: record create/list/delete.
- `models/session.py`, `models/activity.py`, `models/record.py`: API models.
- `db.py`: table definitions and indexes for these resources.
- `API.md`: precise endpoint schemas and query parameters.
