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

    go = [b for b in at.get("button") if _label(b) == "Go"][0]
    go.click().run()
    assert not at.exception

    start = [b for b in at.get("button") if _label(b) == "Start"][0]
    start.click().run()
    assert not at.exception
    assert any("split it" in _label(b) for b in at.get("button"))

    split = [b for b in at.get("button") if "split it" in _label(b)][0]
    split.click().run()
    assert not at.exception

    done = [b for b in at.get("button") if "Done with this step" in _label(b)][0]
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
    delete_btn.click().run()
    assert not at.exception
