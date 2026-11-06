"""Regression coverage for capture, recoverable edits and task switching."""
import pytest
from streamlit.testing.v1 import AppTest
from pathlib import Path
from focusflow import db, service
from focusflow.graph import classify_intent
from focusflow.state import new_state
from focusflow.i18n import t


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "product.db"))
    monkeypatch.setattr(db, "MULTI_SESSION", False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    db.init_db()


@pytest.mark.parametrize("text", ["明天继续写论文", "完成了以后去买菜", "not done", "write my resume"])
def test_capture_never_executes_text(text):
    state = service.start_focus(new_state(), "Write report")
    saved = service.capture_thought(state, text)
    assert saved["current_step"] == state["current_step"]
    assert saved["completed_steps"] == []
    assert saved["later_list"] == [text]
    assert service.undo_edit(saved)["later_list"] == []


def test_resume_word_inside_goal_is_not_command():
    assert classify_intent(dict(new_state(), user_input="继续写论文")) == "new_task"
    assert classify_intent(dict(new_state(), user_input="write my resume")) == "new_task"


def test_switch_and_return_survive_reload():
    first = service.start_focus(new_state(), "Write thesis")
    first = service.mark_step_done(first)
    paused = service.pause_focus(first, "results paragraph 2")
    parked = service.park_focus(paused)
    second = service.start_focus(parked, "Reply email")
    second = service.capture_thought(second, "Buy milk")
    shelf = service.park_focus(service.pause_focus(second))
    restored = service.restore_parked(service.load_or_new_state(), 0)
    assert restored["current_step"] == first["current_step"]
    assert restored["task_queue"] == first["task_queue"]
    assert restored["completed_steps"] == first["completed_steps"]
    assert restored["resume_note"] == "results paragraph 2"
    assert restored["later_list"] == ["Buy milk"]
    assert restored["parked_tasks"][0]["current_goal"] == "Reply email"
    assert service.restore_parked(restored, 0) == restored


def test_undo_completion_restores_progress_and_preferences():
    state = service.start_focus(new_state(), "Write report")
    prefs = db.load_preferences()
    advanced = service.mark_step_done(state)
    restored = service.undo_edit(service.load_or_new_state())
    assert restored["current_step"] == state["current_step"]
    assert restored["task_queue"] == state["task_queue"]
    assert not restored["completed_steps"]
    assert db.load_preferences() == prefs


def test_edit_and_continue_keep_original_goal():
    state = service.start_focus(new_state(), "Write report")
    state = service.edit_step(state, "Write one finding", "One draft sentence")
    assert service.load_or_new_state()["completion_condition"] == "One draft sentence"
    while state["focus_mode"]:
        state = service.mark_step_done(state)
    completed = state["completed_steps"]
    state = service.continue_goal(state, "Add supporting data")
    assert state["completed_steps"] == completed
    assert state["current_goal"] == "Write report"
    assert state["current_step"] == "Add supporting data"


def test_ui_park_restore_and_delete_confirmation():
    at = AppTest.from_file(Path(__file__).parent.parent / "app.py").run()
    assert any(b.disabled for b in at.button if "Delete" in b.label)
    at.text_area(key="brain_dump_input").set_value("Write thesis")
    next(b for b in at.button if b.label == t("en", "go_button")).click().run()
    at.button(key="pause-focus").click().run()
    # Reopen from persisted state, also exercising return across app sessions.
    at = AppTest.from_file(Path(__file__).parent.parent / "app.py").run()
    at.button(key="park-focus").click().run()
    assert at.button(key="restore-0")
    at.button(key="restore-0").click().run()
    assert at.session_state["ff_state"]["focus_mode"]
    assert not at.exception
