"""Heuristic fallback used when no LLM API key is configured.

This is intentionally simple pattern-matching, not a language model. It
exists so the app is runnable end-to-end (Brain Dump, Breakdown,
Interruption handling) with zero setup, in either English or Chinese.
Quality improves once a real ANTHROPIC_API_KEY or OPENAI_API_KEY is set --
see focusflow/llm.py.

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


def run(task: str, user_text: str, lang: str = "en", ratio: float | None = None) -> dict:
    if task == "brain_dump":
        return _brain_dump(user_text)
    if task == "breakdown":
        return _breakdown(user_text, lang, ratio)
    if task == "interruption":
        return _interruption(user_text, lang)
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


# Each entry: (match keywords, English template, Chinese template)
_TEMPLATES = [
    (["面试", "interview"],
     "Open one relevant interview question list or job description and read only the first item.",
     "打开一份相关的面试题清单或职位描述，只读第一条。"),
    (["简历", "cv", "resume"],
     "Open your CV file and re-read just the top section.",
     "打开你的简历文件，只重新看一下最上面那部分。"),
    (["论文", "dissertation", "thesis", "discussion"],
     "Open the document and scroll to the relevant section heading.",
     "打开文档，滚动到相关章节的标题处。"),
    (["邮件", "email", "reply"],
     "Open the email thread and re-read the last message only.",
     "打开邮件对话，只重新看最后一条消息。"),
    (["健身", "gym", "workout", "运动"],
     "Put on your workout clothes.",
     "换上运动服。"),
]


def _scaled_minutes(base_minutes: int, ratio: float | None) -> int:
    """Adapt a base estimate using the user's long-term actual/estimated ratio.

    Clamped so personalization nudges the number without producing silly
    extremes off a small sample.
    """
    if not ratio:
        return base_minutes
    scaled = base_minutes * max(0.5, min(ratio, 2.5))
    return max(2, round(scaled))


def _breakdown(goal_text: str, lang: str = "en", ratio: float | None = None) -> dict:
    low = goal_text.lower()
    action = None
    for keywords, template_en, template_zh in _TEMPLATES:
        if any(k in low for k in keywords):
            action = template_zh if lang == "zh" else template_en
            break

    if action is None:
        if lang == "zh":
            action = f"打开完成「{goal_text.strip()}」需要用到的东西，先只看第一项。"
        else:
            action = f"Open whatever you need for '{goal_text.strip()}' and look at just the first item."

    if lang == "zh":
        completion_condition = "你已经能在屏幕上看到内容了。"
        next_steps = [
            {
                "action": "找出下一步最小的一个具体细节。",
                "estimated_minutes": _scaled_minutes(5, ratio),
                "completion_condition": "你已经说出了一件具体要做的事。",
            },
            {
                "action": "只做那一件事，先不打磨、不完善其他部分。",
                "estimated_minutes": _scaled_minutes(10, ratio),
                "completion_condition": "那件事做完了，不完美也没关系。",
            },
        ]
    else:
        completion_condition = "You can see the content on screen and are looking at it."
        next_steps = [
            {
                "action": "Identify the single smallest next detail to act on.",
                "estimated_minutes": _scaled_minutes(5, ratio),
                "completion_condition": "You have named one concrete thing to do next.",
            },
            {
                "action": "Do that one thing, without editing or polishing anything else.",
                "estimated_minutes": _scaled_minutes(10, ratio),
                "completion_condition": "That one thing is done, imperfect is fine.",
            },
        ]

    return {
        "task_title": goal_text.strip(),
        "first_step": {
            "action": action,
            "estimated_minutes": _scaled_minutes(5, ratio),
            "completion_condition": completion_condition,
        },
        "next_steps": next_steps,
    }


def _interruption(message: str, lang: str = "en") -> dict:
    """Mock never proposes "start_new_focus" -- it has no real judgment about
    urgency, so it always plays it safe. A real LLM is free to propose it;
    focusflow/policy.py is what actually decides whether that's allowed."""
    if lang == "zh":
        reason = "Mock 模式下默认把新提到的内容当作独立事项处理；配置 LLM API key 后可做更准确的判断。"
    else:
        reason = (
            "Mock mode always plays it safe and files new mentions away; "
            "set an LLM API key for more nuanced judgment calls."
        )
    return {"action": "capture_to_later", "reason": reason}
