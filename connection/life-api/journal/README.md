# Daily journal

The journal stores one `journal_entries` row per calendar date and allows multiple categorized `journal_pages` under each entry. Day-level mood and JSON metadata live on the entry; pages contain optional title, text content, JSON metadata, and display order. Page categories are database-managed `journal_page_types`.

## Typical flow

1. List active page types with `GET /journal/page-types`.
2. Create a date container with `POST /journal/entries`.
3. Add typed pages with `POST /journal/pages`; page type input is normalized to lowercase with spaces changed to underscores and must refer to an active type.
4. Read entries, a date, or an entry's pages with the journal GET routes. Entry and page updates use PATCH routes.

The schema seeds `main`, `workout`, `school`, `job`, and `goose` page types. An active entry can have at most one active page for a given type; a partial unique index enforces this. A deleted page does not prevent a new active page of that type, while restore can fail if another active page now exists.

## Delete and restore

Deleting an entry soft-deletes it and cascade-soft-deletes its active pages. Restoring the entry restores only pages marked with cascade as the delete reason; pages manually deleted stay deleted. Deleting a page type leaves existing pages unchanged but prevents that type from being used for new pages until restored.

## Source locations

- `routers/journal.py`: page type, entry, and page operations.
- `models/journal.py`: journal request/response models.
- `db.py`: journal schema, seed data, foreign keys, and active-page uniqueness index.
- `API.md`: endpoint-level contract and JSON examples.
- `life_engine_database_table_reference.md`: detailed journal schema and soft-delete semantics.
