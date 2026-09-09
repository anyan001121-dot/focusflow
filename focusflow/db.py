"""SQLite persistence for FocusFlow.

Single-user local app: one session row (id=1) holds the current
FocusFlowState as JSON, an append-only events log used for the product
metrics in PRD section 10 (task start rate, time-to-start, etc.), and a
preferences row used for the V0.3 personalization loop (see
focusflow/service.py).

All stored data lives in one local file and can be wiped with
`delete_all()` -- see PRD section 11 (user must be able to delete stored
task information).

Every function takes an optional `db_path` override; when omitted, the
module-level `DB_PATH` is read at *call time* (not baked in as a default
argument), so tests can `monkeypatch.setattr(db, "DB_PATH", ...)` and have
it take effect even for callers (like focusflow/service.py) that never
pass db_path explicitly.
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

CREATE TABLE IF NOT EXISTS preferences (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    data_json TEXT NOT NULL
);
"""

_DEFAULT_PREFERENCES = {
    "breakdown_total": 0,
    "breakdown_rejections": 0,
    "estimate_ratio_sum": 0.0,
    "estimate_ratio_count": 0,
}


def _resolve(db_path: str | None) -> str:
    return db_path if db_path is not None else DB_PATH


@contextmanager
def _connect(db_path: str | None = None):
    conn = sqlite3.connect(_resolve(db_path))
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str | None = None) -> None:
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)


def save_state(state: dict, db_path: str | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO sessions (id, state_json, updated_at)
               VALUES (1, ?, ?)
               ON CONFLICT(id) DO UPDATE SET state_json = excluded.state_json,
                                              updated_at = excluded.updated_at""",
            (json.dumps(state), now),
        )


def load_state(db_path: str | None = None) -> dict | None:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT state_json FROM sessions WHERE id = 1"
        ).fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def log_event(event_type: str, payload: dict | None = None, db_path: str | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO events (ts, event_type, payload) VALUES (?, ?, ?)",
            (now, event_type, json.dumps(payload or {})),
        )


def get_events(limit: int = 200, db_path: str | None = None) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT ts, event_type, payload FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"ts": ts, "event_type": event_type, "payload": json.loads(payload)}
        for ts, event_type, payload in rows
    ]


def load_preferences(db_path: str | None = None) -> dict:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT data_json FROM preferences WHERE id = 1").fetchone()
    if row is None:
        return dict(_DEFAULT_PREFERENCES)
    data = dict(_DEFAULT_PREFERENCES)
    data.update(json.loads(row[0]))
    return data


def save_preferences(data: dict, db_path: str | None = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO preferences (id, data_json) VALUES (1, ?)
               ON CONFLICT(id) DO UPDATE SET data_json = excluded.data_json""",
            (json.dumps(data),),
        )


def record_step_duration(
    actual_minutes: float, estimated_minutes: float, db_path: str | None = None
) -> None:
    """Feed one completed step's actual-vs-estimated ratio into long-term preferences."""
    if not estimated_minutes or estimated_minutes <= 0:
        return
    prefs = load_preferences(db_path)
    prefs["estimate_ratio_sum"] += actual_minutes / estimated_minutes
    prefs["estimate_ratio_count"] += 1
    save_preferences(prefs, db_path)


def record_breakdown_outcome(was_split: bool, db_path: str | None = None) -> None:
    """Feed one completed task's breakdown-acceptance outcome into long-term preferences."""
    prefs = load_preferences(db_path)
    prefs["breakdown_total"] += 1
    if was_split:
        prefs["breakdown_rejections"] += 1
    save_preferences(prefs, db_path)


def delete_all(db_path: str | None = None) -> None:
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM events")
        conn.execute("DELETE FROM preferences")
