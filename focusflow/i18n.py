"""UI string tables for the Streamlit front end.

Agent-generated content (task text, breakdown steps, etc.) is localized at
the LLM/mock layer -- see prompts.py and mock_llm.py. This module only
covers static interface chrome (labels, buttons, captions) so the whole
page reads consistently in the user's chosen language.

Usage: `from focusflow.i18n import t; t(lang, "start_button")`
"""

from __future__ import annotations

LANGUAGES = {"en": "English", "zh": "中文"}

_STRINGS: dict[str, dict[str, str]] = {
    "disclaimer": {
        "en": "An executive-function assistant. Not a medical device -- it does not diagnose or treat ADHD.",
        "zh": "一个执行功能助手，不是医疗设备——不诊断也不治疗 ADHD。",
    },
    "llm_backend_label": {
        "en": "LLM backend: {provider}",
        "zh": "LLM 后端：{provider}",
    },
    "provider_anthropic": {"en": "Anthropic", "zh": "Anthropic"},
    "provider_openai": {"en": "OpenAI", "zh": "OpenAI"},
    "provider_mock": {
        "en": "Mock (no API key set)",
        "zh": "Mock 模式（未设置 API key）",
    },
    "language_label": {"en": "Language", "zh": "语言"},
    "later_list_header": {
        "en": "Later list ({n})",
        "zh": "稍后列表（{n}）",
    },
    "later_list_empty": {
        "en": "Nothing parked here yet.",
        "zh": "还没有暂存的事项。",
    },
    "resume_button": {
        "en": "Where was I? (Resume)",
        "zh": "我刚才在做什么？（继续）",
    },
    "privacy_header": {"en": "Privacy", "zh": "隐私"},
    "privacy_caption": {
        "en": "All data is stored locally in focusflow.db.",
        "zh": "所有数据都保存在本地 focusflow.db 文件中。",
    },
    "delete_button": {
        "en": "Delete all my data",
        "zh": "删除我的所有数据",
    },
    "resume_welcome": {"en": "**Welcome back.**", "zh": "**欢迎回来。**"},
    "resume_you_were": {
        "en": "You were: **{task}**",
        "zh": "你正在做：**{task}**",
    },
    "resume_completed_header": {"en": "Completed:", "zh": "已完成："},
    "resume_next_action": {
        "en": "**Next action:** {action}",
        "zh": "**下一步：** {action}",
    },
    "resume_estimated": {
        "en": "Estimated time: ~{minutes} min",
        "zh": "预计用时：约 {minutes} 分钟",
    },
    "resume_nothing": {
        "en": "Nothing to resume yet. Start by telling me what's on your mind below.",
        "zh": "还没有可以继续的任务，先在下面写下你脑子里想的事情吧。",
    },
    "clarify_message": {
        "en": "What's on your mind? You can dump several things at once, or name one thing you want to start.",
        "zh": "你在想什么？可以一次性把几件事都写出来，也可以直接说一件你想开始做的事。",
    },
    "brain_dump_header": {"en": "Here's what I heard", "zh": "我整理了一下"},
    "brain_dump_empty": {
        "en": "I couldn't find a clear task in there -- try naming one thing directly.",
        "zh": "没有找到明确的任务，试着直接说一件具体的事吧。",
    },
    "urgency_label": {
        "en": "urgency: {urgency}",
        "zh": "紧急程度：{urgency}",
    },
    "start_button": {"en": "Start", "zh": "开始"},
    "later_parked": {
        "en": "Parked {n} lower-priority item(s) in the Later list.",
        "zh": "已把 {n} 项优先级较低的事情放进稍后列表。",
    },
    "ideas_header": {
        "en": "Ideas / non-actionable ({n})",
        "zh": "想法 / 暂不可执行（{n}）",
    },
    "focus_header": {"en": "Current focus", "zh": "当前焦点"},
    "focus_goal": {"en": "**Goal:** {goal}", "zh": "**目标：** {goal}"},
    "focus_start_here": {
        "en": "**Start here:** {step}",
        "zh": "**从这里开始：** {step}",
    },
    "focus_estimated": {"en": "~{minutes} min", "zh": "约 {minutes} 分钟"},
    "interruption_captured": {
        "en": "Captured for later. Back to your current focus above.",
        "zh": "已记录到稍后列表。回到上面你当前的任务继续吧。",
    },
    "interruption_related": {
        "en": "Noted -- looks related to what you're already doing.",
        "zh": "已记下——看起来和你正在做的事情有关。",
    },
    "completed_header": {"en": "Completed ({n})", "zh": "已完成（{n}）"},
    "done_button": {"en": "✅ Done with this step", "zh": "✅ 这一步完成了"},
    "aside_label": {
        "en": "Anything else on your mind right now?",
        "zh": "现在脑子里还有别的事情吗？",
    },
    "aside_placeholder": {
        "en": "e.g. I just remembered I need to buy detergent",
        "zh": "比如：我突然想起要买洗衣液",
    },
    "send_button": {"en": "Send", "zh": "发送"},
    "task_complete_message": {
        "en": "Finished ‘{task}’ in {steps} step(s).",
        "zh": "完成了「{task}」，一共 {steps} 步。",
    },
    "whats_on_mind_header": {"en": "What's on your mind?", "zh": "你在想什么？"},
    "whats_on_mind_caption": {
        "en": "Dump everything messily, or name one thing you want to start right now.",
        "zh": "把想到的事情随意写出来，或者直接说一件想马上开始的事。",
    },
    "go_button": {"en": "Go", "zh": "开始"},
}

_URGENCY_LABELS = {
    "high": {"en": "high", "zh": "高"},
    "medium": {"en": "medium", "zh": "中"},
    "low": {"en": "low", "zh": "低"},
}


def t(lang: str, key: str, **kwargs) -> str:
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("en", key))
    return text.format(**kwargs) if kwargs else text


def urgency_label(lang: str, urgency: str) -> str:
    entry = _URGENCY_LABELS.get(urgency, {})
    return entry.get(lang, entry.get("en", urgency))
