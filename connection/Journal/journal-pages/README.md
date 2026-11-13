# Journal pages

The Journal tab edits rich-text pages for the selected date. It supports adding pages from available page types, renaming/deleting pages, formatting text, and legacy preset-tag page creation. The widget is [`JournalWidget`](../../../Journal/GUI/components/Journal_Widget.py); its service API and backward-compatible single-journal methods are in [`JournalService`](../../../Journal/features/Journal_Service.py).

## Local model and API flow

Each dated [`DailyEntry`](../../../Journal/Models/Daily_Entry.py) contains `journal_pages`; each [`JournalPage`](../../../Journal/Models/Journal_Page.py) can hold a name, HTML content, creation time, legacy tag, and API identifiers/type. JSON storage migrates old `journal` text to a page named `Main` when reading old records.

When an API client is supplied, `JournalService` creates a [`JournalSyncService`](../../../Journal/features/Journal_Sync_Service.py). The sync service compares and imports local pages before replacing the cache with API data. It stops on conflicting text, and content updates send the last seen page revision to detect changes from another device. `MainWindow` requests a date sync during its background load before it populates the journal widget. Local storage remains the cache used by the UI and analytics.

API endpoint wrappers are in [`API_Client.py`](../../../Journal/features/API_Client.py), methods named `get_journal_*`, `create_journal_*`, `update_journal_page`, `delete_journal_page`, and `restore_journal_page`.

## Source map

- `Journal/GUI/components/Journal_Widget.py` — editor, page list, page controls, save/load.
- `Journal/features/Journal_Service.py` — validation, local operations, API service delegation.
- `Journal/features/Journal_Sync_Service.py` — API/local page reconciliation and remote mutations.
- `Journal/Models/Journal_Page.py` — page fields and remote identifiers.
- `Journal/Storage/json_storage.py` — legacy journal migration and persistence.
