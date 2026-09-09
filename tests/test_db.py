import os

from focusflow import db


def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / "test.db")
    db.init_db(path)

    assert db.load_state(path) is None

    db.save_state({"current_task": "write tests"}, path)
    loaded = db.load_state(path)
    assert loaded["current_task"] == "write tests"

    db.save_state({"current_task": "updated"}, path)
    assert db.load_state(path)["current_task"] == "updated"


def test_log_event_and_delete_all(tmp_path):
    path = str(tmp_path / "test.db")
    db.init_db(path)

    db.save_state({"current_task": "x"}, path)
    db.log_event("brain_dump", {"user_input": "hello"}, path)

    events = db.get_events(db_path=path)
    assert len(events) == 1
    assert events[0]["event_type"] == "brain_dump"

    db.delete_all(path)
    assert db.load_state(path) is None
    assert db.get_events(db_path=path) == []


def test_preferences_defaults_and_recording(tmp_path):
    path = str(tmp_path / "test.db")
    db.init_db(path)

    prefs = db.load_preferences(path)
    assert prefs["breakdown_total"] == 0
    assert prefs["estimate_ratio_count"] == 0

    db.record_step_duration(actual_minutes=10, estimated_minutes=5, db_path=path)
    prefs = db.load_preferences(path)
    assert prefs["estimate_ratio_count"] == 1
    assert prefs["estimate_ratio_sum"] == 2.0

    db.record_breakdown_outcome(was_split=True, db_path=path)
    db.record_breakdown_outcome(was_split=False, db_path=path)
    prefs = db.load_preferences(path)
    assert prefs["breakdown_total"] == 2
    assert prefs["breakdown_rejections"] == 1

    db.delete_all(path)
    assert db.load_preferences(path)["breakdown_total"] == 0
