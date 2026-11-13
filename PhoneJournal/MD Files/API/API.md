# life-api — API reference

**Source of truth:** [`main.py`](../main.py)

**Maintenance:** Update this file whenever you add, remove, or change an endpoint, request body, query parameter, response shape, or auth behavior in `main.py`.

---

## Overview

| Item | Value |
|------|--------|
| Framework | FastAPI |
| Content-Type | `application/json` (for bodies) |
| Auth | Header `x-api-key` on all endpoints except `GET /health` |
| IDs | UUID strings in paths and JSON |
| Datetimes | ISO 8601 (e.g. `2026-05-27T21:00:00Z`) |

### Authentication

| Header | Required | Description |
|--------|----------|-------------|
| `x-api-key` | Yes (except `/health`) | Must match server env `API_KEY` |

**401 Unauthorized**

```json
{ "detail": "Unauthorized" }
```

### Common error shape

FastAPI returns errors as:

```json
{ "detail": "<message or validation errors>" }
```

---

## Endpoint index

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | No |
| GET | `/exercises` | Yes |
| POST | `/sessions` | Yes |
| GET | `/sessions` | Yes |
| GET | `/sessions/{session_id}` | Yes |
| DELETE | `/sessions/{session_id}` | Yes |
| POST | `/sessions/{session_id}/restore` | Yes |
| GET | `/workouts/full` | Yes |
| POST | `/activities` | Yes |
| GET | `/sessions/{session_id}/activities` | Yes |
| DELETE | `/activities/{activity_id}` | Yes |
| POST | `/records` | Yes |
| GET | `/activities/{activity_id}/records` | Yes |
| DELETE | `/records/{record_id}` | Yes |
| POST | `/tasks` | Yes |
| GET | `/tasks` | Yes |
| POST | `/tasks/{task_id}/complete` | Yes |
| DELETE | `/tasks/{task_id}` | Yes |
| POST | `/tasks/{task_id}/restore` | Yes |

---

## Health

### `GET /health`

No authentication.

**Response `200`**

```json
{ "status": "ok" }
```

---

## Exercises

### `GET /exercises`

List exercises from the server-side exercise library.

**Query parameters**

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `equipment` | string | — | Filters by `equipment` field (case-insensitive input) |
| `muscle` | string | — | Matches membership in `primary_muscles` or `secondary_muscles` (case-insensitive input) |

**Response `200`**

JSON array of exercise objects. Shape depends on the library; fields commonly include:

- `name` (string)
- `equipment` (string)
- `primary_muscles` (string[])
- `secondary_muscles` (string[])
- `aliases` (string[])
- optional `attachments` (string[]) — commonly present on cable movements (e.g. `["rope"]`, `["straight_bar", "rope"]`)

---

## Sessions

### `POST /sessions`

Create a session.

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `type` | string | Yes | Stored lowercased and trimmed |
| `name` | string \| null | No | |
| `start_time` | datetime | Yes | |
| `end_time` | datetime \| null | No | Optional session end time |
| `source` | string \| null | No | Optional source such as phone, desktop, manual |
| `metadata` | object \| null | No | Optional session-level JSON |
| `notes` | string \| null | No | |

**Example request**

```json
{
  "type": "workout",
  "name": "Morning lift",
  "start_time": "2026-05-27T14:30:00Z",
  "end_time": "2026-05-27T15:30:00Z",
  "source": "phone",
  "metadata": {
    "location": "gym"
  },
  "notes": "Felt strong"
}
```

**Response `200`**

```json
{ "session_id": "550e8400-e29b-41d4-a716-446655440000" }
```

**Errors**

| Status | `detail` |
|--------|----------|
| 401 | Unauthorized |
| 500 | Session creation failed |

---

### `GET /sessions`

List sessions (newest `start_time` first).

**Query parameters**

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `type` | string | — | Filter; matched lowercased and trimmed |
| `limit` | int | 20 | Min 1, max 100 |
| `start` | datetime | — | `start_time >= start` (unless both `start` and `end` set) |
| `end` | datetime | — | `start_time <= end` (or `BETWEEN` when both set) |
| `include_deleted` | bool | false | Include soft-deleted rows |

**Response `200`** — array of:

| Field | Type |
|-------|------|
| `id` | string |
| `type` | string |
| `name` | string \| null |
| `start_time` | datetime |
| `end_time` | datetime \| null |
| `source` | string \| null |
| `metadata` | object \| null |
| `notes` | string \| null |

**Example response**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "workout",
    "name": "Morning lift",
    "start_time": "2026-05-27T14:30:00Z",
    "end_time": "2026-05-27T15:30:00Z",
    "source": "phone",
    "metadata": {
      "location": "gym"
    },
    "notes": null
  }
]
```

---

### `GET /sessions/{session_id}`

Get one non-deleted session.

**Path parameters**

| Param | Type |
|-------|------|
| `session_id` | string (UUID) |

**Response `200`**

Same object shape as one item in `GET /sessions`.

**Errors**

| Status | `detail` |
|--------|----------|
| 404 | Session not found |

---

### `DELETE /sessions/{session_id}`

Soft-delete a session. Cascades: marks related activities and records deleted with `deleted_reason = 'cascade'`.

**Response `204`** — empty body

**Errors**

| Status | `detail` |
|--------|----------|
| 404 | Session not found |
| 500 | Session deletion failed |

---

### `POST /sessions/{session_id}/restore`

Restore a session and cascade-restored children (only rows with `deleted_reason = 'cascade'`).

**Response `200`**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "restored"
}
```

**Errors**

| Status | `detail` |
|--------|----------|
| 404 | Session not found |
| 500 | Session restore failed |

---

### `GET /workouts/full`

Nested export of all non-deleted workout sessions with activities and records.

**Response `200`** — array of:

```json
[
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "workout",
    "name": "Morning lift",
    "start_time": "2026-05-27T14:30:00Z",
    "end_time": "2026-05-27T15:30:00Z",
    "source": "phone",
    "metadata": {
      "location": "gym"
    },
    "notes": null,
    "activities": [
      {
        "activity_id": "660e8400-e29b-41d4-a716-446655440001",
        "type": "exercise",
        "name": "Bench press",
        "metadata": { "equipment": "barbell" },
        "records": [
          {
            "record_id": "770e8400-e29b-41d4-a716-446655440002",
            "record_time": "2026-05-27T14:45:00Z",
            "data": { "sets": 3, "reps": 8, "weight_kg": 80 }
          }
        ]
      }
    ]
  }
]
```

Only sessions where `type = 'workout'`. Ordered by `start_time` DESC.

---

## Activities

### `POST /activities`

Create an activity under a session.

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `session_id` | string | Yes | UUID |
| `type` | string | Yes | Lowercased and trimmed; **`task` is rejected** |
| `name` | string \| null | No | |
| `metadata` | object \| null | No | Arbitrary JSON object |

**Example request**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "exercise",
  "name": "Squat",
  "metadata": { "variant": "back" }
}
```

**Response `200`**

```json
{ "activity_id": "660e8400-e29b-41d4-a716-446655440001" }
```

**Errors**

| Status | `detail` |
|--------|----------|
| 400 | Tasks should not be created as activities |
| 500 | Activity creation failed |

---

### `GET /sessions/{session_id}/activities`

List activities for a session (ordered by `id`).

**Path parameters**

| Param | Type |
|-------|------|
| `session_id` | string (UUID) |

**Query parameters**

| Param | Type | Default |
|-------|------|---------|
| `include_deleted` | bool | false |

**Response `200`** — array of:

| Field | Type |
|-------|------|
| `id` | string |
| `session_id` | string |
| `type` | string |
| `name` | string \| null |
| `metadata` | object \| null |

**Example response**

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "exercise",
    "name": "Squat",
    "metadata": { "variant": "back" }
  }
]
```

---

### `DELETE /activities/{activity_id}`

Soft-delete one activity (`deleted_reason = 'manual'`).

**Response `204`** — empty body

**Errors**

| Status | `detail` |
|--------|----------|
| 404 | Activity not found |
| 500 | Activity deletion failed |

---

## Records

### `POST /records`

Create a record for an activity. `record_time` is set by the database (not sent in the request).

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `activity_id` | string | Yes |
| `data` | object | Yes |

**Example request**

```json
{
  "activity_id": "660e8400-e29b-41d4-a716-446655440001",
  "data": { "sets": 3, "reps": 10, "weight_kg": 100 }
}
```

**Response `200`**

```json
{ "record_id": "770e8400-e29b-41d4-a716-446655440002" }
```

**Errors**

| Status | `detail` |
|--------|----------|
| 500 | Record creation failed |

---

### `GET /activities/{activity_id}/records`

List records for an activity (ordered by `record_time`).

**Path parameters**

| Param | Type |
|-------|------|
| `activity_id` | string (UUID) |

**Query parameters**

| Param | Type | Default |
|-------|------|---------|
| `include_deleted` | bool | false |

**Response `200`** — array of:

| Field | Type |
|-------|------|
| `id` | string |
| `activity_id` | string |
| `record_time` | datetime |
| `data` | object |

**Example response**

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "activity_id": "660e8400-e29b-41d4-a716-446655440001",
    "record_time": "2026-05-27T14:45:00Z",
    "data": { "sets": 3, "reps": 10, "weight_kg": 100 }
  }
]
```

---

### `DELETE /records/{record_id}`

Soft-delete one record (`deleted_reason = 'manual'`).

**Response `204`** — empty body

**Errors**

| Status | `detail` |
|--------|----------|
| 404 | Record not found |
| 500 | Record deletion failed |

---

## Tasks

Tasks use a separate `tasks` table. Do not create tasks via `POST /activities` with `type: "task"`.

### `POST /tasks`

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | Yes | |
| `description` | string \| null | No | |
| `category` | string \| null | No | |
| `priority` | int \| null | No | |
| `due_at` | datetime \| null | No | |
| `session_id` | string \| null | No | Optional parent session |

**Example request**

```json
{
  "title": "Buy groceries",
  "description": "Milk and eggs",
  "category": "errands",
  "priority": 2,
  "due_at": "2026-05-28T18:00:00Z",
  "session_id": null
}
```

**Response `200`**

```json
{ "task_id": "880e8400-e29b-41d4-a716-446655440003" }
```

**Errors**

| Status | `detail` |
|--------|----------|
| 500 | Task creation failed |

---

### `GET /tasks`

List tasks (newest `created_at` first).

**Query parameters**

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `status` | string | — | Exact match |
| `category` | string | — | Exact match |
| `limit` | int | 50 | Min 1, max 200 |
| `include_deleted` | bool | false | |

**Response `200`** — array of:

| Field | Type |
|-------|------|
| `id` | string |
| `title` | string |
| `description` | string \| null |
| `category` | string \| null |
| `status` | string |
| `priority` | int \| null |
| `due_at` | datetime \| null |
| `completed_at` | datetime \| null |
| `created_at` | datetime |
| `session_id` | string \| null |
| `updated_at` | datetime \| null |

---

### `POST /tasks/{task_id}/complete`

Mark a non-deleted task completed (`status = 'completed'`, `completed_at = now()`, `updated_at = now()`). Deleted tasks return 404.

**Response `200`**

```json
{
  "task_id": "880e8400-e29b-41d4-a716-446655440003",
  "status": "completed"
}
```

**Errors**

| Status | `detail` |
|--------|----------|
| 404 | Task not found |
| 500 | Task completion failed |

---

### `DELETE /tasks/{task_id}`

Soft-delete a task by setting `deleted_at`, `deleted_reason = 'manual'`, and `updated_at`.

**Response `204`** — empty body

**Errors**

| Status | `detail` |
|--------|----------|
| 404 | Task not found |
| 500 | Task deletion failed |

---

### `POST /tasks/{task_id}/restore`

Restore a task by clearing `deleted_at` and `deleted_reason`, and updating `updated_at`.

**Response `200`**

```json
{
  "task_id": "880e8400-e29b-41d4-a716-446655440003",
  "status": "restored"
}
```

**Errors**

| Status | `detail` |
|--------|----------|
| 404 | Task not found |
| 500 | Task restore failed |

---

## Data model (app ↔ database)

```
Session (sessions)
  └── Activity (activities) — session_id
        └── Record (records) — activity_id

Task (tasks) — primarily standalone, but may optionally link to a session through session_id
```

**Soft delete**

| Table | Columns | List filter |
|-------|---------|-------------|
| `sessions`, `activities`, `records` | `deleted_at`, `deleted_reason` | `include_deleted=false` (default) |
| `tasks` | `deleted_at`, `deleted_reason` | `include_deleted=false` (default) |

**Session delete/restore cascade**

- Delete session → related activities/records get `deleted_reason = 'cascade'`
- Restore session → only restores children where `deleted_reason = 'cascade'`

---

## Environment (server)

| Variable | Purpose |
|----------|---------|
| `API_KEY` | Expected `x-api-key` value |
| `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` | Postgres connection |
| `PGSSLMODE` | Default `require` |

Interactive OpenAPI docs (when the server is running): `/docs`, `/redoc`.
