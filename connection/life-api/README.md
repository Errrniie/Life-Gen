# life-api

A FastAPI service that stores life-tracking data in PostgreSQL. It exposes authenticated JSON endpoints for workouts, tasks, and a daily journal, plus a server-side exercise catalog. The code is in `life-api/`; these notes summarize the structure and behavior visible in that project.

## Functional areas

- [Service architecture and setup](service/README.md)
- [Workout logging](workouts/README.md)
- [Task tracking](tasks/README.md)
- [Daily journal](journal/README.md)
- [Exercise catalog](exercise-catalog/README.md)

## Existing references

`life-api/API.md` is the endpoint-level API contract. `life-api/life_engine_database_table_reference.md` documents the database tables and their intended data responsibilities. Consult those files for request and response shapes and full column details.
