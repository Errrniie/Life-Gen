# Life Engine Database Table Explanation

This document explains what each table in the Life Engine PostgreSQL database is responsible for, how the tables relate to each other, and how the FastAPI backend currently uses them.

## Big Picture

The database is built around two main systems:

1. **Tasks** — standalone planned work items.
2. **Sessions / Activities / Records** — structured logged activity data, especially workouts.

The core relationship for logged activity data is:

```text
sessions
  └── activities
        └── records
```

Tasks are separate from workouts and should stay separate.

```text
tasks  ← standalone task system
sessions → activities → records  ← workout/activity logging system
```

---

## 1. `tasks`

### Purpose

The `tasks` table stores standalone tasks, reminders, and planned work. Tasks are not workouts. They are separate user-facing items like homework, errands, app work, chores, or deadlines.

### What belongs here

Examples:

- Finish fluids homework
- Study for dynamics exam
- Call someone
- Work on app backend
- Submit assignment

### What should NOT go here

Workout exercises, sets, reps, or workout session data should not be stored here.

### Important columns

| Column | Purpose |
|---|---|
| `id` | Unique task ID |
| `title` | Main task name |
| `description` | Notes/details for the task |
| `category` | Optional grouping such as school, general, work |
| `status` | Task state, such as pending or completed |
| `priority` | Optional priority value |
| `due_at` | Optional due date/time |
| `completed_at` | Time the task was completed |
| `created_at` | Time the task was created |
| `deleted_at` | Soft-delete timestamp |
| `deleted_reason` | Reason for deletion, usually manual |

### API behavior

The API can:

- Create tasks with `POST /tasks`
- Get tasks with `GET /tasks`
- Complete tasks with `POST /tasks/{task_id}/complete`
- Soft-delete tasks with `DELETE /tasks/{task_id}`
- Restore tasks with `POST /tasks/{task_id}/restore`

### Design rule

Tasks should not be stored inside `activities`. If something is a task, it belongs in `tasks` only.

---

## 2. `sessions`

### Purpose

The `sessions` table stores a full logged session. A session is a broad container for a block of activity.

For workouts, a session represents the whole workout.

### Workout example

```text
Session:
  type = workout
  name = Push Day
```

The session is the workout as a whole. The exercises inside the workout are stored in `activities`.

### What belongs here

Examples:

- Push Day
- Leg Day
- Back Day
- Study session
- Work session
- Cardio session

### Important columns

| Column | Purpose |
|---|---|
| `id` | Unique session ID |
| `type` | Broad category, such as workout, study, work, general |
| `name` | Specific session name, such as Push Day or Leg Day |
| `start_time` | When the session started |
| `end_time` | When the session ended, if used |
| `source` | Optional source of the session data |
| `metadata` | Optional flexible JSON data |
| `notes` | Human-readable notes |
| `deleted_at` | Soft-delete timestamp |
| `deleted_reason` | Reason for deletion, such as manual |

### API behavior

The API can:

- Create sessions with `POST /sessions`
- Get sessions with `GET /sessions`
- Get a single session with `GET /sessions/{session_id}`
- Soft-delete a session with `DELETE /sessions/{session_id}`
- Restore a session with `POST /sessions/{session_id}/restore`
- Get full workouts with `GET /workouts/full`

### Design rule

For workouts:

```text
sessions.type = workout
sessions.name = Leg Day / Push Day / Back Day
```

Do not store `Leg Day` as the `type`. The type should stay broad. The name should be specific.

---

## 3. `activities`

### Purpose

The `activities` table stores the individual activities inside a session.

For workouts, activities are exercises.

### Workout example

```text
Session: Push Day
  Activity: Bench Press
  Activity: Incline Dumbbell Press
  Activity: Triceps Pushdown
```

### What belongs here

Examples:

- Bench Press
- Squat
- Deadlift
- Running
- Cycling
- Reading chapter
- Coding block

### Important columns

| Column | Purpose |
|---|---|
| `id` | Unique activity ID |
| `session_id` | Parent session ID |
| `type` | Activity category, such as strength, cardio, mobility |
| `name` | Specific activity/exercise name |
| `metadata` | Flexible JSON for extra details, such as muscle tags or equipment |
| `created_at` | Time activity was created |
| `deleted_at` | Soft-delete timestamp |
| `deleted_reason` | Reason for deletion, manual or cascade |

### API behavior

The API can:

- Create activities with `POST /activities`
- Get activities for a session with `GET /sessions/{session_id}/activities`
- Soft-delete activities with `DELETE /activities/{activity_id}`

### Design rule

Activities should not be tasks. The API blocks creating activities with `type = task` because tasks belong in the `tasks` table.

### Tags / muscle groups

Workout tags can be stored in `metadata`.

Recommended structure:

```json
{
  "tags": ["chest", "triceps"],
  "equipment": "barbell"
}
```

This allows an exercise to hit multiple muscle groups.

---

## 4. `records`

### Purpose

The `records` table stores the actual measured/logged data for an activity.

For workouts, records are usually sets.

### Workout example

```text
Activity: Bench Press
  Record: set 1, 135 lbs, 10 reps
  Record: set 2, 155 lbs, 8 reps
  Record: set 3, 175 lbs, 5 reps
```

### What belongs here

Examples:

- Set/reps/weight
- Distance/time
- Pain score
- Notes for a set
- Any measurable event tied to an activity

### Important columns

| Column | Purpose |
|---|---|
| `id` | Unique record ID |
| `activity_id` | Parent activity ID |
| `record_time` | Time the record was logged |
| `data` | JSON data for the actual measurement |
| `deleted_at` | Soft-delete timestamp |
| `deleted_reason` | Reason for deletion, manual or cascade |

### API behavior

The API can:

- Create records with `POST /records`
- Get records for an activity with `GET /activities/{activity_id}/records`
- Soft-delete records with `DELETE /records/{record_id}`

### Example `data` JSON

```json
{
  "set": 1,
  "reps": 10,
  "weight": 135,
  "unit": "lbs",
  "notes": "Felt good"
}
```

### Design rule

Records should store the smallest logged unit of data. For workouts, that usually means one set per record.

---

## Workout Data Flow

A complete workout should be structured like this:

```text
sessions
  type = workout
  name = Push Day

activities
  Bench Press
  Incline Press
  Triceps Pushdown

records
  set/reps/weight for each exercise
```

Example nested structure returned by `GET /workouts/full`:

```json
[
  {
    "session_id": "...",
    "type": "workout",
    "name": "Push Day",
    "start_time": "...",
    "notes": "...",
    "activities": [
      {
        "activity_id": "...",
        "type": "strength",
        "name": "Bench Press",
        "metadata": {
          "tags": ["chest", "triceps"]
        },
        "records": [
          {
            "record_id": "...",
            "record_time": "...",
            "data": {
              "set": 1,
              "reps": 10,
              "weight": 135,
              "unit": "lbs"
            }
          }
        ]
      }
    ]
  }
]
```

---

## Soft Delete System

The database uses soft deletes instead of permanently deleting rows.

### Soft delete columns

| Column | Meaning |
|---|---|
| `deleted_at` | If not null, the row is considered deleted |
| `deleted_reason` | Explains why the row was deleted |

### Delete reasons

| Reason | Meaning |
|---|---|
| `manual` | User directly deleted this item |
| `cascade` | Item was deleted because its parent was deleted |

### Why this matters

If a user deletes an entire workout, the session is manually deleted and the child activities/records are cascade deleted.

If the workout is restored, only cascade-deleted child rows should come back. Manually deleted exercises or sets should stay deleted.

---

## Recommended App Behavior

### During an active workout

The app should build the workout locally while the user is still editing it.

Do not send API calls for every small change during the workout.

### When the workout is finished

Send the workout to the API:

```text
POST /sessions
POST /activities
POST /records
```

### When loading saved workouts

Use:

```text
GET /workouts/full
```

This avoids needing the app to call sessions, then activities, then records separately.

---

## Restructuring Checklist

If the database structure changes, update all three layers:

1. PostgreSQL tables
2. FastAPI models, endpoints, and SQL queries in `main.py`
3. Phone and desktop app models/API calls

Do not change one layer without checking the other two.

---

## Current Table Responsibilities Summary

| Table | Responsibility |
|---|---|
| `tasks` | Standalone tasks and planned work |
| `sessions` | Full logged sessions, including complete workouts |
| `activities` | Activities/exercises inside a session |
| `records` | Measured/logged data inside an activity |

