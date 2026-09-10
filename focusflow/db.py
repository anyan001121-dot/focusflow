"""SQLite persistence for FocusFlow.

By default this is a single-user local app: every row is keyed "default",
so the whole file behaves exactly like one shared local profile -- state
survives across `streamlit run app.py` restarts, which is what the Resume
feature is built to demonstrate.

Set `FOCUSFLOW_MULTI_SESSION=true` (e.g. for a public Streamlit Cloud demo
where many strangers hit the same process) to key every row by a caller-
supplied `session_id` instead, so concurrent visitors don't read or
overwrite each other's brain dumps -- see focusflow/service.py and app.py
for where that id comes from. Local personal use never needs to set this;
every function's `session_id` argument is simply ignored (falls back to
"default") when the flag is off, so behavior is unchanged.

`session_id` is always a keyword-only argument (after `db_path`, which
keeps its original position) so old positional call sites -- and the
existing tests -- didn't silently break when it was added.

Every function also takes an optional `db_path` override; when omitted,
the module-level `DB_PATH` (and `MULTI_SESSION`) is read at *call time*
(not baked in as a default argument), so tests can
`monkeypatch.setattr(db, "DB_PATH", ...)` / `monkeypatch.setattr(db,
"MULTI_SESSION", ...)` and have it take effect even for callers (like
focusflow/service.py) that never pass these explicitly.

All stored data lives in one local file and can be wiped with
`delete_all()` -- see PRD section 11 (user must be able to delete stored
task information). In multi-session mode, `delete_all()` only wipes the
calling session's own rows.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.environ.get("FOCUSFLOW_DB_PATH", "focusflow.db")
MULTI_SESSION = os.environ.get("FOCUSFLOW_MULTI_SESSION", "false").lower() == "true"

_DEFAULT_KEY = "default"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    state_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS preferences (
    id TEXT PRIMARY KEY,
    data_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checklist (
    id TEXT PRIMARY KEY,
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


def _key(session_id: str | None) -> str:
    if MULTI_SESSION and session_id:
        return session_id
    return _DEFAULT_KEY


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


def save_state(state: dict, db_path: str | None = None, *, session_id: str | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO sessions (id, state_json, updated_at)
               VALUES (?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET state_json = excluded.state_json,
                                              updated_at = excluded.updated_at""",
            (_key(session_id), json.dumps(state), now),
        )


def load_state(db_path: str | None = None, *, session_id: str | None = None) -> dict | None:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT state_json FROM sessions WHERE id = ?", (_key(session_id),)
        ).fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def log_event(
    event_type: str,
    payload: dict | None = None,
    db_path: str | None = None,
    *,
    session_id: str | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO events (session_id, ts, event_type, payload) VALUES (?, ?, ?, ?)",
            (_key(session_id), now, event_type, json.dumps(payload or {})),
        )


def get_events(
    limit: int = 200, db_path: str | None = None, *, session_id: str | None = None
) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT ts, event_type, payload FROM events WHERE session_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (_key(session_id), limit),
        ).fetchall()
    return [
        {"ts": ts, "event_type": event_type, "payload": json.loads(payload)}
        for ts, event_type, payload in rows
    ]


def load_preferences(db_path: str | None = None, *, session_id: str | None = None) -> dict:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT data_json FROM preferences WHERE id = ?", (_key(session_id),)
        ).fetchone()
    if row is None:
        return dict(_DEFAULT_PREFERENCES)
    data = dict(_DEFAULT_PREFERENCES)
    data.update(json.loads(row[0]))
    return data


def save_preferences(
    data: dict, db_path: str | None = None, *, session_id: str | None = None
) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO preferences (id, data_json) VALUES (?, ?)
               ON CONFLICT(id) DO UPDATE SET data_json = excluded.data_json""",
            (_key(session_id), json.dumps(data)),
        )


def record_step_duration(
    actual_minutes: float,
    estimated_minutes: float,
    db_path: str | None = None,
    *,
    session_id: str | None = None,
) -> None:
    """Feed one completed step's actual-vs-estimated ratio into long-term preferences."""
    if not estimated_minutes or estimated_minutes <= 0:
        return
    prefs = load_preferences(db_path, session_id=session_id)
    prefs["estimate_ratio_sum"] += actual_minutes / estimated_minutes
    prefs["estimate_ratio_count"] += 1
    save_preferences(prefs, db_path, session_id=session_id)


def record_breakdown_outcome(
    was_split: bool, db_path: str | None = None, *, session_id: str | None = None
) -> None:
    """Feed one completed task's breakdown-acceptance outcome into long-term preferences."""
    prefs = load_preferences(db_path, session_id=session_id)
    prefs["breakdown_total"] += 1
    if was_split:
        prefs["breakdown_rejections"] += 1
    save_preferences(prefs, db_path, session_id=session_id)


def load_checklist(db_path: str | None = None, *, session_id: str | None = None) -> dict:
    """Manual "have you done this?" flags for the Setup page. Kept separate
    from `preferences` and untouched by `delete_all()` -- this is one-time
    environment setup progress, not personal task data."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT data_json FROM checklist WHERE id = ?", (_key(session_id),)
        ).fetchone()
    if row is None:
        return {}
    return json.loads(row[0])


def save_checklist(
    data: dict, db_path: str | None = None, *, session_id: str | None = None
) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO checklist (id, data_json) VALUES (?, ?)
               ON CONFLICT(id) DO UPDATE SET data_json = excluded.data_json""",
            (_key(session_id), json.dumps(data)),
        )


def delete_all(db_path: str | None = None, *, session_id: str | None = None) -> None:
    """Wipe stored data for one session (or the single local profile, when
    multi-session mode is off). Never touches other sessions' rows."""
    key = _key(session_id)
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (key,))
        conn.execute("DELETE FROM events WHERE session_id = ?", (key,))
        conn.execute("DELETE FROM preferences WHERE id = ?", (key,))
