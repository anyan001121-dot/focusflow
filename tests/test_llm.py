"""LLM fault tolerance: a failing real-provider call must degrade to the
mock output, never propagate a raw exception up to the Streamlit page --
and the *kind* of failure must be classified correctly, since app.py shows
a real error for "auth" but only a soft caption for a one-off blip."""

import pytest

from focusflow import llm


def test_active_provider_falls_back_to_mock_with_no_keys(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert llm.active_provider() == "mock"


def test_transient_anthropic_failure_falls_back_to_mock_output(monkeypatch):
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
    assert result[llm.FALLBACK_FLAG] == "transient"


def test_malformed_json_response_is_classified_as_parse_failure(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    monkeypatch.setattr(llm, "_call_anthropic", lambda system, user: "not json at all")

    with pytest.warns(RuntimeWarning, match="falling back to practice-mode"):
        result = llm.complete_json("system prompt", "hello", task="brain_dump")

    assert "tasks" in result
    assert result[llm.FALLBACK_FLAG] == "parse"


def test_openai_timeout_falls_back_to_mock_output(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-real")

    def _boom(system, user):
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr(llm, "_call_openai", _boom)

    with pytest.warns(RuntimeWarning, match="falling back to practice-mode"):
        result = llm.complete_json("system prompt", "hello", task="interruption")

    assert "action" in result
    assert result[llm.FALLBACK_FLAG] == "transient"


def test_anthropic_auth_failure_is_classified_as_auth(monkeypatch):
    import anthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exc = anthropic.AuthenticationError.__new__(anthropic.AuthenticationError)
    monkeypatch.setattr(llm, "_call_anthropic", lambda system, user: (_ for _ in ()).throw(exc))

    with pytest.warns(RuntimeWarning, match="reason: auth"):
        result = llm.complete_json("system prompt", "hello", task="breakdown")

    assert result[llm.FALLBACK_FLAG] == "auth"


def test_anthropic_rate_limit_is_classified_as_rate_limit(monkeypatch):
    import anthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exc = anthropic.RateLimitError.__new__(anthropic.RateLimitError)
    monkeypatch.setattr(llm, "_call_anthropic", lambda system, user: (_ for _ in ()).throw(exc))

    with pytest.warns(RuntimeWarning, match="reason: rate_limit"):
        result = llm.complete_json("system prompt", "hello", task="breakdown")

    assert result[llm.FALLBACK_FLAG] == "rate_limit"


def test_openai_auth_failure_is_classified_as_auth(monkeypatch):
    import openai

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-real")

    exc = openai.AuthenticationError.__new__(openai.AuthenticationError)
    monkeypatch.setattr(llm, "_call_openai", lambda system, user: (_ for _ in ()).throw(exc))

    with pytest.warns(RuntimeWarning, match="reason: auth"):
        result = llm.complete_json("system prompt", "hello", task="breakdown")

    assert result[llm.FALLBACK_FLAG] == "auth"


def test_successful_call_never_carries_a_fallback_flag(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    monkeypatch.setattr(
        llm, "_call_anthropic", lambda system, user: '{"tasks": []}'
    )

    result = llm.complete_json("system prompt", "hello", task="brain_dump")
    assert llm.FALLBACK_FLAG not in result
