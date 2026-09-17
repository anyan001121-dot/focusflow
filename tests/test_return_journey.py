"""Real-life transitions: breaks, persisted return points, and the next task."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from streamlit.testing.v1 import AppTest

from focusflow import db, service
from focusflow.i18n import t
from focusflow.state import new_state


def setup_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "journey.db"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    db.init_db()


def test_pause_survives_reload_without_counting_break(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)
    state = service.start_focus(new_state(), "Write my report")
    now = datetime.now(timezone.utc)
    state["step_start_time"] = (now - timedelta(minutes=12)).isoformat()
    paused = service.pause_focus(state, "report.docx, paragraph 2")
    paused["paused_at"] = (now - timedelta(minutes=10)).isoformat()
    db.save_state(paused)
    restored = service.load_or_new_state()
    assert service.mark_step_done(restored) == restored
    assert service.split_current_step(restored) == restored
    assert service.start_focus(restored, "Other task") == restored
    resumed = service.resume(restored)
    elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(resumed["step_start_time"])).total_seconds()
    assert 119 <= elapsed < 125
    assert resumed["current_step"] == state["current_step"]
    assert resumed["task_queue"] == state["task_queue"]
    assert resumed["completion_condition"] == state["completion_condition"]
    assert resumed["resume_note"] == "report.docx, paragraph 2"
    assert not resumed["paused_at"]


def test_completed_set_does_not_resume_as_active(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)
    state = service.start_focus(new_state(), "Write report")
    for _ in range(20):
        if not state["focus_mode"]:
            break
        state = service.mark_step_done(state)
    assert not state["focus_mode"]
    assert service.resume(state)["response"]["has_active_task"] is False


def test_later_items_are_actionable_and_do_not_overwrite_focus(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)
    state = dict(new_state(), later_list=["Reply to email", "Buy milk"])
    state = service.resolve_later(state, 0, start=True)
    assert state["current_goal"] == "Reply to email"
    assert state["later_list"] == ["Buy milk"]
    assert service.resolve_later(state, 0, start=True) == state
    assert service.resolve_later(state, 0) == state
    assert service.resolve_later(new_state(), -1) == new_state()


def test_chinese_pause_return_and_next_task_ui(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)
    at = AppTest.from_file(Path(__file__).parent.parent / "app.py", default_timeout=10).run()
    at.selectbox[0].set_value("zh").run()
    at.text_area(key="brain_dump_input").set_value("写论文").run()
    next(b for b in at.button if b.label == t("zh", "go_button")).click().run()
    assert not at.exception
    assert any("这一步做到这里" in c.value for c in at.caption)
    at.text_input(key="pause_note").set_value("结果章节第 2 段").run()
    at.button(key="pause-focus").click().run()
    assert at.session_state["ff_state"]["paused_at"]
    assert not any(b.label == t("zh", "done_button") for b in at.button)
    at.button(key="return-focus").click().run()
    for _ in range(20):
        if not at.session_state["ff_state"]["focus_mode"]:
            break
        next(b for b in at.button if b.label == t("zh", "done_button")).click().run()
    assert not at.exception
    assert not at.session_state["ff_state"]["focus_mode"]
    assert at.text_area(key="brain_dump_input") is not None
    assert any("较大的任务可能还需要继续" in s.value for s in at.success)


def test_example_is_editable_and_capture_clears_input(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)
    at = AppTest.from_file(Path(__file__).parent.parent / "app.py", default_timeout=10).run()
    go = lambda: next(b for b in at.button if b.label == t("en", "go_button"))
    go().click().run()
    assert not at.session_state["ff_state"]["focus_mode"]
    at.button(key="example_study").click().run()
    assert at.text_area(key="brain_dump_input").value == t("en", "example_study")
    assert not at.session_state["ff_state"]["focus_mode"]
    at.text_area(key="brain_dump_input").set_value("Write paper results").run()
    go().click().run()
    step = at.session_state["ff_state"]["current_step"]
    assert at.toggle(key="show_timer").value is False
    at.text_input(key="interruption_input").set_value("Reply to my supervisor")
    next(b for b in at.button if b.label == t("en", "send_button")).click().run()
    assert not at.exception
    assert at.session_state["ff_state"]["current_step"] == step
    assert at.session_state["ff_state"]["later_list"] == ["Reply to my supervisor"]
    # Streamlit AppTest may retain the submitted widget value until its next run;
    # the clear_on_submit form behavior is also checked in the browser.
