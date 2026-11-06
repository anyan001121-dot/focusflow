"""Headless Streamlit execution checks (via AppTest) -- no browser needed.

These catch wiring bugs pytest's graph/service tests can't: a widget key
typo, a button label that stopped matching, an exception thrown only when
Streamlit actually renders the page.
"""

import os
from pathlib import Path

os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("OPENAI_API_KEY", None)

from streamlit.testing.v1 import AppTest

from focusflow import db
from focusflow.i18n import t

_ROOT = Path(__file__).parent.parent
_APP = str(_ROOT / "app.py")
_SETUP_PAGE = str(_ROOT / "pages" / "0_Setup.py")
_ANALYTICS_PAGE = str(_ROOT / "pages" / "1_Analytics.py")


def _label(btn) -> str:
    return btn.label


def test_app_boots_clean(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "app.db"))
    at = AppTest.from_file(_APP)
    at.run()
    assert not at.exception


def test_analytics_page_boots_clean_with_no_data(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "analytics.db"))
    at = AppTest.from_file(_ANALYTICS_PAGE)
    at.run()
    assert not at.exception


def test_setup_page_checklist_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "setup.db"))
    at = AppTest.from_file(_SETUP_PAGE)
    at.run()
    assert not at.exception

    at.get("checkbox")[0].check().run()
    assert not at.exception

    at2 = AppTest.from_file(_SETUP_PAGE)
    at2.run()
    assert at2.get("checkbox")[0].value is True


def test_full_click_through_brain_dump_to_split_to_done(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "flow.db"))
    at = AppTest.from_file(_APP)
    at.run()

    at.text_area(key="brain_dump_input").set_value(
        "Prepare for an AI Product Manager interview, reply to an email"
    ).run()
    assert not at.exception

    go = [b for b in at.get("button") if _label(b) == t("en", "go_button")][0]
    go.click().run()
    assert not at.exception

    start = [b for b in at.get("button") if _label(b) == t("en", "start_button")][0]
    start.click().run()
    assert not at.exception
    assert any(_label(b) == t("en", "split_button") for b in at.get("button"))

    split = [b for b in at.get("button") if _label(b) == t("en", "split_button")][0]
    split.click().run()
    assert not at.exception

    done = [b for b in at.get("button") if _label(b) == t("en", "done_button")][0]
    done.click().run()
    assert not at.exception


def test_language_switch_and_privacy_reset(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "lang.db"))
    at = AppTest.from_file(_APP)
    at.run()

    lang_select = at.get("selectbox")[0]
    lang_select.set_value("zh").run()
    assert not at.exception
    assert any("继续" in _label(b) for b in at.get("button"))

    delete_btn = [b for b in at.get("button") if "删除" in _label(b)][0]
    assert delete_btn.disabled
    saved_before_confirmation = db.load_state()
    assert saved_before_confirmation is not None
    next(c for c in at.checkbox if c.label == "我确认清空任务、暂存和使用记录").check().run()
    assert db.load_state() == saved_before_confirmation
    delete_btn = next(b for b in at.button if "删除" in b.label)
    assert not delete_btn.disabled
    delete_btn.click().run()
    assert not at.exception
    assert db.load_state() is None
    assert db.get_events() == []
    assert not at.session_state["ff_state"]["focus_mode"]
