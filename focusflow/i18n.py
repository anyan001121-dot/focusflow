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
    'input_label': {'en': "What's on your mind?", 'zh': '你想开始做什么？'},
    'input_placeholder': {'en': 'For example: I need to write my report, but I keep putting it off.', 'zh': '比如：想写论文，但一直没打开文档。'},
    'example_header': {'en': 'Not sure what to write? Try an example.', 'zh': '不知道写什么？可以从一个例子开始'},
    'example_study': {'en': 'Start writing my paper', 'zh': '开始写论文'},
    'example_work': {'en': 'Reply to an email I have been putting off', 'zh': '回复一封拖了很久的邮件'},
    'example_return': {'en': 'Continue preparing for my interview', 'zh': '接着准备面试'},
    'start_reassurance': {'en': 'One thing or several thoughts are both welcome. You can pause whenever you need.', 'zh': '写一件事，或把几件事一起放下，都可以。需要的时候，随时暂停。'},
    'next_step_label': {'en': 'YOUR NEXT SMALL STEP', 'zh': '接下来的一小步'},
    'show_timer': {'en': 'Show elapsed time', 'zh': '显示已用时间'},
    'product_promise': {'en': 'A place to start, and somewhere to return to.', 'zh': '给开始留一点空间，也给回来留一个位置。'},
    'later_review': {'en': 'Review parked thoughts', 'zh': '查看暂存的事情'},
    'later_start': {'en': 'Start this', 'zh': '开始这件事'},
    'later_resolved': {'en': 'Handled / not needed', 'zh': '已处理／不需要了'},
    'completion_condition': {'en': 'This step is done when: {condition}', 'zh': '这一步做到这里就可以：{condition}'},
    'pause_header': {'en': 'Leave a note for when you return (optional)', 'zh': '给回来时的自己留句话（可选）'},
    'pause_note': {'en': 'Optional: leave a clue for your return (file, page, next move)', 'zh': '可选：给回来时的自己留句话（文件、页码、下一动作）'},
    'pause_button': {'en': 'Pause here', 'zh': '先停在这里'},
    'pause_saved': {'en': "Your place is saved. Come back when you're ready.", 'zh': '已经记住你做到哪里了。准备好了，再回来。'},
    'return_button': {'en': 'Pick up from here', 'zh': '从这里接着做'},
    'return_note': {'en': 'Your return note: {note}', 'zh': '你留下的提示：{note}'},
    "disclaimer": {
        "en": "A friendly executive-function helper -- not a medical device, "
        "and it doesn't diagnose or treat ADHD.",
        "zh": "一个友善的执行功能小助手——不是医疗设备，不诊断也不治疗 ADHD。",
    },
    'llm_backend_label': {'en': 'Suggestions: {provider}', 'zh': '建议来源：{provider}'},
    "provider_anthropic": {"en": "Anthropic", "zh": "Anthropic"},
    "provider_openai": {"en": "OpenAI", "zh": "OpenAI"},
    'provider_mock': {'en': 'Practice mode · template suggestions', 'zh': '练习模式 · 模板建议'},
    "language_label": {"en": "🌐 Language", "zh": "🌐 语言"},
    'later_list_header': {'en': 'Set aside for later ({n})', 'zh': '先放在这里（{n}）'},
    'later_list_empty': {'en': 'If another thought comes up, you can leave it here.', 'zh': '想到别的事时，可以先放在这里。'},
    'resume_button': {'en': 'Where was I? Continue', 'zh': '我刚才做到哪里了？继续'},
    "privacy_header": {"en": "🔒 Privacy", "zh": "🔒 隐私"},
    'privacy_caption': {'en': 'State and history are stored on the computer/server running this app. With an AI provider connected, task text is sent to that provider. A public demo is not a durable personal workspace.', 'zh': '状态与历史保存在运行应用的电脑或服务器上。接入 AI 服务后，任务文本会发送给该服务商。公开演示不适合长期保存个人任务。'},
    "delete_button": {
        "en": "🗑️ Delete all my data",
        "zh": "🗑️ 删除我的所有数据",
    },
    'resume_welcome': {'en': 'Welcome back! Your next step is right here. 🌱', 'zh': '欢迎回来啦 🌱 刚才的那一步还在。'},
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
    'brain_dump_header': {'en': 'A few things to choose from.', 'zh': '先挑一件就好。'},
    "brain_dump_empty": {
        "en": "Hmm, couldn't spot a clear task in there -- try naming one thing directly.",
        "zh": "嗯……没找到明确的任务，试着直接说一件具体的事吧。",
    },
    "urgency_label": {
        "en": "urgency: {urgency}",
        "zh": "紧急程度：{urgency}",
    },
    'start_button': {'en': 'Start ✨', 'zh': '开始吧 ✨'},
    "later_parked": {
        "en": "Tucked {n} lower-priority thing(s) into the Later list 📥",
        "zh": "已经把 {n} 件优先级较低的事情放进稍后列表啦 📥",
    },
    "ideas_header": {
        "en": "💭 Ideas / not urgent right now ({n})",
        "zh": "💭 想法 / 暂时不用做（{n}）",
    },
    'focus_header': {'en': 'Just this step, for now.', 'zh': '眼前，只需要这一步。'},
    'focus_goal': {'en': "You're working on: **{goal}**", 'zh': '你正在做：**{goal}**'},
    "focus_start_here": {
        "en": "👉 **Start here:** {step}",
        "zh": "👉 **从这里开始：** {step}",
    },
    'focus_estimated': {'en': 'About {minutes} min · a guide, not a deadline', 'zh': '大约 {minutes} 分钟 · 只是参考，不是倒计时'},
    'interruption_captured': {'en': 'Saved for later. Your current step is still here.', 'zh': '已经记下来了。正在做的这一步还在这里。'},
    "interruption_related": {
        "en": "Got it -- sounds related to what you're already doing 👍",
        "zh": "知道啦——看起来和你正在做的事情有关 👍",
    },
    'policy_kept_on_track': {'en': 'Your current step is saved. Use Pause if you need to handle something urgent.', 'zh': '当前步骤已保留。如果需要处理急事，可以使用暂停。'},
    "llm_fallback_notice": {
        "en": "⚠️ The connected LLM had a hiccup just now, so this suggestion came from practice mode instead.",
        "zh": "⚠️ 刚才连接的 LLM 出了点小状况，这条建议是练习模式给出的。",
    },
    "llm_fallback_rate_limit": {
        "en": "⏳ Hit a rate limit just now, so this suggestion came from practice mode instead. Should clear up on its own shortly.",
        "zh": "⏳ 刚才触发了限流，这条建议是练习模式给出的。一般过一会儿就恢复了。",
    },
    "llm_fallback_auth": {
        "en": "❌ Your API key looks invalid or expired, so this suggestion came from practice mode instead. Check the **Setup** page in the sidebar.",
        "zh": "❌ 你的 API key 好像失效了或者不对，这条建议是练习模式给出的。去侧边栏的 **Setup** 页面看看。",
    },
    'completed_header': {'en': "Steps you've taken ({n})", 'zh': '已经走过的小步骤（{n}）'},
    'done_button': {'en': '✅ Done with this step!', 'zh': '✅ 这一步搞定啦！'},
    'split_button': {'en': 'This feels too big. Make it smaller.', 'zh': '这一步还有点难，再小一点'},
    "step_split_notice": {
        "en": "Broke that into something smaller for you 🧩",
        "zh": "已经帮你拆成更小的一步啦 🧩",
    },
    'timer_elapsed': {'en': 'Time since starting: {mmss}', 'zh': '开始后经过：{mmss}'},
    'timer_over_estimate': {'en': 'Past the ~{minutes} min estimate. The estimate is only a guide; take a break or split the step if helpful.', 'zh': '已超过约 {minutes} 分钟的预估。预估仅供参考；可以暂停，也可以再拆小一点。'},
    'cognitive_load_prompt': {'en': "If you'd like: how did those steps feel?", 'zh': '如果愿意，可以告诉我：刚才这几步做起来怎么样？'},
    'cognitive_load_easy': {'en': 'Manageable', 'zh': '做得动'},
    'cognitive_load_okay': {'en': 'Some effort', 'zh': '有点费力'},
    'cognitive_load_hard': {'en': 'Too much', 'zh': '还是太难'},
    'cognitive_load_thanks': {'en': 'Noted. Thank you for telling me.', 'zh': '记下了，谢谢你告诉我。'},
    'aside_label': {'en': 'Something else on your mind?', 'zh': '又想起了别的事？'},
    'aside_placeholder': {'en': "Leave a few words here so you don't have to hold onto them.", 'zh': '写下来，就不用一直惦记着。'},
    'send_button': {'en': 'Save for later', 'zh': '先记下来'},
    'task_complete_message': {'en': "You finished this set of {steps} steps for '{task}'. This may be one part of the larger task.", 'zh': '你完成了「{task}」这一轮的 {steps} 个小步骤。较大的任务可能还需要继续。'},
    'whats_on_mind_header': {'en': "Let's make room for one thing.", 'zh': '现在，先照顾眼前这一件事。'},
    'whats_on_mind_caption': {'en': "You may know what needs doing and still find it hard to begin. Write a few words. They don't need to be organized.", 'zh': '知道要做什么，也可能还是开始不了。先写几个字就好，不用想清楚，也不用整理好。'},
    'go_button': {'en': "Let's go ✨", 'zh': '出发咯 🌈'},
    "analytics_title": {"en": "📊 Analytics", "zh": "📊 分析看板"},
    'analytics_caption': {'en': 'Local usage records, not proof of real-world task completion. Time includes unpaused time away; uncompleted sets may still be in progress.', 'zh': '这些是使用记录，不代表现实任务已经完成。用时包含未暂停的离开时间；未完成的轮次也可能仍在进行。'},
    'metric_north_star': {'en': 'Completed step sets (7d)', 'zh': '近 7 天完成的小步骤轮次'},
    'metric_completion_rate': {'en': 'Completed sets / generated sets', 'zh': '完成轮次／生成轮次'},
    'metric_abandonment_rate': {'en': 'Sets not recorded complete', 'zh': '未记录完成的轮次占比'},
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
    'setup_title': {'en': 'Connect an AI provider', 'zh': '接入 AI 建议'},
    'setup_intro': {'en': 'Practice mode lets you try the flow without an API key. Its suggestions use templates and may not fit your task. To get suggestions from an AI provider, configure a key below.', 'zh': '不用 API key 也可以先体验流程。练习模式使用模板，建议可能不贴合你的任务。需要模型生成建议时，再按下面的说明接入。'},
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

