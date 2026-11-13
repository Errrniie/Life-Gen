# Workouts

The Workout tab opens as a searchable history and review view. Each saved workout shows its date, time, title, exercises, sets, notes, source, and available metadata. Editing and creation open a separate form for muscle groups, exercises, per-set reps/weight/comments and units, duration, time, and notes. UI and form components live in [`Workout_Widget.py`](../../../Journal/GUI/components/Workout_Widget.py); validation, volume, local CRUD, and API operations are in [`WorkoutService`](../../../Journal/features/Workout_Service.py).

## Persistence and API

Workouts are nested in a dated `DailyEntry`; the model types `Workout`, `Exercise`, and `Set` are defined in [`Journal/Models/Workout.py`](../../../Journal/Models/Workout.py). With an API key, the service loads every workout session for the history list, including multiple sessions on one date. It creates a complete workout through one atomic API call with a persisted retry UUID and edits a workout through revision-checked `PATCH /workouts/{session_id}`. An edit preserves extra exercise and set fields, rejecting stale changes from another client. Without a key, local storage supports one workout per date. `MainWindow` invokes workout API loading during background date loads when a key exists. The dated local analytics cache still holds one workout per date; the history list is the complete API view.

Server workout editing becomes available after the matching Life-Api changes are deployed. Until then, the review screen remains available and disables the server edit action when no revision is returned.

## Templates

The widget can save and load reusable workout templates. [`WorkoutTemplateService`](../../../Journal/features/Workout_Template_Service.py) stores them in a separate JSON file, `data/workout_templates.json`; template data omits the date. Related dialog: [`Load_Template_Dialog.py`](../../../Journal/GUI/components/Load_Template_Dialog.py). The existing [color map](../../../Journal/WORKOUT_COLORS.md) describes current widget styling.

## Source map

- `Journal/GUI/components/Workout_Widget.py` — workout editor and template actions.
- `Journal/features/Workout_Service.py` — domain logic and API-backed session operations.
- `Journal/features/Workout_Template_Service.py` — local template CRUD.
- `Journal/Models/Workout.py` — workout, exercise, and set data classes.
- `Journal/features/API_Client.py` — workout/session endpoint wrappers.
