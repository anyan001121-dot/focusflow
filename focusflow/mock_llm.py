"""Heuristic fallback used when no LLM API key is configured.

This is intentionally simple pattern-matching, not a language model. It
exists so the app is runnable end-to-end (Brain Dump, Breakdown,
Interruption handling) with zero setup. Quality improves once a real
ANTHROPIC_API_KEY or OPENAI_API_KEY is set — see focusflow/llm.py.

Every function returns the same JSON-shaped object a real LLM call would,
per the schemas documented in focusflow/prompts.py.
"""

from __future__ import annotations

import re

_SPLIT_RE = re.compile(r"[,，、;；\n]+|(?:\band\b)|然后|接着|还要|还有")

_HIGH_URGENCY_WORDS = [
    "urgent", "asap", "today", "deadline", "due", "interview",
    "今天", "紧急", "截止", "面试", "马上",
]
_LOW_URGENCY_WORDS = [
    "someday", "maybe", "eventually", "以后", "有空", "也许", "或许",
]
_IDEA_WORDS = ["idea:", "maybe i should", "或许可以", "也许可以", "考虑一下"]


def run(task: str, user_text: str) -> dict:
    if task == "brain_dump":
        return _brain_dump(user_text)
    if task == "breakdown":
        return _breakdown(user_text)
    if task == "interruption":
        return _interruption(user_text)
    raise ValueError(f"mock_llm: unknown task {task!r}")


def _brain_dump(user_text: str) -> dict:
    fragments = [f.strip() for f in _SPLIT_RE.split(user_text) if f.strip()]
    tasks = []
    for frag in fragments:
        low = frag.lower()
        if any(w in low for w in _HIGH_URGENCY_WORDS):
            urgency = "high"
        elif any(w in low for w in _LOW_URGENCY_WORDS):
            urgency = "low"
        else:
            urgency = "medium"
        actionable = not any(w in low for w in _IDEA_WORDS)
        tasks.append({"task": frag, "urgency": urgency, "actionable": actionable})
    return {"tasks": tasks}


_TEMPLATES = [
    (["面试", "interview"], "Open one relevant interview question list or job description and read only the first item."),
    (["简历", "cv", "resume"], "Open your CV file and re-read just the top section."),
    (["论文", "dissertation", "thesis", "discussion"], "Open the document and scroll to the relevant section heading."),
    (["邮件", "email", "reply"], "Open the email thread and re-read the last message only."),
    (["健身", "gym", "workout", "运动"], "Put on your workout clothes."),
]


def _breakdown(goal_text: str) -> dict:
    low = goal_text.lower()
    action = None
    for keywords, template in _TEMPLATES:
        if any(k in low for k in keywords):
            action = template
            break
    if action is None:
        action = f"Open whatever you need for '{goal_text.strip()}' and look at just the first item."

    return {
        "task_title": goal_text.strip(),
        "first_step": {
            "action": action,
            "estimated_minutes": 5,
            "completion_condition": "You can see the content on screen and are looking at it.",
        },
        "next_steps": [
            {
                "action": "Identify the single smallest next detail to act on.",
                "estimated_minutes": 5,
                "completion_condition": "You have named one concrete thing to do next.",
            },
            {
                "action": "Do that one thing, without editing or polishing anything else.",
                "estimated_minutes": 10,
                "completion_condition": "That one thing is done, imperfect is fine.",
            },
        ],
    }


def _interruption(message: str) -> dict:
    return {
        "related": False,
        "reason": "Mock mode always treats new mentions as separate items; "
        "set an LLM API key for context-aware relatedness checks.",
    }
