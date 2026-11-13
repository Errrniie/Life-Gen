# Sleep

The Sleep tab records daily sleep hours and displays a trend; it also imports records from Samsung Health CSV. This feature is local and does not use `APIClient`.

[`SleepWidget`](../../../Journal/GUI/components/Sleep_Widget.py) provides the date-specific input, trend display, and CSV import action. [`SleepService`](../../../Journal/features/Sleep_Service.py) validates dates and 0–24 hour values, parses multiple date/duration formats, detects CSV columns, and stores sleep hours in the selected date's `DailyEntry`. The main window also exposes a File menu import action.

## Source map

- `Journal/GUI/components/Sleep_Widget.py` — sleep UI and import feedback.
- `Journal/features/Sleep_Service.py` — parsing, validation, range lookup, CSV import.
- `Journal/Models/Daily_Entry.py` — `sleep_hours` field.
- `Journal/Storage/json_storage.py` — local persistence.
