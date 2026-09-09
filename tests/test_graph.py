"""Graph tests run against the heuristic mock LLM (no API key required)."""

import os

os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("OPENAI_API_KEY", None)

from focusflow.graph import build_graph
from focusflow.state import new_state


def test_brain_dump_produces_at_most_three_priorities():
    graph = build_graph()
    state = new_state()
    state["user_input"] = (
        "I need to apply for jobs, fix my CV, learn Agent concepts, "
        "go to the gym, reply to an email and work on my dissertation"
    )
    result = graph.invoke(state)

    assert result["intent"] == "brain_dump"
    assert len(result["response"]["priorities"]) <= 3
    assert result["response"]["type"] == "brain_dump"


def test_new_task_breaks_down_into_concrete_first_step_and_starts_focus():
    graph = build_graph()
    state = new_state()
    state["user_input"] = "Prepare for an AI Product Manager interview"
    result = graph.invoke(state)

    assert result["intent"] == "new_task"
    assert result["focus_mode"] is True
    assert result["current_step"]
    assert result["estimated_time"] > 0
    assert result["response"]["type"] == "focus_start"


def test_interruption_during_focus_mode_does_not_replace_current_task():
    graph = build_graph()
    state = new_state()
    state["focus_mode"] = True
    state["current_task"] = "Write dissertation discussion"
    state["current_step"] = "Open the Discussion section."
    state["next_action"] = "Open the Discussion section."
    state["user_input"] = "I just remembered I need to buy detergent"

    result = graph.invoke(state)

    assert result["intent"] == "interruption"
    assert result["current_task"] == "Write dissertation discussion"
    assert result["current_step"] == "Open the Discussion section."
    assert "I just remembered I need to buy detergent" in result["later_list"]


def test_done_advances_to_next_queued_step():
    graph = build_graph()
    state = new_state()
    state["focus_mode"] = True
    state["current_task"] = "Prep interview"
    state["current_step"] = "Open one job description."
    state["task_queue"] = [
        {"action": "Highlight requirements.", "estimated_minutes": 5, "completion_condition": "done"}
    ]
    state["user_input"] = "done"

    result = graph.invoke(state)

    assert result["intent"] == "continue_focus"
    assert result["completed_steps"] == ["Open one job description."]
    assert result["current_step"] == "Highlight requirements."
    assert result["task_queue"] == []


def test_done_with_empty_queue_completes_task():
    graph = build_graph()
    state = new_state()
    state["focus_mode"] = True
    state["current_task"] = "Prep interview"
    state["current_step"] = "Highlight requirements."
    state["task_queue"] = []
    state["user_input"] = "done"

    result = graph.invoke(state)

    assert result["focus_mode"] is False
    assert result["response"]["type"] == "task_complete"


def test_resume_reports_current_state_without_dumping_everything():
    graph = build_graph()
    state = new_state()
    state["current_task"] = "Editing your AI PM CV"
    state["completed_steps"] = ["Education", "Skills section"]
    state["current_step"] = "RAG project description"
    state["next_action"] = "Rewrite the second project bullet."
    state["user_input"] = "I'm back"

    result = graph.invoke(state)

    assert result["intent"] == "resume"
    assert result["response"]["has_active_task"] is True
    assert result["response"]["next_action"] == "Rewrite the second project bullet."


def test_empty_input_is_clarify_not_a_crash():
    graph = build_graph()
    state = new_state()
    state["user_input"] = ""

    result = graph.invoke(state)

    assert result["intent"] == "clarify"
