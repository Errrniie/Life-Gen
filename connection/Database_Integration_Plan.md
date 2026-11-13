# Journal and life-api database integration

## Changes prepared in this workspace

- Task reads request every API page, use explicit soft-delete rows for removal, and keep unseen local rows. Task creation uses a persisted request UUID so a timeout can be retried without inserting a second task.
- Tasks have a calendar `due_date`, a `revision` for conflicting edits, an update endpoint, and a reopen endpoint. Journal sends date-only deadlines as dates rather than fabricated UTC deadlines.
- Journal pages use a revision for edits. Initial import compares local pages with remote pages and stops on conflicting text before replacing local storage.
- Workout creation is one transaction with a persisted retry UUID. The full workout query retains parents when child rows are soft-deleted and returns exercises and sets in stored order.
- Workout cache refresh rejects malformed rows and multiple sessions on the same local date before writing analytics data. The desktop data model currently stores one workout per date.

These changes are local source changes. The actual PostgreSQL instance has not been inspected or migrated here. `life-api` currently applies additive schema changes through `ensure_schema()` at startup.

## Database rollout

1. Back up PostgreSQL and record the deployed API version. Inspect `information_schema.columns`, `pg_constraint`, and `pg_indexes` for the tables used by Journal. Check whether existing active journal pages duplicate `(journal_entry_id, page_type)` and whether any request UUIDs already exist.
2. Apply the new nullable columns and indexes from `life-api/db.py` before starting the new API. Backfill `tasks.due_date` only where the historical `due_at` truly represented a calendar deadline; a UTC timestamp alone cannot reveal the user's original local date. Existing rows receive `revision = 1` from the default.
3. Deploy the new API before the new desktop application. Verify the new task fields, task PATCH/reopen, journal revisions, and atomic workout endpoint against the deployed instance. Keep a rollback copy of the old API and database backup.
4. Move startup schema mutation into numbered migrations with a migration ledger and one-time deploy command. The migration must reject unexpected older schemas instead of silently creating an incompatible table. Do this before allowing independent desktop and phone release cycles.
5. Add an authenticated phone client through the API. Do not put PostgreSQL credentials or the server-wide `API_KEY` in the phone app. Introduce per-user ownership and revocable device credentials, then scope all reads/writes by owner in SQL. Migrate existing rows to the chosen owner before opening registration to additional users.

## Decisions needed for the phone data model

- **Account scope:** one private account across devices, or separate user accounts. The current schema has no owner ID, so multi-user access cannot safely be enabled as it stands.
- **Workout cardinality:** one workout per calendar day, or multiple. For multiple, change Journal's `DailyEntry.workout` and cache/analytics/UI to a collection. The current importer reports a conflict rather than hiding a session.
- **Shared data:** whether sleep, rest/missed-day status, and workout templates must sync. They currently remain local and therefore will not appear on another device.

## Remaining protocol work

- Add a versioned change feed or snapshot cursor with tombstones before replacing the full-list task and workout reads with bounded pagination. Offset pagination is safe for the current task reconciler because unseen rows are retained, but concurrent inserts/deletes may require a later sync to settle.
- Define an explicit conflict UI for page and task `409` responses. Journal currently preserves local data and reports the error; it does not automatically merge divergent text.
- Require `expected_revision` for all phone task/page edits once all clients send it. The API currently accepts it as optional for compatibility, so a client that omits it can still overwrite a concurrent edit.
- Decide which older workout sessions are legacy partial data and repair them before relying on analytics. The new atomic endpoint only prevents new partial workouts.
