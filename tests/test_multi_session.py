"""FOCUSFLOW_MULTI_SESSION isolation -- the public-demo safety net.

Local personal use never sets this, so these tests explicitly monkeypatch
db.MULTI_SESSION rather than relying on the environment, and use tmp_path
db files so they can't collide with a developer's real focusflow.db.
"""

from focusflow import db


def test_single_session_mode_ignores_session_id_and_shares_one_row(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "MULTI_SESSION", False)
    db.init_db(path)

    db.save_state({"current_task": "alice's task"}, path, session_id="alice")
    db.save_state({"current_task": "bob's task"}, path, session_id="bob")

    # Both "sessions" land on the same shared row when the flag is off.
    assert db.load_state(path, session_id="alice")["current_task"] == "bob's task"
    assert db.load_state(path, session_id="bob")["current_task"] == "bob's task"


def test_multi_session_mode_isolates_state_between_sessions(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "MULTI_SESSION", True)
    db.init_db(path)

    db.save_state({"current_task": "alice's task"}, path, session_id="alice")
    db.save_state({"current_task": "bob's task"}, path, session_id="bob")

    assert db.load_state(path, session_id="alice")["current_task"] == "alice's task"
    assert db.load_state(path, session_id="bob")["current_task"] == "bob's task"


def test_multi_session_mode_isolates_preferences_and_events(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "MULTI_SESSION", True)
    db.init_db(path)

    db.record_breakdown_outcome(True, path, session_id="alice")
    db.record_breakdown_outcome(False, path, session_id="bob")
    db.log_event("brain_dump", {"x": 1}, path, session_id="alice")

    assert db.load_preferences(path, session_id="alice")["breakdown_rejections"] == 1
    assert db.load_preferences(path, session_id="bob")["breakdown_rejections"] == 0
    assert len(db.get_events(db_path=path, session_id="alice")) == 1
    assert len(db.get_events(db_path=path, session_id="bob")) == 0


def test_multi_session_delete_all_only_wipes_calling_session(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "MULTI_SESSION", True)
    db.init_db(path)

    db.save_state({"current_task": "alice's task"}, path, session_id="alice")
    db.save_state({"current_task": "bob's task"}, path, session_id="bob")

    db.delete_all(path, session_id="alice")

    assert db.load_state(path, session_id="alice") is None
    assert db.load_state(path, session_id="bob")["current_task"] == "bob's task"
