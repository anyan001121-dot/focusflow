"""SQLite persistence for FocusFlow.

Single-user local app: one session row (id=1) holds the current
FocusFlowState as JSON, plus an append-only events log used for the
product metrics in PRD section 10 (task start rate, time-to-start, etc.).

All stored data lives in one local file and can be wiped with
`delete_all()` -- see PRD section 11 (user must be able to delete stored
task information).
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.environ.get("FOCUSFLOW_DB_PATH", "focusflow.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    state_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL
);
"""


@contextmanager
def _connect(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)


def save_state(state: dict, db_path: str = DB_PATH) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO sessions (id, state_json, updated_at)
               VALUES (1, ?, ?)
               ON CONFLICT(id) DO UPDATE SET state_json = excluded.state_json,
                                              updated_at = excluded.updated_at""",
            (json.dumps(state), now),
        )


def load_state(db_path: str = DB_PATH) -> dict | None:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT state_json FROM sessions WHERE id = 1"
        ).fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def log_event(event_type: str, payload: dict | None = None, db_path: str = DB_PATH) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO events (ts, event_type, payload) VALUES (?, ?, ?)",
            (now, event_type, json.dumps(payload or {})),
        )


def get_events(limit: int = 200, db_path: str = DB_PATH) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT ts, event_type, payload FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"ts": ts, "event_type": event_type, "payload": json.loads(payload)}
        for ts, event_type, payload in rows
    ]


def delete_all(db_path: str = DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM events")
