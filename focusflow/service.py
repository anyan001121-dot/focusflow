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

from datetime import datetime, timezone

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
    state["undo_snapshot"] = {}
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
    if state.get("paused_at"):
        return state
    return _run(state, user_input, session_id=session_id)


def start_focus(
    state: FocusFlowState, goal: str, session_id: str | None = None
) -> FocusFlowState:
    """UI shortcut: user picked a goal to start now (e.g. from Brain Dump priorities)."""
    if state.get("focus_mode") or not goal.strip():
        return state
    return _run(state, goal, intent="new_task", session_id=session_id)


def mark_step_done(state: FocusFlowState, session_id: str | None = None) -> FocusFlowState:
    if not state.get("focus_mode") or state.get("paused_at"):
        return state
    prefs = db.load_preferences(session_id=session_id)
    updated = _run(state, "done", intent="continue_focus", session_id=session_id)
    updated = _save_edit(state, updated, session_id)
    updated["undo_snapshot"]["preferences"] = prefs
    db.save_state(updated, session_id=session_id)
    return updated


def split_current_step(state: FocusFlowState, session_id: str | None = None) -> FocusFlowState:
    """UI shortcut: "this step is still too big" -- ask for a smaller one."""
    if not state.get("focus_mode") or state.get("paused_at"):
        return state
    return _run(state, state.get("current_step", ""), intent="split_step", session_id=session_id)


def resume(state: FocusFlowState, session_id: str | None = None) -> FocusFlowState:
    if state.get("paused_at"):
        state = dict(state)
        now = datetime.now(timezone.utc)
        paused = datetime.fromisoformat(state["paused_at"])
        started = state.get("step_start_time")
        if started:
            state["step_start_time"] = (datetime.fromisoformat(started) + (now - paused)).isoformat()
        if not started:
            state["step_start_time"] = now.isoformat()
        state["paused_at"] = ""
    return _run(state, "resume", intent="resume", session_id=session_id)


def pause_focus(state: FocusFlowState, note: str = "", session_id: str | None = None) -> FocusFlowState:
    """Keep the exact return point; an explicit break is not task abandonment."""
    if not state.get("focus_mode") or state.get("paused_at"):
        return state
    updated = dict(state)
    updated.update(undo_snapshot={}, paused_at=datetime.now(timezone.utc).isoformat(), resume_note=note.strip(),
                   response={"type": "paused"})
    db.save_state(updated, session_id=session_id)
    db.log_event("pause", {}, session_id=session_id)
    return updated


def resolve_later(state: FocusFlowState, index: int, start: bool = False,
                  session_id: str | None = None) -> FocusFlowState:
    """Review parked items only outside an active (including paused) task."""
    items = list(state.get("later_list", []))
    if state.get("focus_mode") or not 0 <= index < len(items):
        return state
    item = items.pop(index)
    updated = dict(state, later_list=items)
    if start:
        return start_focus(updated, item, session_id)
    db.log_event("later_resolved", {}, session_id=session_id)
    return _save_edit(state, updated, session_id)


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


# Explicit UI actions never pass note text through the intent router.
def capture_thought(state, text, session_id=None):
    if not text.strip():
        return state
    updated = dict(state, later_list=[*state.get("later_list", []), text.strip()],
                   response={"type": "interruption", "captured": True})
    return _save_edit(state, updated, session_id)


def _save_edit(previous, updated, session_id=None):
    from copy import deepcopy
    snapshot = deepcopy(dict(previous))
    snapshot.pop("undo_snapshot", None)
    updated = dict(updated, undo_snapshot={"state": snapshot})
    db.save_state(updated, session_id=session_id)
    return updated


def undo_edit(state, session_id=None):
    snapshot = state.get("undo_snapshot", {})
    if not snapshot:
        return state
    updated = dict(snapshot["state"])
    if "preferences" in snapshot:
        db.save_preferences(snapshot["preferences"], session_id=session_id)
    db.save_state(updated, session_id=session_id)
    db.log_event("undo", {"note": "Previous action reverted; raw events retained."}, session_id=session_id)
    return updated


def park_focus(state, session_id=None):
    """Move an explicitly paused task into the return shelf, preserving its queue."""
    if not state.get("paused_at"):
        return state
    task = {k: v for k, v in state.items() if k not in
            ("parked_tasks", "later_list", "undo_snapshot", "response")}
    updated = dict(new_state(), lang=state.get("lang", "en"),
                   later_list=state.get("later_list", []),
                   parked_tasks=[*state.get("parked_tasks", []), task])
    return _save_edit(state, updated, session_id)


def restore_parked(state, index, session_id=None):
    tasks = list(state.get("parked_tasks", []))
    if state.get("focus_mode") or not 0 <= index < len(tasks):
        return state
    task = tasks.pop(index)
    updated = dict(state, **{k: v for k, v in task.items() if k != "lang"})
    updated.update(parked_tasks=tasks, undo_snapshot={})
    return resume(updated, session_id)


def edit_step(state, action, condition, session_id=None):
    if not state.get("focus_mode") or state.get("paused_at") or not action.strip():
        return state
    updated = dict(state, current_step=action.strip(), next_action=action.strip(),
                   completion_condition=condition.strip(),
                   step_start_time=datetime.now(timezone.utc).isoformat(),
                   response={"type": "step_edited"})
    return _save_edit(state, updated, session_id)


def continue_goal(state, action, session_id=None):
    """A user-chosen next action retains the goal and all completed work."""
    if state.get("focus_mode") or not state.get("current_goal") or not action.strip():
        return state
    updated = dict(state, focus_mode=True, current_step=action.strip(), next_action=action.strip(),
                   task_queue=[], completion_condition="", estimated_time=5,
                   step_start_time=datetime.now(timezone.utc).isoformat(),
                   response={"type": "focus_start"})
    return _save_edit(state, updated, session_id)


def import_return_file(state, raw, session_id=None):
    """Merge return points without replacing current work; importing is undoable."""
    from .return_file import read_return_file
    incoming = read_return_file(raw)
    tasks = list(state.get('parked_tasks', []))
    def identity(task):
        return (task.get('current_goal'), task.get('current_step'), tuple(task.get('completed_steps', [])),
                tuple((step.get('action'), step.get('completion_condition', '')) for step in task.get('task_queue', [])), task.get('resume_note', ''))
    known = {identity(t) for t in tasks}
    if state.get('focus_mode'):
        known.add(identity(state))
    for task in incoming['parked_tasks']:
        if identity(task) not in known:
            tasks.append(task)
            known.add(identity(task))
    later = list(state.get('later_list', []))
    later.extend(item for item in incoming['later_list'] if item not in later)
    return _save_edit(state, dict(state, parked_tasks=tasks, later_list=later), session_id)


def add_preparation_step(state, reason, detail='', session_id=None):
    """Insert an explicit prerequisite, then return to the original step."""
    if not state.get('focus_mode') or state.get('paused_at') or reason not in ('how', 'missing'):
        return state
    detail = detail.strip()
    if not detail:
        return state
    zh = state.get('lang') == 'zh'
    if reason == 'missing':
        action = f'找到或向相关的人询问「{detail}」的获取方式。' if zh else f'Find where to get "{detail}", or ask someone who knows.'
        condition = '已找到获取方式，或记下了等待谁提供。' if zh else 'You have a source, or have noted who you are waiting for.'
    else:
        action = f'找一个解释「{detail}」的例子，只记下一条能用在当前步骤的做法。' if zh else f'Find one example explaining "{detail}" and note one action you can use.'
        condition = '写下了一条可尝试的做法；仍不明白时可以暂停。' if zh else 'One action is written down; you can pause if it is still unclear.'
    original = dict(action=state['current_step'], completion_condition=state.get('completion_condition', ''), estimated_minutes=state.get('estimated_time', 5))
    updated = dict(state, current_step=action, next_action=action, completion_condition=condition,
                   estimated_time=5, task_queue=[original, *state.get('task_queue', [])],
                   step_start_time=datetime.now(timezone.utc).isoformat(), response={'type': 'preparation'})
    return _save_edit(state, updated, session_id)
