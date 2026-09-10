"""LLM fault tolerance: a failing real-provider call must degrade to the
mock output, never propagate a raw exception up to the Streamlit page."""

import pytest

from focusflow import llm


def test_active_provider_falls_back_to_mock_with_no_keys(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert llm.active_provider() == "mock"


def test_anthropic_failure_falls_back_to_mock_output(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def _boom(system, user):
        raise ConnectionError("simulated network failure")

    monkeypatch.setattr(llm, "_call_anthropic", _boom)

    with pytest.warns(RuntimeWarning, match="falling back to practice-mode"):
        result = llm.complete_json(
            "system prompt", "Prepare for an interview", task="breakdown"
        )

    assert "first_step" in result
    assert "action" in result["first_step"]


def test_malformed_json_response_falls_back_to_mock_output(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    monkeypatch.setattr(llm, "_call_anthropic", lambda system, user: "not json at all")

    with pytest.warns(RuntimeWarning, match="falling back to practice-mode"):
        result = llm.complete_json("system prompt", "hello", task="brain_dump")

    assert "tasks" in result


def test_openai_failure_falls_back_to_mock_output(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-real")

    def _boom(system, user):
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr(llm, "_call_openai", _boom)

    with pytest.warns(RuntimeWarning, match="falling back to practice-mode"):
        result = llm.complete_json("system prompt", "hello", task="interruption")

    assert "related" in result
