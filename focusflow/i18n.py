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
    "split_button": {
        "en": "Still too big -- split it",
        "zh": "还是太大了——再拆一下",
    },
    "step_split_notice": {
        "en": "Broke that into something smaller.",
        "zh": "已经把它拆成更小的一步了。",
    },
    "timer_elapsed": {"en": "Elapsed: {mmss}", "zh": "已用时：{mmss}"},
    "timer_over_estimate": {
        "en": "Past the ~{minutes} min estimate -- that's normal, keep going or mark done when ready.",
        "zh": "已经超过约 {minutes} 分钟的预估——很正常，继续做或者做完了就点完成。",
    },
    "cognitive_load_prompt": {
        "en": "How much mental effort did that take?",
        "zh": "刚才那件事花了你多少心力？",
    },
    "cognitive_load_easy": {"en": "😌 Easy", "zh": "😌 轻松"},
    "cognitive_load_okay": {"en": "😐 Okay", "zh": "😐 还好"},
    "cognitive_load_hard": {"en": "😣 Hard", "zh": "😣 费劲"},
    "cognitive_load_thanks": {"en": "Noted, thanks.", "zh": "记下了，谢谢。"},
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
    "analytics_title": {"en": "📊 Analytics", "zh": "📊 分析看板"},
    "analytics_caption": {
        "en": "Local, single-user approximations from your own usage -- not a diagnostic tool.",
        "zh": "基于你自己本地使用数据的粗略统计——不是诊断工具。",
    },
    "metric_north_star": {
        "en": "Successful task starts (7d)",
        "zh": "近7天成功启动任务次数",
    },
    "metric_completion_rate": {"en": "Task completion rate", "zh": "任务完成率"},
    "metric_abandonment_rate": {"en": "Abandonment rate", "zh": "放弃率"},
    "metric_acceptance_rate": {
        "en": "Breakdown acceptance rate",
        "zh": "拆解接受率",
    },
    "metric_estimate_ratio": {
        "en": "Actual vs. estimated time",
        "zh": "实际用时 / 预估用时",
    },
    "metric_interruptions": {"en": "Interruptions captured", "zh": "捕获的打断次数"},
    "metric_cognitive_load": {"en": "Avg. cognitive load", "zh": "平均认知负荷"},
    "section_activity": {"en": "Activity by type", "zh": "各类活动次数"},
    "no_data_yet": {
        "en": "Not enough data yet -- use the app a bit more first.",
        "zh": "数据还不够——先多用一会儿再来看。",
    },
    "setup_title": {
        "en": "⚙️ Setup: connect a real LLM",
        "zh": "⚙️ 设置：接入真实 LLM",
    },
    "setup_intro": {
        "en": "FocusFlow runs out of the box on a small heuristic \"mock\" backend "
        "(see focusflow/mock_llm.py) so there's something to try immediately. "
        "For real task extraction and breakdown quality, connect an Anthropic or "
        "OpenAI API key.",
        "zh": "FocusFlow 默认跑在一个小型启发式 \"mock\" 后端上（见 focusflow/mock_llm.py），"
        "这样你可以立刻上手试用。想要更好的任务提取和拆解质量，需要接入 Anthropic 或 OpenAI 的 API key。",
    },
    "setup_order_note": {
        "en": "Check these off in any order -- nothing here is gated on the step above it.",
        "zh": "这些可以按任意顺序打勾——不需要按上下顺序来。",
    },
    "setup_status_connected": {
        "en": "✅ Connected: {provider}",
        "zh": "✅ 已连接：{provider}",
    },
    "setup_status_mock": {
        "en": "Not connected yet -- currently running on the Mock backend.",
        "zh": "还没连接——目前在用 Mock 模式。",
    },
    "step_get_key": {
        "en": "Get an API key from Anthropic or OpenAI",
        "zh": "去 Anthropic 或 OpenAI 申请一个 API key",
    },
    "step_copy_env": {
        "en": "In the project folder, copy `.env.example` to a new file named `.env`",
        "zh": "在项目目录里，把 `.env.example` 复制一份，命名为 `.env`",
    },
    "step_paste_key": {
        "en": "Open `.env` and paste your key after `ANTHROPIC_API_KEY=` or `OPENAI_API_KEY=`",
        "zh": "打开 `.env`，把你的 key 粘贴到 `ANTHROPIC_API_KEY=` 或 `OPENAI_API_KEY=` 后面",
    },
    "step_restart": {
        "en": "Restart the app (stop it, then run `streamlit run app.py` again)",
        "zh": "重启应用（停掉后重新运行 `streamlit run app.py`）",
    },
    "step_verify": {
        "en": "Come back to this page and check the status above",
        "zh": "回到这个页面，看看上面的状态",
    },
    "for_others_header": {
        "en": "For other people running this project",
        "zh": "给其他运行这个项目的人",
    },
    "for_others_body": {
        "en": "This checklist is also the setup guide for anyone who clones the repo "
        "-- see also the Quickstart section in README.md.",
        "zh": "这份 checklist 同时也是给任何 clone 这个仓库的人看的设置指南——也可以参考 "
        "README.md 里的 Quickstart 部分。",
    },
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
