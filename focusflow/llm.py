"""Provider-agnostic LLM wrapper.

FocusFlow never hard-codes a vendor. `complete_json()` picks a backend at
call time based on which API key is present in the environment, and falls
back to a small heuristic "mock" provider when no key is configured so the
app is fully runnable (with lower-quality output) before any key is added.

    ANTHROPIC_API_KEY set -> Anthropic Claude
    OPENAI_API_KEY set    -> OpenAI
    neither set           -> heuristic mock provider

All three paths return a parsed JSON-compatible Python object matching the
caller-supplied schema description, so callers never branch on provider.

Fault tolerance: a real API call gets a bounded timeout and a few
SDK-managed retries (both vendor SDKs already implement exponential
backoff for transient errors -- no need to reinvent that). If the call
still fails after retries, or the model returns text `_extract_json` can't
parse, FocusFlow logs a warning and **falls back to the same heuristic
mock output a missing API key would produce** rather than crashing the
page with a traceback.

That fallback is disclosed, not silent -- and not disclosed uniformly
either. The returned dict carries a `FALLBACK_FLAG` key set to one of:

    "auth"        an invalid/expired API key -- this will keep happening
                  on every call until the user fixes it, so it's worth a
                  real, persistent error pointing at the Setup page.
    "rate_limit"  a quota/rate-limit hit -- usually resolves on its own.
    "transient"   a timeout, connection error, or other one-off failure.
    "parse"       the model's response didn't parse as JSON.

focusflow/graph.py surfaces this in the response so the UI (app.py) can
match the loudness of the disclosure to how actionable it is: a wrong API
key gets a real error, a rate limit gets a soft warning, everything else
gets a one-line caption. Treating all of these the same way would either
alarm someone over a one-off network blip, or let a genuinely broken key
go unnoticed indefinitely behind an ever-present "having a hiccup" message.
"""

from __future__ import annotations

import json
import os
import re
import warnings
from typing import Any

from . import mock_llm

_TIMEOUT_SECONDS = 20.0
_MAX_RETRIES = 2

FALLBACK_FLAG = "_llm_fallback"


class LLMError(RuntimeError):
    pass


def _extract_json(text: str) -> Any:
    """Best-effort extraction of a JSON object/array from an LLM response."""
    text = text.strip()
    # Strip markdown code fences if present.
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fall back to grabbing the first {...} or [...] block.
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    raise LLMError(f"Could not parse JSON from LLM response: {text[:200]!r}")


def active_provider() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "mock"


def _classify_error(provider: str, exc: Exception) -> str:
    """Sort a provider failure into "auth" / "rate_limit" / "transient" /
    "parse" -- see module docstring for why the distinction matters."""
    if isinstance(exc, LLMError):
        return "parse"
    try:
        if provider == "anthropic":
            import anthropic

            if isinstance(exc, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)):
                return "auth"
            if isinstance(exc, anthropic.RateLimitError):
                return "rate_limit"
        elif provider == "openai":
            import openai

            if isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError)):
                return "auth"
            if isinstance(exc, openai.RateLimitError):
                return "rate_limit"
    except Exception:  # noqa: BLE001 -- classification must never itself fail
        pass
    return "transient"


def _fall_back_to_mock(provider: str, task: str, user: str, lang: str, ratio, exc: Exception) -> Any:
    reason = _classify_error(provider, exc)
    warnings.warn(
        f"FocusFlow: {provider} call failed ({exc.__class__.__name__}: {exc}); "
        f"falling back to practice-mode output for this turn (reason: {reason}).",
        RuntimeWarning,
        stacklevel=3,
    )
    result = mock_llm.run(task, user, lang=lang, ratio=ratio)
    # Tag the result so the caller can disclose it -- see graph.py, which
    # pops this key before treating the rest as the normal schema.
    if isinstance(result, dict):
        result[FALLBACK_FLAG] = reason
    return result


def complete_json(
    system: str, user: str, *, task: str, lang: str = "en", ratio: float | None = None
) -> Any:
    """Ask the active LLM provider for a JSON response.

    `task` names the mock_llm heuristic to use if no API key is configured
    (e.g. "brain_dump", "breakdown", "interruption"), so the mock provider
    can produce a schema-appropriate stub without a real model call. `lang`
    ("en"/"zh") is forwarded to the mock provider so its canned text matches
    the caller-supplied `system` prompt's requested language; for real
    providers the language instruction already lives in `system`. `ratio`
    is the user's long-term actual/estimated time ratio (see
    focusflow/db.py:record_step_duration) -- real providers get the same
    signal via the personalization note baked into `system`, the mock
    provider needs it passed explicitly since it never reads `system`.
    """
    provider = active_provider()
    if provider == "anthropic":
        try:
            return _extract_json(_call_anthropic(system, user))
        except Exception as exc:  # noqa: BLE001 -- deliberate: see module docstring
            return _fall_back_to_mock(provider, task, user, lang, ratio, exc)
    if provider == "openai":
        try:
            return _extract_json(_call_openai(system, user))
        except Exception as exc:  # noqa: BLE001 -- deliberate: see module docstring
            return _fall_back_to_mock(provider, task, user, lang, ratio, exc)
    return mock_llm.run(task, user, lang=lang, ratio=ratio)


def _call_anthropic(system: str, user: str) -> str:
    import anthropic

    client = anthropic.Anthropic(timeout=_TIMEOUT_SECONDS, max_retries=_MAX_RETRIES)
    model = os.environ.get("FOCUSFLOW_ANTHROPIC_MODEL", "claude-sonnet-5")
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def _call_openai(system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI(timeout=_TIMEOUT_SECONDS, max_retries=_MAX_RETRIES)
    model = os.environ.get("FOCUSFLOW_OPENAI_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""
