"""UI string tables for the Streamlit front end.

Agent-generated content (task text, breakdown steps, etc.) is localized at
the LLM/mock layer -- see prompts.py and mock_llm.py. This module only
covers static interface chrome (labels, buttons, captions) so the whole
page reads consistently in the user's chosen language.

Tone: warm and a little playful (emoji, soft phrasing), but never at the
cost of clarity -- an ADHD-friendly interface needs to be readable in one
glance more than it needs to be clever. The disclaimer and privacy copy
stay plain and unambiguous on purpose; PRD section 7 also rules out
guilt/shame/hype, so "cute" here means warmth, not pep-talk energy.

Usage: `from focusflow.i18n import t; t(lang, "start_button")`
"""

from __future__ import annotations

LANGUAGES = {"en": "English", "zh": "中文"}

_STRINGS: dict[str, dict[str, str]] = {
    "disclaimer": {
        "en": "A friendly executive-function helper -- not a medical device, "
        "and it doesn't diagnose or treat ADHD.",
        "zh": "一个友善的执行功能小助手——不是医疗设备，不诊断也不治疗 ADHD。",
    },
    "llm_backend_label": {
        "en": "LLM backend: {provider}",
        "zh": "LLM 后端：{provider}",
    },
    "provider_anthropic": {"en": "Anthropic", "zh": "Anthropic"},
    "provider_openai": {"en": "OpenAI", "zh": "OpenAI"},
    "provider_mock": {
        "en": "🧪 Practice mode (no API key yet)",
        "zh": "🧪 练习模式（还没接入 key）",
    },
    "language_label": {"en": "🌐 Language", "zh": "🌐 语言"},
    "later_list_header": {
        "en": "🗂️ Later list ({n})",
        "zh": "🗂️ 稍后列表（{n}）",
    },
    "later_list_empty": {
        "en": "Nothing parked here yet -- nice and clear! ✨",
        "zh": "这里空空的，很棒！✨",
    },
    "resume_button": {
        "en": "Where was I? (Resume) 🔍",
        "zh": "我刚才在做什么？（继续）🔍",
    },
    "privacy_header": {"en": "🔒 Privacy", "zh": "🔒 隐私"},
    "privacy_caption": {
        "en": "All your data stays right here on your computer, in focusflow.db.",
        "zh": "你的数据都好好地留在本地的 focusflow.db 文件里。",
    },
    "delete_button": {
        "en": "🗑️ Delete all my data",
        "zh": "🗑️ 删除我的所有数据",
    },
    "resume_welcome": {"en": "**Hey, welcome back!** 👋", "zh": "**嘿，欢迎回来啦！** 👋"},
    "resume_you_were": {
        "en": "You were working on: **{task}**",
        "zh": "你刚才在忙：**{task}**",
    },
    "resume_completed_header": {"en": "Already done ✅:", "zh": "已经搞定 ✅："},
    "resume_next_action": {
        "en": "**Next up:** {action}",
        "zh": "**接下来：** {action}",
    },
    "resume_estimated": {
        "en": "Should take about {minutes} min 🕒",
        "zh": "大概需要 {minutes} 分钟 🕒",
    },
    "resume_nothing": {
        "en": "Nothing to pick back up yet -- tell me what's on your mind below! 🌱",
        "zh": "还没有可以继续的任务——先在下面写下你在想什么吧！🌱",
    },
    "clarify_message": {
        "en": "What's on your mind? 🌱 Dump a few things at once, or just name one "
        "thing you want to start.",
        "zh": "你在想什么呀？🌱 可以一口气把几件事都写出来，也可以直接说一件你想开始做的事。",
    },
    "brain_dump_header": {"en": "Here's the tidy version ✨", "zh": "整理好啦 ✨"},
    "brain_dump_empty": {
        "en": "Hmm, couldn't spot a clear task in there -- try naming one thing directly.",
        "zh": "嗯……没找到明确的任务，试着直接说一件具体的事吧。",
    },
    "urgency_label": {
        "en": "urgency: {urgency}",
        "zh": "紧急程度：{urgency}",
    },
    "start_button": {"en": "Start ✨", "zh": "开始吧 ✨"},
    "later_parked": {
        "en": "Tucked {n} lower-priority thing(s) into the Later list 📥",
        "zh": "已经把 {n} 件优先级较低的事情放进稍后列表啦 📥",
    },
    "ideas_header": {
        "en": "💭 Ideas / not urgent right now ({n})",
        "zh": "💭 想法 / 暂时不用做（{n}）",
    },
    "focus_header": {"en": "🌟 Focus time", "zh": "🌟 专注时间"},
    "focus_goal": {"en": "🎯 **Goal:** {goal}", "zh": "🎯 **目标：** {goal}"},
    "focus_start_here": {
        "en": "👉 **Start here:** {step}",
        "zh": "👉 **从这里开始：** {step}",
    },
    "focus_estimated": {"en": "~{minutes} min", "zh": "约 {minutes} 分钟"},
    "interruption_captured": {
        "en": "Tucked away for later 📥 Back to what you're doing above.",
        "zh": "已经收进稍后列表啦 📥 回到上面继续吧。",
    },
    "interruption_related": {
        "en": "Got it -- sounds related to what you're already doing 👍",
        "zh": "知道啦——看起来和你正在做的事情有关 👍",
    },
    "policy_kept_on_track": {
        "en": "🛡️ The agent actually wanted to switch tasks -- a hard rule kept you on '{task}' instead.",
        "zh": "🛡️ Agent 本来想切换任务——但被一条硬规则拦下来了，继续留在「{task}」上。",
    },
    "llm_fallback_notice": {
        "en": "⚠️ The connected LLM had a hiccup just now, so this suggestion came from practice mode instead.",
        "zh": "⚠️ 刚才连接的 LLM 出了点小状况，这条建议是练习模式给出的。",
    },
    "completed_header": {"en": "✅ Done so far ({n})", "zh": "✅ 已经完成（{n}）"},
    "done_button": {"en": "✅ Done with this step!", "zh": "✅ 这一步搞定啦！"},
    "split_button": {
        "en": "Still too big? Let's split it 🧩",
        "zh": "还是有点大，再拆小一点吧 🧩",
    },
    "step_split_notice": {
        "en": "Broke that into something smaller for you 🧩",
        "zh": "已经帮你拆成更小的一步啦 🧩",
    },
    "timer_elapsed": {"en": "⏱️ Elapsed: {mmss}", "zh": "⏱️ 已用时：{mmss}"},
    "timer_over_estimate": {
        "en": "🌤️ Past the ~{minutes} min estimate -- totally normal, keep going "
        "or mark done whenever.",
        "zh": "🌤️ 已经超过约 {minutes} 分钟的预估——很正常，继续做，或者觉得可以了就点完成。",
    },
    "cognitive_load_prompt": {
        "en": "How did that feel? 💭",
        "zh": "刚才感觉怎么样？💭",
    },
    "cognitive_load_easy": {"en": "😌 Easy", "zh": "😌 轻松"},
    "cognitive_load_okay": {"en": "😐 Okay", "zh": "😐 还好"},
    "cognitive_load_hard": {"en": "😣 Hard", "zh": "😣 费劲"},
    "cognitive_load_thanks": {
        "en": "Got it, thanks for sharing! 💛",
        "zh": "记下啦，谢谢你告诉我！💛",
    },
    "aside_label": {
        "en": "Anything else popping into your head? 💭",
        "zh": "现在脑子里还蹦出别的事情吗？💭",
    },
    "aside_placeholder": {
        "en": "e.g. I just remembered I need to buy detergent",
        "zh": "比如：我突然想起要买洗衣液",
    },
    "send_button": {"en": "Send 💌", "zh": "发送 💌"},
    "task_complete_message": {
        "en": "Yay! You finished '{task}' in {steps} step(s) 🎉",
        "zh": "太棒啦！完成了「{task}」，一共 {steps} 步 🎉",
    },
    "whats_on_mind_header": {"en": "What's on your mind? 🌱", "zh": "你在想什么呀？🌱"},
    "whats_on_mind_caption": {
        "en": "Dump it all out messily, or just name one thing you want to start right now.",
        "zh": "把想到的事情随便写出来，或者直接说一件你现在想开始的事。",
    },
    "go_button": {"en": "Let's go ✨", "zh": "出发咯 🌈"},
    "analytics_title": {"en": "📊 Analytics", "zh": "📊 分析看板"},
    "analytics_caption": {
        "en": "A cozy little peek at your own local usage -- not a diagnostic tool.",
        "zh": "一个温馨的本地小看板，看看自己的使用情况——不是诊断工具。",
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
        "en": "Not much data yet -- go use the app a little, then come back! 🌱",
        "zh": "数据还不多——先去用一下 app，再回来看看吧！🌱",
    },
    "setup_title": {
        "en": "⚙️ Let's connect a real LLM ✨",
        "zh": "⚙️ 一起接入真实 LLM 吧 ✨",
    },
    "setup_intro": {
        "en": "FocusFlow comes with a cozy little \"practice mode\" built in "
        "(see focusflow/mock_llm.py) so there's something to try right away. "
        "For the real task-breakdown magic, connect an Anthropic or OpenAI API key.",
        "zh": "FocusFlow 自带一个可爱的\"练习模式\"（见 focusflow/mock_llm.py），"
        "让你马上就能试用。想要真正聪明的任务拆解，需要接入 Anthropic 或 OpenAI 的 API key。",
    },
    "setup_order_note": {
        "en": "Tick these off in whatever order feels right -- none of them depend on each other. 🌈",
        "zh": "按你喜欢的顺序打勾就好——它们互相都不依赖。🌈",
    },
    "setup_status_connected": {
        "en": "🎉 Connected: {provider}!",
        "zh": "🎉 已经连接：{provider}！",
    },
    "setup_status_mock": {
        "en": "Not connected yet -- you're currently in practice mode. 🧪",
        "zh": "还没连接——现在是练习模式哦。🧪",
    },
    "step_get_key": {
        "en": "🔑 Get an API key from Anthropic or OpenAI",
        "zh": "🔑 去 Anthropic 或 OpenAI 申请一个 API key",
    },
    "step_copy_env": {
        "en": "📄 In the project folder, copy `.env.example` to a new file named `.env`",
        "zh": "📄 在项目目录里，把 `.env.example` 复制一份，命名为 `.env`",
    },
    "step_paste_key": {
        "en": "✍️ Open `.env` and paste your key after `ANTHROPIC_API_KEY=` or `OPENAI_API_KEY=`",
        "zh": "✍️ 打开 `.env`，把你的 key 粘贴到 `ANTHROPIC_API_KEY=` 或 `OPENAI_API_KEY=` 后面",
    },
    "step_restart": {
        "en": "🔄 Restart the app (stop it, then run `streamlit run app.py` again)",
        "zh": "🔄 重启应用（停掉后重新运行 `streamlit run app.py`）",
    },
    "step_verify": {
        "en": "👀 Come back to this page and check the status above",
        "zh": "👀 回到这个页面，看看上面的状态",
    },
    "for_others_header": {
        "en": "💌 For other people running this project",
        "zh": "💌 给其他运行这个项目的人",
    },
    "for_others_body": {
        "en": "This checklist is also the setup guide for anyone who clones the repo "
        "-- see also the Quickstart section in README.md.",
        "zh": "这份 checklist 同时也是给任何 clone 这个仓库的人看的设置指南——也可以参考 "
        "README.md 里的 Quickstart 部分。",
    },
}

_URGENCY_LABELS = {
    "high": {"en": "🔴 high", "zh": "🔴 高"},
    "medium": {"en": "🟡 medium", "zh": "🟡 中"},
    "low": {"en": "🟢 low", "zh": "🟢 低"},
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
