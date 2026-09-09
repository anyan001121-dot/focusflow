"""LangGraph state machine implementing the FocusFlow agent architecture.

    Intent Router
        -> brain_dump_node      (messy input -> top-3 priorities)
        -> breakdown_node       (one goal -> one small first step)
        -> interruption_node    (focus-mode aside -> Later List, keep focus)
        -> continue_focus_node  ("done" -> advance to next queued step)
        -> resume_node          (rebuild a minimal "where you left off")
        -> clarify_node         (empty/unrecognized input)

Every node only ever returns the fields it changed; LangGraph merges them
into the running FocusFlowState. Persistence is handled by the caller
(see focusflow/service.py) -- these nodes are pure and unit-testable
without a database.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from langgraph.graph import END, StateGraph

from . import llm, prompts
from .state import FocusFlowState

_SPLIT_RE = re.compile(r"[,，、;；\n]+|(?:\band\b)|然后|接着|还要|还有")

_RESUME_WORDS = ["resume", "i'm back", "im back", "continue", "我回来了", "继续"]
_DONE_WORDS = ["done", "finished", "completed", "完成了", "做完了", "finish"]

_URGENCY_RANK = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Intent routing
# ---------------------------------------------------------------------------

def classify_intent(state: FocusFlowState) -> str:
    """Decide what to do with this turn's input.

    If the caller already set `intent` (e.g. a UI button that unambiguously
    means "start focus on this task"), that choice is respected and no
    text classification happens.
    """
    if state.get("intent"):
        return state["intent"]

    text = (state.get("user_input") or "").strip()
    low = text.lower()
    if not text:
        return "clarify"

    if any(w in low for w in _RESUME_WORDS):
        return "resume"

    if state.get("focus_mode"):
        if any(w in low for w in _DONE_WORDS):
            return "continue_focus"
        return "interruption"

    fragments = [f for f in _SPLIT_RE.split(text) if f.strip()]
    if len(fragments) >= 2:
        return "brain_dump"
    return "new_task"


def router_node(state: FocusFlowState) -> dict:
    return {"intent": classify_intent(state)}


def _route(state: FocusFlowState) -> str:
    return state["intent"]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def brain_dump_node(state: FocusFlowState) -> dict:
    lang = state.get("lang", "en")
    result = llm.complete_json(
        prompts.brain_dump_system(lang), state["user_input"], task="brain_dump", lang=lang
    )
    tasks = result.get("tasks", [])
    actionable = [t for t in tasks if t.get("actionable", True)]
    ideas = [t for t in tasks if not t.get("actionable", True)]
    actionable.sort(key=lambda t: _URGENCY_RANK.get(t.get("urgency", "medium"), 1))

    priorities = actionable[:3]
    later = [t["task"] for t in actionable[3:]]

    return {
        "priorities": priorities,
        "later_list": state.get("later_list", []) + later,
        "response": {
            "type": "brain_dump",
            "priorities": priorities,
            "ideas": ideas,
            "later_list_additions": later,
        },
    }


def breakdown_node(state: FocusFlowState) -> dict:
    lang = state.get("lang", "en")
    goal = state.get("user_input", "").strip()
    result = llm.complete_json(
        prompts.breakdown_system(lang), goal, task="breakdown", lang=lang
    )
    first = result["first_step"]
    next_steps = result.get("next_steps", [])

    return {
        "current_goal": goal,
        "current_task": result.get("task_title", goal),
        "current_step": first["action"],
        "next_action": first["action"],
        "estimated_time": first.get("estimated_minutes", 5),
        "task_queue": next_steps,
        "completed_steps": [],
        "focus_mode": True,
        "interruption_count": 0,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "response": {
            "type": "focus_start",
            "current_goal": goal,
            "current_task": result.get("task_title", goal),
            "current_step": first["action"],
            "estimated_time": first.get("estimated_minutes", 5),
            "completion_condition": first.get("completion_condition", ""),
        },
    }


def interruption_node(state: FocusFlowState) -> dict:
    lang = state.get("lang", "en")
    prompt_input = (
        f"Current task: {state.get('current_task', '')}\n"
        f"New message: {state.get('user_input', '')}"
    )
    result = llm.complete_json(
        prompts.interruption_system(lang), prompt_input, task="interruption", lang=lang
    )
    related = result.get("related", False)
    later_list = list(state.get("later_list", []))
    captured = not related
    if captured:
        later_list.append(state["user_input"])

    return {
        "later_list": later_list,
        "interruption_count": state.get("interruption_count", 0) + (1 if captured else 0),
        "response": {
            "type": "interruption",
            "captured": captured,
            "current_task": state.get("current_task", ""),
            "current_step": state.get("current_step", ""),
            "next_action": state.get("next_action", ""),
        },
    }


def continue_focus_node(state: FocusFlowState) -> dict:
    completed = list(state.get("completed_steps", []))
    if state.get("current_step"):
        completed.append(state["current_step"])

    queue = list(state.get("task_queue", []))
    if queue:
        nxt = queue.pop(0)
        return {
            "completed_steps": completed,
            "task_queue": queue,
            "current_step": nxt["action"],
            "next_action": nxt["action"],
            "estimated_time": nxt.get("estimated_minutes", 5),
            "response": {
                "type": "step_advance",
                "completed_steps": completed,
                "current_step": nxt["action"],
                "estimated_time": nxt.get("estimated_minutes", 5),
                "completion_condition": nxt.get("completion_condition", ""),
            },
        }

    task_name = state.get("current_task", "")
    steps_count = len(completed)
    summary = f"Finished '{task_name}' in {steps_count} step(s)."  # internal log only
    return {
        "completed_steps": completed,
        "focus_mode": False,
        "current_step": "",
        "next_action": "",
        "session_summary": summary,
        "response": {
            "type": "task_complete",
            "current_task": task_name,
            "steps_count": steps_count,
        },
    }


def resume_node(state: FocusFlowState) -> dict:
    if not state.get("current_task"):
        return {
            "response": {
                "type": "resume",
                "has_active_task": False,
            }
        }
    return {
        "response": {
            "type": "resume",
            "has_active_task": True,
            "current_task": state.get("current_task", ""),
            "completed_steps": state.get("completed_steps", []),
            "current_step": state.get("current_step", ""),
            "next_action": state.get("next_action", ""),
            "estimated_time": state.get("estimated_time", 0),
        }
    }


def clarify_node(state: FocusFlowState) -> dict:
    return {"response": {"type": "clarify"}}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(FocusFlowState)

    graph.add_node("router", router_node)
    graph.add_node("brain_dump", brain_dump_node)
    graph.add_node("new_task", breakdown_node)
    graph.add_node("interruption", interruption_node)
    graph.add_node("continue_focus", continue_focus_node)
    graph.add_node("resume", resume_node)
    graph.add_node("clarify", clarify_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        _route,
        {
            "brain_dump": "brain_dump",
            "new_task": "new_task",
            "interruption": "interruption",
            "continue_focus": "continue_focus",
            "resume": "resume",
            "clarify": "clarify",
        },
    )
    for node in ("brain_dump", "new_task", "interruption", "continue_focus", "resume", "clarify"):
        graph.add_edge(node, END)

    return graph.compile()
