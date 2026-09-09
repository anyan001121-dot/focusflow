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
