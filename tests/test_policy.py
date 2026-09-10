"""The policy engine is the one piece of FocusFlow that a persuasive LLM
output must never be able to talk its way around. These tests exercise
focusflow/policy.py directly, independent of any LLM call."""

from focusflow.policy import ALL_ACTIONS, SAFE_DEFAULT, allowed_actions, enforce


def test_start_new_focus_is_categorically_disallowed_during_focus_mode():
    state = {"focus_mode": True}
    assert "start_new_focus" not in allowed_actions(state)


def test_start_new_focus_is_allowed_outside_focus_mode():
    state = {"focus_mode": False}
    assert "start_new_focus" in allowed_actions(state)


def test_enforce_passes_through_an_allowed_proposal_unchanged():
    state = {"focus_mode": True}
    action, downgraded = enforce("capture_to_later", state)
    assert action == "capture_to_later"
    assert downgraded is False


def test_enforce_downgrades_a_disallowed_proposal_to_the_safe_default():
    state = {"focus_mode": True}
    action, downgraded = enforce("start_new_focus", state)
    assert action == SAFE_DEFAULT
    assert downgraded is True


def test_enforce_downgrades_an_unrecognized_proposal_too():
    """A malformed / hallucinated action name is treated the same as a
    disallowed one -- fail closed, not open."""
    state = {"focus_mode": True}
    action, downgraded = enforce("do_something_the_model_invented", state)
    assert action == SAFE_DEFAULT
    assert downgraded is True


def test_enforced_action_is_always_a_member_of_allowed_actions():
    for focus_mode in (True, False):
        state = {"focus_mode": focus_mode}
        for proposal in ALL_ACTIONS | {"nonsense"}:
            action, _ = enforce(proposal, state)
            assert action in allowed_actions(state)
