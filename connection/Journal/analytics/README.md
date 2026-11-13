# Analytics

Analytics presents charts generated from the local storage range. The view receives journal, task, workout, and sleep services, and obtains the shared storage object through the workout service. It does not fetch a separate analytics dataset from the API.

The chart tabs cover workout frequency, workout volume by muscle group, sleep trends, and task completion rate. Workout frequency has day, month, and whole-year views; volume can be inspected in total, weekly, and monthly groupings. A date-range selector scopes chart generation. See [`AnalyticsView`](../../../Journal/GUI/components/Analytics_View.py).

`MainWindow` refreshes charts after feature widgets emit `data_saved`, and when Analytics is selected. Analytics start/end dates are stored by [`SettingsStore`](../../../Journal/config/settings_store.py); the view initializes a default last-30-day range.

## Source map

- `Journal/GUI/components/Analytics_View.py` — chart UI and calculations.
- `Journal/GUI/Main_Window.py` — refresh coordination.
- `Journal/Storage/interface.py` — date range retrieval contract.
- `Journal/config/settings_store.py` — saved analytics date range.
