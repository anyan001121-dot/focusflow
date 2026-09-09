import os

os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("OPENAI_API_KEY", None)

from focusflow import db, service


def test_split_current_step_marks_breakdown_as_split(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db(path)

    state = service.load_or_new_state()
    state = service.start_focus(state, "Prepare for an AI Product Manager interview")
    assert state["breakdown_was_split"] is False

    state = service.split_current_step(state)
    assert state["breakdown_was_split"] is True
    assert state["response"]["type"] == "step_split"


def test_below_min_sample_size_no_personalization_hint(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db(path)

    prefs = db.load_preferences(path)
    assert service._personalization_hint(prefs) == ""
    assert service._estimate_ratio(prefs) is None


def test_high_rejection_rate_triggers_smaller_step_hint(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db(path)

    for _ in range(4):
        db.record_breakdown_outcome(was_split=True, db_path=path)

    prefs = db.load_preferences(path)
    hint = service._personalization_hint(prefs)
    assert "smaller" in hint.lower()


def test_record_cognitive_load_logs_event(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db(path)

    service.record_cognitive_load("easy")
    events = db.get_events(db_path=path)
    assert events[0]["event_type"] == "cognitive_load"
    assert events[0]["payload"]["rating"] == "easy"
