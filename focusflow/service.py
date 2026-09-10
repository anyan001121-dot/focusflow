"""Glue between the LangGraph pipeline and SQLite persistence.

This is what focusflow/app.py (Streamlit) talks to. Keeping it separate
from graph.py means the graph nodes stay pure and unit-testable without a
database, per PRD section 5 ("controlled workflow, not unnecessary
complexity"). Long-term preference learning also lives here: nodes report
raw signals (actual vs. estimated minutes, whether a breakdown got split),
and this layer is what turns those into the aggregate stats in
focusflow/db.py's preferences table and feeds them back in as the next
breakdown's personalization hint.

Every function takes an optional `session_id`. It's ignored unless
`FOCUSFLOW_MULTI_SESSION=true` (see focusflow/db.py) -- local personal use
never needs to pass it.
"""

from __future__ import annotations

from . import db
from .graph import build_graph
from .state import FocusFlowState, new_state

_graph = None

# Minimum sample size before a preference nudges behaviour, so a single
# early data point doesn't overfit the very first few uses.
_MIN_SAMPLES = 3


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def load_or_new_state(session_id: str | None = None) -> FocusFlowState:
    saved = db.load_state(session_id=session_id)
    if saved is not None:
        return saved
    return new_state()


def _estimate_ratio(prefs: dict) -> float | None:
    count = prefs.get("estimate_ratio_count", 0)
    if count < _MIN_SAMPLES:
        return None
    return prefs["estimate_ratio_sum"] / count


def _personalization_hint(prefs: dict) -> str:
    parts = []
    ratio = _estimate_ratio(prefs)
    if ratio is not None:
        if ratio > 1.3:
            parts.append(
                f"This user tends to need about {ratio:.1f}x the time you'd "
                "normally estimate, so scale estimated_minutes up and keep steps small."
            )
        elif ratio < 0.7:
            parts.append(
                f"This user tends to finish in about {ratio:.1f}x the time you'd "
                "normally estimate; slightly larger time estimates are fine."
            )

    total = prefs.get("breakdown_total", 0)
    if total >= _MIN_SAMPLES:
        rejection_rate = prefs.get("breakdown_rejections", 0) / total
        if rejection_rate > 0.3:
            parts.append(
                "This user often finds the first step still too big and splits it "
                "further -- make the first step noticeably smaller and more granular than usual."
            )
    return " ".join(parts)


def _run(
    state: FocusFlowState,
    user_input: str,
    intent: str | None = None,
    session_id: str | None = None,
) -> FocusFlowState:
    prefs = db.load_preferences(session_id=session_id)

    state = dict(state)
    state["user_input"] = user_input
    state["intent"] = intent or ""
    state["personalization_hint"] = _personalization_hint(prefs)
    state["estimate_ratio"] = _estimate_ratio(prefs) or 0.0

    result = _get_graph().invoke(state)
    db.save_state(result, session_id=session_id)

    response = result.get("response", {})
    actual = response.get("actual_minutes")
    estimated = response.get("estimated_minutes_for_step")
    if actual is not None and estimated:
        db.record_step_duration(actual, estimated, session_id=session_id)
    if response.get("type") == "task_complete":
        db.record_breakdown_outcome(
            response.get("breakdown_was_split", False), session_id=session_id
        )

    db.log_event(
        result.get("intent", ""),
        {"user_input": user_input, "response": response},
        session_id=session_id,
    )
    return result


def handle_message(
    state: FocusFlowState, user_input: str, session_id: str | None = None
) -> FocusFlowState:
    """Free-text turn: router classifies intent from the text and focus_mode."""
    return _run(state, user_input, session_id=session_id)


def start_focus(
    state: FocusFlowState, goal: str, session_id: str | None = None
) -> FocusFlowState:
    """UI shortcut: user picked a goal to start now (e.g. from Brain Dump priorities)."""
    return _run(state, goal, intent="new_task", session_id=session_id)


def mark_step_done(state: FocusFlowState, session_id: str | None = None) -> FocusFlowState:
    return _run(state, "done", intent="continue_focus", session_id=session_id)


def split_current_step(state: FocusFlowState, session_id: str | None = None) -> FocusFlowState:
    """UI shortcut: "this step is still too big" -- ask for a smaller one."""
    return _run(state, state.get("current_step", ""), intent="split_step", session_id=session_id)


def resume(state: FocusFlowState, session_id: str | None = None) -> FocusFlowState:
    return _run(state, "resume", intent="resume", session_id=session_id)


def reset_all(session_id: str | None = None) -> FocusFlowState:
    db.delete_all(session_id=session_id)
    return new_state()


def set_language(
    state: FocusFlowState, lang: str, session_id: str | None = None
) -> FocusFlowState:
    updated = dict(state)
    updated["lang"] = lang
    db.save_state(updated, session_id=session_id)
    return updated


def record_cognitive_load(rating: str, session_id: str | None = None) -> None:
    """Self-reported effort after a completed task (PRD section 10)."""
    db.log_event("cognitive_load", {"rating": rating}, session_id=session_id)
