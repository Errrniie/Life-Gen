# Application and data

## Startup and composition

[`Journal/main.py`](../../../Journal/main.py) creates `JSONStorage`, `SettingsStore`, one `APIClient`, feature services, and `MainWindow`. The main window creates Journal, Tasks, Workout, Sleep, and Analytics tabs, coordinates date navigation, and starts background API refreshes for date changes. See [`Journal/GUI/Main_Window.py`](../../../Journal/GUI/Main_Window.py).

## Local persistence and model

[`Journal/Storage/interface.py`](../../../Journal/Storage/interface.py) defines the storage contract. [`Journal/Storage/json_storage.py`](../../../Journal/Storage/json_storage.py) implements it as one JSON object keyed by `YYYY-MM-DD`; writes use a temporary file then replace the target. Entries are represented by [`DailyEntry`](../../../Journal/Models/Daily_Entry.py), which groups journal pages, tasks, sleep hours, workout, and rest/missed-day flags. Nested data types are in `Journal/Models/`.

The primary data file is `Journal/data/lifelog.json`. `JSONStorage` merges records by default, preserving existing non-empty journal pages, tasks, sleep, and workout data when incoming values are empty. It also converts legacy journal text into a `Main` page and tolerates missing fields in older workout/task records. On malformed JSON, its loader prints a warning and returns an empty mapping; callers should be aware that a subsequent save can then write from that empty mapping.

## Settings and templates

[`Journal/config/settings_store.py`](../../../Journal/config/settings_store.py) stores settings in `data/settings.json` by default. These include analytics date range, appearance color, sync preferences, API key, and journal presets. Settings are written via a temporary file. The API key is stored in this JSON settings file.

Workout templates are persisted separately in `data/workout_templates.json` by [`WorkoutTemplateService`](../../../Journal/features/Workout_Template_Service.py). They are local and omit a workout date. Templates are not part of the daily-entry JSON object.

## External service

[`APIClient`](../../../Journal/features/API_Client.py) wraps Requests and targets the configured-in-code Life API base URL. It adds `x-api-key` when an API key is present and exposes task, session/activity, workout, and journal-page operations. Journal, tasks, and workouts use this client in applicable flows; sleep and templates use local files only. See the feature references for details.

## Important paths

- `Journal/main.py` — application construction and entry point.
- `Journal/GUI/Main_Window.py` — tabs, date navigation, background load coordination, menus.
- `Journal/Storage/` — storage interface and JSON implementation.
- `Journal/Models/` — persisted data structures.
- `Journal/config/settings_store.py` — persisted preferences and API key.
- `Journal/data/` — current user data files in this checkout.
