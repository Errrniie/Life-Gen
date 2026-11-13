# Exercise catalog

The exercise catalog is bundled in Python source rather than fetched from a separate service or stored in PostgreSQL. `GET /exercises` returns the in-memory combined library and can filter by equipment or primary/secondary muscle.

## Organization and name matching

`Exercise_Libraray/__init__.py` combines lists from `Barbell.py`, `Dumbbell.py`, `Smith_Machine.py`, `Cable.py`, `Machine.py`, `Bodyweight.py`, and `Cardio.py`. It builds an alias map from canonical names and any per-exercise aliases. `normalize_exercise_name()` uses this map for activity creation, and otherwise returns a cleaned title-cased name.

The package directory is spelled `Exercise_Libraray` in source; preserve that spelling in imports and paths. Filtering and exercise object fields are described in `API.md`.
