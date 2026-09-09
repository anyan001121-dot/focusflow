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
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from . import mock_llm


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
        return _extract_json(_call_anthropic(system, user))
    if provider == "openai":
        return _extract_json(_call_openai(system, user))
    return mock_llm.run(task, user, lang=lang, ratio=ratio)


def _call_anthropic(system: str, user: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
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

    client = OpenAI()
    model = os.environ.get("FOCUSFLOW_OPENAI_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""
