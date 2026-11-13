from fastapi import FastAPI, Header, HTTPException, Depends, Query, Response
import os
import psycopg
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime
import logging
import traceback
from typing import List
from psycopg.types.json import Json
from Exercise_Libraray import EXERCISE_LIBRARY, normalize_exercise_name

# API contract: keep API.md in sync when adding/removing/changing endpoints.

# --------------------------------------------------
# Setup
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("life-api")

load_dotenv()
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError("API_KEY environment variable is not set")

app = FastAPI()


@app.on_event("startup")
def ensure_schema():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # UUID generation for primary keys
                cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        type TEXT NOT NULL,
                        name TEXT NULL,
                        start_time TIMESTAMPTZ NOT NULL,
                        end_time TIMESTAMPTZ NULL,
                        source TEXT NULL,
                        metadata JSONB NULL,
                        notes TEXT NULL,
                        created_at TIMESTAMPTZ DEFAULT now(),
                        deleted_at TIMESTAMPTZ NULL,
                        deleted_reason TEXT NULL,
                        CONSTRAINT chk_sessions_time_order
                        CHECK (end_time IS NULL OR end_time >= start_time)
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS activities (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                        type TEXT NOT NULL,
                        name TEXT NULL,
                        metadata JSONB NULL,
                        created_at TIMESTAMPTZ DEFAULT now(),
                        deleted_at TIMESTAMPTZ NULL,
                        deleted_reason TEXT NULL
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS records (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
                        record_time TIMESTAMPTZ NOT NULL DEFAULT now(),
                        data JSONB NOT NULL,
                        deleted_at TIMESTAMPTZ NULL,
                        deleted_reason TEXT NULL
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        title TEXT NOT NULL,
                        description TEXT NULL,
                        category TEXT NULL,
                        session_id UUID NULL REFERENCES sessions(id) ON DELETE CASCADE,
                        status TEXT NOT NULL DEFAULT 'pending',
                        priority INT NULL,
                        due_at TIMESTAMPTZ NULL,
                        completed_at TIMESTAMPTZ NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ DEFAULT now(),
                        deleted_at TIMESTAMPTZ NULL,
                        deleted_reason TEXT NULL
                    );
                    """
                )

                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time DESC);"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_activities_session_id ON activities(session_id);"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_records_activity_id_record_time ON records(activity_id, record_time);"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);"
                )

                # Back-compat for older schemas.
                cur.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS end_time TIMESTAMPTZ;")
                cur.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS source TEXT;")
                cur.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS metadata JSONB;")
                cur.execute(
                    "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();"
                )
                cur.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;")
                cur.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS deleted_reason TEXT;")
                cur.execute(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_constraint
                            WHERE conname = 'chk_sessions_time_order'
                        ) THEN
                            ALTER TABLE sessions
                            ADD CONSTRAINT chk_sessions_time_order
                            CHECK (end_time IS NULL OR end_time >= start_time);
                        END IF;
                    END $$;
                    """
                )
                cur.execute(
                    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();"
                )
                cur.execute("ALTER TABLE activities ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;")
                cur.execute("ALTER TABLE activities ADD COLUMN IF NOT EXISTS deleted_reason TEXT;")
                cur.execute("ALTER TABLE records ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;")
                cur.execute("ALTER TABLE records ADD COLUMN IF NOT EXISTS deleted_reason TEXT;")
                cur.execute(
                    """
                    ALTER TABLE tasks
                    ADD COLUMN IF NOT EXISTS session_id UUID NULL
                    REFERENCES sessions(id) ON DELETE CASCADE;
                    """
                )
                cur.execute(
                    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();"
                )
                cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS deleted_reason TEXT;")
                cur.execute("ALTER TABLE tasks ALTER COLUMN status SET DEFAULT 'pending';")
            conn.commit()
    except Exception:
        logger.error("FAILED TO ENSURE DB SCHEMA")
        logger.error(traceback.format_exc())
        raise

# --------------------------------------------------
# Models
# --------------------------------------------------

class SessionCreate(BaseModel):
    type: str
    name: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    source: str | None = None
    metadata: dict | None = None
    notes: str | None = None


class SessionOut(BaseModel):
    id: str
    type: str
    name: str | None
    start_time: datetime
    end_time: datetime | None = None
    source: str | None = None
    metadata: dict | None = None
    notes: str | None


class ActivityCreate(BaseModel):
    session_id: str
    type: str
    name: str | None = None
    metadata: dict | None = None


class ActivityOut(BaseModel):
    id: str
    session_id: str
    type: str
    name: str | None
    metadata: dict | None


class RecordCreate(BaseModel):
    activity_id: str
    data: dict


class RecordOut(BaseModel):
    id: str
    activity_id: str
    record_time: datetime
    data: dict

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    priority: int | None = None
    due_at: datetime | None = None
    session_id: str | None = None


class TaskOut(BaseModel):
    id: str
    title: str
    description: str | None
    category: str | None
    status: str
    priority: int | None
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    session_id: str | None = None
    updated_at: datetime | None = None

# --------------------------------------------------
# Dependencies
# --------------------------------------------------

def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def get_conn():
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        sslmode=os.environ.get("PGSSLMODE", "require"),
    )

# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}

# --------------------------------------------------
# Exercises
# --------------------------------------------------

@app.get("/exercises", dependencies=[Depends(verify_api_key)])
def get_exercises(
    equipment: str | None = Query(None),
    muscle: str | None = Query(None),
):
    exercises = EXERCISE_LIBRARY

    if equipment:
        equipment_clean = equipment.lower().strip()
        exercises = [e for e in exercises if e.get("equipment") == equipment_clean]

    if muscle:
        muscle_clean = muscle.lower().strip()
        exercises = [
            e
            for e in exercises
            if muscle_clean in e.get("primary_muscles", [])
            or muscle_clean in e.get("secondary_muscles", [])
        ]

    return exercises

# --------------------------------------------------
# Sessions
# --------------------------------------------------

@app.post("/sessions", dependencies=[Depends(verify_api_key)])
def create_session(session: SessionCreate):
    session.type = session.type.lower().strip()
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sessions (
                        type,
                        name,
                        start_time,
                        end_time,
                        source,
                        metadata,
                        notes
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    session.type,
                    session.name,
                    session.start_time,
                    session.end_time,
                    session.source,
                    Json(session.metadata) if session.metadata is not None else None,
                    session.notes,
                ))
                session_id = cur.fetchone()[0]
            conn.commit()

        return {"session_id": session_id}

    except Exception:
        logger.error("FAILED TO CREATE SESSION")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Session creation failed")


@app.get("/sessions", response_model=List[SessionOut], dependencies=[Depends(verify_api_key)])
def get_sessions(
    type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    start: datetime | None = None,
    end: datetime | None = None,
    include_deleted: bool = Query(False),
):
    query = """
        SELECT id, type, name, start_time, end_time, source, metadata, notes
        FROM sessions
    """
    params = []
    conditions = []

    if not include_deleted:
        conditions.append("deleted_at IS NULL")

    if start and end:
        conditions.append("start_time BETWEEN %s AND %s")
        params.extend([start, end])
    elif start:
        conditions.append("start_time >= %s")
        params.append(start)
    elif end:
        conditions.append("start_time <= %s")
        params.append(end)

    if type:
        conditions.append("type = %s")
        params.append(type.lower().strip())

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY start_time DESC LIMIT %s"
    params.append(limit)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return [
        {
            "id": str(r[0]),
            "type": r[1],
            "name": r[2],
            "start_time": r[3],
            "end_time": r[4],
            "source": r[5],
            "metadata": r[6],
            "notes": r[7],
        }
        for r in rows
    ]


@app.get("/workouts/full", dependencies=[Depends(verify_api_key)])
def get_full_workouts():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    s.id,
                    s.type,
                    s.name,
                    s.start_time,
                    s.end_time,
                    s.source,
                    s.metadata,
                    s.notes,
                    a.id,
                    a.type,
                    a.name,
                    a.metadata,
                    r.id,
                    r.record_time,
                    r.data
                FROM sessions s
                LEFT JOIN activities a ON a.session_id = s.id
                LEFT JOIN records r ON r.activity_id = a.id
                WHERE s.type = 'workout'
                  AND s.deleted_at IS NULL
                  AND (a.id IS NULL OR a.deleted_at IS NULL)
                  AND (r.id IS NULL OR r.deleted_at IS NULL)
                ORDER BY s.start_time DESC, a.id, r.record_time
            """)
            rows = cur.fetchall()

    sessions: dict[str, dict] = {}
    session_order: list[str] = []

    for row in rows:
        session_id = str(row[0])
        activity_id = row[8]
        record_id = row[12]

        if session_id not in sessions:
            sessions[session_id] = {
                "session_id": session_id,
                "type": row[1],
                "name": row[2],
                "start_time": row[3],
                "end_time": row[4],
                "source": row[5],
                "metadata": row[6],
                "notes": row[7],
                "activities": [],
                "_activity_map": {},
            }
            session_order.append(session_id)

        session_obj = sessions[session_id]

        if activity_id is not None:
            activity_id_str = str(activity_id)
            if activity_id_str not in session_obj["_activity_map"]:
                activity_obj = {
                    "activity_id": activity_id_str,
                    "type": row[9],
                    "name": row[10],
                    "metadata": row[11],
                    "records": [],
                }
                session_obj["_activity_map"][activity_id_str] = activity_obj
                session_obj["activities"].append(activity_obj)

            if record_id is not None:
                session_obj["_activity_map"][activity_id_str]["records"].append(
                    {
                        "record_id": str(record_id),
                        "record_time": row[13],
                        "data": row[14],
                    }
                )

    result = []
    for session_id in session_order:
        session_obj = sessions[session_id]
        del session_obj["_activity_map"]
        result.append(session_obj)

    return result


@app.get("/sessions/{session_id}", response_model=SessionOut, dependencies=[Depends(verify_api_key)])
def get_session(session_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, type, name, start_time, end_time, source, metadata, notes
                FROM sessions
                WHERE id = %s
                  AND deleted_at IS NULL
            """, (session_id,))
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": str(row[0]),
        "type": row[1],
        "name": row[2],
        "start_time": row[3],
        "end_time": row[4],
        "source": row[5],
        "metadata": row[6],
        "notes": row[7],
    }

# --------------------------------------------------
# Activities
# --------------------------------------------------

@app.post("/activities", dependencies=[Depends(verify_api_key)])
def create_activity(activity: ActivityCreate):
    if activity.type.lower() == "task":
        raise HTTPException(400, "Tasks should not be created as activities")
    activity.type = activity.type.lower().strip()
    activity.name = normalize_exercise_name(activity.name)

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activities (session_id, type, name, metadata)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                """, (
                    activity.session_id,
                    activity.type,
                    activity.name,
                    Json(activity.metadata) if activity.metadata is not None else None,
                ))
                activity_id = cur.fetchone()[0]
            conn.commit()

        return {"activity_id": activity_id}

    except Exception:
        logger.error("FAILED TO CREATE ACTIVITY")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Activity creation failed")


@app.get(
    "/sessions/{session_id}/activities",
    response_model=List[ActivityOut],
    dependencies=[Depends(verify_api_key)],
)
def get_activities_for_session(
    session_id: str,
    include_deleted: bool = Query(False),
):
    query = """
        SELECT id, session_id, type, name, metadata
        FROM activities
        WHERE session_id = %s
    """
    params = [session_id]

    if not include_deleted:
        query += " AND deleted_at IS NULL"

    query += " ORDER BY id"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return [
        {
            "id": str(r[0]),
            "session_id": str(r[1]),
            "type": r[2],
            "name": r[3],
            "metadata": r[4],
        }
        for r in rows
    ]

# --------------------------------------------------
# Records
# --------------------------------------------------

@app.post("/records", dependencies=[Depends(verify_api_key)])
def create_record(record: RecordCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO records (activity_id, data)
                    VALUES (%s, %s)
                    RETURNING id;
                """, (
                    record.activity_id,
                    Json(record.data),
                ))
                record_id = cur.fetchone()[0]
            conn.commit()

        return {"record_id": record_id}

    except Exception:
        logger.error("FAILED TO CREATE RECORD")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Record creation failed")


@app.get(
    "/activities/{activity_id}/records",
    response_model=List[RecordOut],
    dependencies=[Depends(verify_api_key)],
)
def get_records_for_activity(
    activity_id: str,
    include_deleted: bool = Query(False),
):
    query = """
        SELECT id, activity_id, record_time, data
        FROM records
        WHERE activity_id = %s
    """
    params = [activity_id]

    if not include_deleted:
        query += " AND deleted_at IS NULL"

    query += " ORDER BY record_time"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return [
        {
            "id": str(r[0]),
            "activity_id": str(r[1]),
            "record_time": r[2],
            "data": r[3],
        }
        for r in rows
    ]


@app.delete("/activities/{activity_id}", dependencies=[Depends(verify_api_key)])
def delete_activity(activity_id: str):
    try:
        with get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE activities
                        SET
                            deleted_at = now(),
                            deleted_reason = 'manual'
                        WHERE id = %s
                          AND deleted_at IS NULL
                        RETURNING id;
                    """, (activity_id,))
                    row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Activity not found")

        return Response(status_code=204)

    except HTTPException:
        raise
    except Exception:
        logger.error("FAILED TO DELETE ACTIVITY")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Activity deletion failed")


@app.delete("/records/{record_id}", dependencies=[Depends(verify_api_key)])
def delete_record(record_id: str):
    try:
        with get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE records
                        SET
                            deleted_at = now(),
                            deleted_reason = 'manual'
                        WHERE id = %s
                          AND deleted_at IS NULL
                        RETURNING id;
                    """, (record_id,))
                    row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Record not found")

        return Response(status_code=204)

    except HTTPException:
        raise
    except Exception:
        logger.error("FAILED TO DELETE RECORD")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Record deletion failed")

# --------------------------------------------------
# Tasks
# --------------------------------------------------

@app.post("/tasks", dependencies=[Depends(verify_api_key)])
def create_task(task: TaskCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO tasks (
                        title,
                        description,
                        category,
                        priority,
                        due_at,
                        session_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    task.title,
                    task.description,
                    task.category,
                    task.priority,
                    task.due_at,
                    task.session_id,
                ))
                task_id = cur.fetchone()[0]
            conn.commit()

        return {"task_id": task_id}

    except Exception:
        logger.error("FAILED TO CREATE TASK")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Task creation failed")


@app.get("/tasks", response_model=List[TaskOut], dependencies=[Depends(verify_api_key)])
def get_tasks(
    status: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    include_deleted: bool = Query(False),
):
    query = """
        SELECT
            id,
            title,
            description,
            category,
            status,
            priority,
            due_at,
            completed_at,
            created_at,
            session_id,
            updated_at
        FROM tasks
    """
    params = []

    conditions = []

    if not include_deleted:
        conditions.append("deleted_at IS NULL")

    if status:
        conditions.append("status = %s")
        params.append(status)

    if category:
        conditions.append("category = %s")
        params.append(category)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)


    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return [
        {
            "id": str(r[0]),
            "title": r[1],
            "description": r[2],
            "category": r[3],
            "status": r[4],
            "priority": r[5],
            "due_at": r[6],
            "completed_at": r[7],
            "created_at": r[8],
            "session_id": str(r[9]) if r[9] is not None else None,
            "updated_at": r[10],
        }
        for r in rows
    ]

@app.post("/tasks/{task_id}/complete", dependencies=[Depends(verify_api_key)])
def complete_task(task_id: str):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE tasks
                    SET
                        status = 'completed',
                        completed_at = now(),
                        updated_at = now()
                    WHERE id = %s
                      AND deleted_at IS NULL
                    RETURNING id;
                """, (task_id,))
                row = cur.fetchone()
            conn.commit()

        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"task_id": task_id, "status": "completed"}

    except HTTPException:
        raise
    except Exception:
        logger.error("FAILED TO COMPLETE TASK")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Task completion failed")

@app.delete("/tasks/{task_id}", dependencies=[Depends(verify_api_key)])
def delete_task(task_id: str):
    try:
        with get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE tasks
                        SET
                            deleted_at = now(),
                            deleted_reason = 'manual',
                            updated_at = now()
                        WHERE id = %s
                          AND deleted_at IS NULL
                        RETURNING id;
                    """, (task_id,))
                    row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        return Response(status_code=204)

    except HTTPException:
        raise
    except Exception:
        logger.error("FAILED TO DELETE TASK")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Task deletion failed")


@app.post("/tasks/{task_id}/restore", dependencies=[Depends(verify_api_key)])
def restore_task(task_id: str):
    try:
        with get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE tasks
                        SET
                            deleted_at = NULL,
                            deleted_reason = NULL,
                            updated_at = now()
                        WHERE id = %s
                        RETURNING id;
                    """, (task_id,))
                    row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"task_id": task_id, "status": "restored"}

    except HTTPException:
        raise
    except Exception:
        logger.error("FAILED TO RESTORE TASK")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Task restore failed")


@app.delete("/sessions/{session_id}", dependencies=[Depends(verify_api_key)])
def delete_session(session_id: str):
    try:
        with get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE sessions
                        SET
                            deleted_at = now(),
                            deleted_reason = 'manual'
                        WHERE id = %s
                          AND deleted_at IS NULL
                        RETURNING id;
                    """, (session_id,))
                    session_row = cur.fetchone()

                    if session_row:
                        cur.execute("""
                            UPDATE activities
                            SET
                                deleted_at = now(),
                                deleted_reason = 'cascade'
                            WHERE session_id = %s
                              AND deleted_at IS NULL;
                        """, (session_id,))
                        cur.execute("""
                            UPDATE records
                            SET
                                deleted_at = now(),
                                deleted_reason = 'cascade'
                            WHERE activity_id IN (
                                SELECT id
                                FROM activities
                                WHERE session_id = %s
                            )
                              AND deleted_at IS NULL;
                        """, (session_id,))

        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")

        return Response(status_code=204)

    except HTTPException:
        raise
    except Exception:
        logger.error("FAILED TO DELETE SESSION")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Session deletion failed")


@app.post("/sessions/{session_id}/restore", dependencies=[Depends(verify_api_key)])
def restore_session(session_id: str):
    try:
        with get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE sessions
                        SET
                            deleted_at = NULL,
                            deleted_reason = NULL
                        WHERE id = %s
                        RETURNING id;
                    """, (session_id,))
                    session_row = cur.fetchone()

                    if session_row:
                        cur.execute("""
                            UPDATE activities
                            SET
                                deleted_at = NULL,
                                deleted_reason = NULL
                            WHERE session_id = %s
                              AND deleted_reason = 'cascade';
                        """, (session_id,))
                        cur.execute("""
                            UPDATE records
                            SET
                                deleted_at = NULL,
                                deleted_reason = NULL
                            WHERE activity_id IN (
                                SELECT id
                                FROM activities
                                WHERE session_id = %s
                            )
                              AND deleted_reason = 'cascade';
                        """, (session_id,))

        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"session_id": session_id, "status": "restored"}

    except HTTPException:
        raise
    except Exception:
        logger.error("FAILED TO RESTORE SESSION")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Session restore failed")
