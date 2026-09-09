"""Glue between the LangGraph pipeline and SQLite persistence.

This is what focusflow/app.py (Streamlit) talks to. Keeping it separate
from graph.py means the graph nodes stay pure and unit-testable without a
database, per PRD section 5 ("controlled workflow, not unnecessary
complexity").
"""

from __future__ import annotations

from . import db
from .graph import build_graph
from .state import FocusFlowState, new_state

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def load_or_new_state() -> FocusFlowState:
    saved = db.load_state()
    if saved is not None:
        return saved
    return new_state()


def _run(state: FocusFlowState, user_input: str, intent: str | None = None) -> FocusFlowState:
    state = dict(state)
    state["user_input"] = user_input
    state["intent"] = intent or ""
    result = _get_graph().invoke(state)
    db.save_state(result)
    db.log_event(
        result.get("intent", ""),
        {"user_input": user_input, "response_type": result.get("response", {}).get("type")},
    )
    return result


def handle_message(state: FocusFlowState, user_input: str) -> FocusFlowState:
    """Free-text turn: router classifies intent from the text and focus_mode."""
    return _run(state, user_input)


def start_focus(state: FocusFlowState, goal: str) -> FocusFlowState:
    """UI shortcut: user picked a goal to start now (e.g. from Brain Dump priorities)."""
    return _run(state, goal, intent="new_task")


def mark_step_done(state: FocusFlowState) -> FocusFlowState:
    return _run(state, "done", intent="continue_focus")


def resume(state: FocusFlowState) -> FocusFlowState:
    return _run(state, "resume", intent="resume")


def reset_all() -> FocusFlowState:
    db.delete_all()
    return new_state()


def set_language(state: FocusFlowState, lang: str) -> FocusFlowState:
    updated = dict(state)
    updated["lang"] = lang
    db.save_state(updated)
    return updated
