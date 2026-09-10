"""Bounded-agency policy engine.

FocusFlow's LLM calls are allowed to *propose* an action, but never to
directly execute one -- this module is the deterministic gate every
proposal passes through before it can touch state. The pattern:

    Agent (LLM) observes state, proposes an action
                    |
    policy.enforce() checks the proposal against allowed_actions(state)
                    |
        in the allowed set?  -- yes --> execute as proposed
                    |
                    no
                    |
        downgrade to a safe default, execute that instead

The point isn't that the LLM can't be trusted to reason well -- it's that
"never abandon the active task without an explicit done/resume" is a
product guarantee, not a preference, and guarantees belong in code that
can't be talked out of them by a persuasive user message. This is
sometimes called "bounded" or "constrained" agency: the agent genuinely
chooses among options and can be wrong about which one is best, but it
cannot expand its own option set.

See focusflow/graph.py:interruption_node for the concrete use: the LLM is
explicitly permitted to propose "start_new_focus" (abandon the current
task), and explicitly will never be allowed to have that proposal take
effect while a task is in focus -- see test_policy.py and
test_graph.py::test_policy_blocks_agent_even_when_it_insists_on_switching_tasks
for the proof.
"""

from __future__ import annotations

from .state import FocusFlowState

# Every action the agent is allowed to *propose*, regardless of whether the
# policy will actually let it through in the current state.
ALL_ACTIONS = frozenset({"capture_to_later", "note_related", "start_new_focus"})

# The action substituted in whenever a proposal is rejected. Always safe:
# it changes nothing about the active task.
SAFE_DEFAULT = "capture_to_later"


def allowed_actions(state: FocusFlowState) -> frozenset[str]:
    """Which actions the agent's proposal is permitted to result in, right now.

    The one hard rule this product cannot compromise on: while a task is
    in focus, no proposal may replace or clear it. That rules out
    "start_new_focus" categorically -- not "usually", not "unless the LLM
    is confident" -- whenever focus_mode is on.
    """
    if state.get("focus_mode"):
        return ALL_ACTIONS - {"start_new_focus"}
    return ALL_ACTIONS


def enforce(proposed_action: str, state: FocusFlowState) -> tuple[str, bool]:
    """Validate a proposed action against the current state.

    Returns (action_to_execute, was_downgraded). `action_to_execute` is
    always a member of `allowed_actions(state)` -- callers never need to
    re-check.
    """
    allowed = allowed_actions(state)
    if proposed_action in allowed:
        return proposed_action, False
    return SAFE_DEFAULT, True
