"""Shared state schema passed through the FocusFlow LangGraph pipeline."""

from __future__ import annotations

from typing import TypedDict


class Step(TypedDict):
    action: str
    estimated_minutes: int
    completion_condition: str


class Priority(TypedDict):
    task: str
    urgency: str  # "high" | "medium" | "low"
    actionable: bool


class FocusFlowState(TypedDict, total=False):
    # raw input for the current turn
    user_input: str

    # routing
    intent: str

    # UI / agent output language: "en" or "zh"
    lang: str

    # active work
    current_goal: str
    current_task: str
    current_step: str
    next_action: str
    estimated_time: int

    # queues
    task_queue: list[Step]
    later_list: list[str]
    completed_steps: list[str]
    priorities: list[Priority]

    # session bookkeeping
    focus_mode: bool
    interruption_count: int
    session_summary: str
    start_time: str

    # what the UI renders for this turn
    response: dict


def new_state() -> FocusFlowState:
    """A fresh, empty session state."""
    return FocusFlowState(
        user_input="",
        intent="",
        lang="en",
        current_goal="",
        current_task="",
        current_step="",
        next_action="",
        estimated_time=0,
        task_queue=[],
        later_list=[],
        completed_steps=[],
        priorities=[],
        focus_mode=False,
        interruption_count=0,
        session_summary="",
        start_time="",
        response={},
    )
