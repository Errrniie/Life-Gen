# Journal project reference

Journal is a Python/PyQt6 desktop app for dated journal pages, tasks, workouts, and sleep records, with charts over local history. The app is assembled in [`Journal/main.py`](../../Journal/main.py) and its five primary views in [`Journal/GUI/Main_Window.py`](../../Journal/GUI/Main_Window.py).

## Functional areas

- [Application and data](application-data/README.md): startup, local JSON storage, settings, and data model.
- [Journal pages](journal-pages/README.md): dated page editing and optional Life API synchronization.
- [Tasks](tasks/README.md): task CRUD, local persistence, and optional API synchronization.
- [Workouts](workouts/README.md): workout logging, API sessions, and local templates.
- [Sleep](sleep/README.md): sleep-hour records and Samsung Health CSV import.
- [Analytics](analytics/README.md): date-range charts derived from the local store.

## Setup and run

The declared runtime dependencies are PyQt6, Matplotlib, NumPy, and Requests in [`Journal/requirements.txt`](../../Journal/requirements.txt). From the `Journal` directory, install them with `python -m pip install -r requirements.txt`, then run `python main.py`. The checked-in `run_app.sh` uses an absolute path to a different Journal checkout and should not be treated as a portable launcher.

Data defaults to `Journal/data/lifelog.json`, settings to `Journal/data/settings.json`, and workout templates to `Journal/data/workout_templates.json`. Relative paths are passed from the app entry point; storage paths are not centrally configured.

## Navigation

Use the feature pages for source locations, behavior, and integration notes. Existing project notes include [Windows porting plan](../../Journal/WINDOWS_PORTING.md) and [workout widget color map](../../Journal/WORKOUT_COLORS.md). `Journal/READ.md` is empty.
