# FocusFlow

**[English](#english)** · **[中文](#中文)**

---

## English

An AI executive-function assistant for people with ADHD or attention/task-management
difficulties. **FocusFlow does not diagnose or treat ADHD.** It exists to close the
gap between *"I know what I need to do"* and *"I can actually start and continue
doing it."*

Design principle: **do not maximize information — minimize the cognitive effort
required to take the next useful action.**

### What it does

- **Brain Dump** — turn messy, unstructured thoughts into at most three clear
  priorities, without dumping a huge list back at you.
- **Task Breakdown** — turn a vague goal ("prepare for an interview") into one
  concrete first step you can start in a few minutes.
- **Focus Mode** — while you're working, a new thought ("I need to buy detergent")
  is captured to a Later list instead of derailing your current task.
- **Resume** — after an interruption, see only what you were doing, what's done,
  and what's next — not the whole project again.
- **Bilingual** — the whole UI, plus the agent's own responses, switch between
  English and 中文 from a sidebar selector.
- **Focus Timer & step splitting** — a live elapsed-time readout during Focus
  Mode, and a "still too big" action that re-breaks the current step into
  something smaller without losing progress.
- **Personalization** — FocusFlow learns your actual-vs-estimated time ratio
  and how often you split steps further, then uses that to size future
  breakdowns (see `focusflow/service.py`).
- **Analytics** — a local dashboard (`pages/1_Analytics.py`) over the metrics
  in the Evaluation section below.
- **A warm, cozy look** — a soft cream/coral theme (`.streamlit/config.toml`)
  and gently playful copy throughout, without tipping into hype or guilt-trip
  language (see the Agent behaviour rules below).

### Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional, see below
streamlit run app.py
```

FocusFlow works with **no API key**: it falls back to a small heuristic "mock"
LLM (`focusflow/mock_llm.py`) so you can try the whole flow immediately. Add
`ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to `.env` for real task extraction and
breakdown quality (see `focusflow/llm.py`).

### Connecting a real LLM

The steps below are independent of each other -- check them off in any
order once you've done them, there's no required sequence:

- [ ] Get an API key: [Anthropic console](https://console.anthropic.com/settings/keys)
      or [OpenAI console](https://platform.openai.com/api-keys).
- [ ] Copy `.env.example` to a new file named `.env` in the project root.
- [ ] Open `.env` and paste your key after `ANTHROPIC_API_KEY=` or
      `OPENAI_API_KEY=` (fill in only one; if both are set, Anthropic is used).
- [ ] Restart the app: stop it and run `streamlit run app.py` again.
- [ ] Open the app and check the sidebar's "LLM backend" line, or the
      **Setup** page in the sidebar nav, which shows a live "connected" status.

This same checklist is built into the app itself as a Setup page
(`pages/0_Setup.py`) with real, persistent checkboxes -- useful for anyone
who clones this repo and wants a guided first run.

### Architecture

```
User Input
    |
Intent Router
    |
    +---------------+---------------+----------------+
    |               |               |                |
Brain Dump       New Task        Resume         Interruption
    |               |               |                |
Organize        Breakdown      Load State        Capture
    |               |               |                |
Prioritize     Next Action     Resume Point      Later List
    +---------------+---------------+----------------+
                     |
                Focus Mode
                     |
                Task State (SQLite)
                     |
               User Progress
```

Implemented with [LangGraph](https://github.com/langchain-ai/langgraph) as a
small, controlled state machine (`focusflow/graph.py`) — not an open-ended
multi-agent system. State persists locally in SQLite (`focusflow/db.py`).

| Layer | File |
|---|---|
| Shared state schema | `focusflow/state.py` |
| Router + nodes (LangGraph) | `focusflow/graph.py` |
| DB + graph orchestration | `focusflow/service.py` |
| LLM provider wrapper | `focusflow/llm.py`, `focusflow/mock_llm.py` |
| Prompts | `focusflow/prompts.py` |
| Persistence | `focusflow/db.py` |
| UI strings (EN/中文) | `focusflow/i18n.py` |
| UI | `app.py` (Streamlit) |
| Setup checklist | `pages/0_Setup.py` |
| Analytics dashboard | `pages/1_Analytics.py` |

### Agent behaviour rules

1. Never overwhelm the user with unnecessary information; show at most three
   immediate priorities by default.
2. Always identify one primary next action.
3. Convert vague goals into observable, concrete actions.
4. Prefer a first step startable within ~2-5 minutes.
5. During Focus Mode, don't abandon the active task just because the user
   mentions something else — capture it to the Later list instead.
6. Preserve task state across interruptions; minimize what the user has to
   reconstruct on resume.
7. No guilt, shame, or excessive motivational language. No medical claims.

### Roadmap

- **V0.1** (done): Brain Dump -> Task Extraction -> Breakdown -> Prioritization ->
  One Next Action.
- **V0.2** (done): LangGraph workflow, Focus Mode, interruption capture, Later
  list, Resume, SQLite persistence.
- **V0.3** (partial):
  - done: a Focus Timer (elapsed time shown live during Focus Mode), a "still
    too big -- split it" action that re-breaks down the current step without
    losing progress, long-term preference memory (actual-vs-estimated time
    ratio + breakdown acceptance rate, stored in SQLite), adaptive task
    sizing that feeds those preferences back into future breakdowns, and an
    Analytics page (`pages/1_Analytics.py`) over the metrics below.
  - not done: calendar integration.

### Evaluation

Product quality should be judged on usage outcomes, not on whether responses
"sound good." FocusFlow logs each turn to a local `events` table
(`focusflow/db.py`) to eventually support:

- Task Start Rate, Time-to-Start, Task Completion Rate
- Breakdown Acceptance Rate, Resume Success Rate, Abandonment Rate
- Cognitive Load (self-reported)
- North Star: **Successful Task Starts per User per Week**

### Privacy & safety

- Not a medical device: no ADHD diagnosis, no medication advice, no
  replacement for professional care.
- All data is stored locally in a single SQLite file (`focusflow.db` by
  default, gitignored).
- Use the "Delete all my data" button in the app (or `service.reset_all()`)
  to wipe stored state and event history at any time.

### Tests

```bash
pytest
```

Graph tests run entirely against the mock LLM backend, so no API key is
needed to verify the core control flow (brain dump prioritization,
interruption handling, resume, task completion).

---

## 中文

一个面向 ADHD / 执行功能困难人群的 AI 执行功能助手。**FocusFlow 不诊断、也不治疗 ADHD**，它的目标是缩小
「我知道要做什么」和「我真的能开始并持续做下去」之间的差距。

设计原则：**不追求信息最大化，而是把"采取下一步有用行动"所需的认知负担降到最低。**

### 它能做什么

- **Brain Dump（一键倾倒）**——把杂乱无章的想法整理成最多三个清晰的优先事项，而不是甩给你一份更长的清单。
- **任务拆解**——把模糊的目标（"准备一场面试"）拆成一个几分钟内就能开始的具体第一步。
- **专注模式（Focus Mode）**——工作过程中突然想到别的事（"我要买洗衣液"），会被记进稍后列表，而不会打断你正在做的事。
- **恢复（Resume）**——被打断后，只看到你在做什么、完成了什么、下一步是什么——不用重新翻一遍整个项目。
- **中英双语**——整个界面以及 Agent 的回复内容，都可以在侧边栏里切换中文 / English。
- **专注计时器 + 步骤再拆分**——专注模式里实时显示已用时间，"还是太大了"按钮可以在不丢失进度的前提下把当前步骤再拆小。
- **个性化**——FocusFlow 会记录你的实际用时/预估用时比例，以及你把步骤再拆分的频率，用这些数据调整以后拆解任务的粒度（见 `focusflow/service.py`）。
- **分析看板**——本地的数据看板（`pages/1_Analytics.py`），对应下方"评估指标"里的各项数字。
- **温馨可爱的视觉风格**——奶油色 + 珊瑚色的暖色主题（`.streamlit/config.toml`），
  文案也带一点俏皮感，但不会变成打鸡血或制造愧疚感的语言（见下方"Agent 行为原则"）。

### 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 可选，见下文
streamlit run app.py
```

FocusFlow **不需要任何 API key** 就能跑：没有配置时会自动回退到一个小型启发式 "mock" LLM
（`focusflow/mock_llm.py`），让你可以立刻体验完整流程。想要更好的任务提取/拆解质量，
可以在 `.env` 里填入 `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY`（见 `focusflow/llm.py`）。

### 接入真实 LLM

下面这些步骤彼此独立，做完了随时打勾，不需要按顺序：

- [ ] 申请一个 API key：[Anthropic 控制台](https://console.anthropic.com/settings/keys)
      或 [OpenAI 控制台](https://platform.openai.com/api-keys)。
- [ ] 把项目根目录的 `.env.example` 复制一份，命名为 `.env`。
- [ ] 打开 `.env`，把你的 key 粘贴到 `ANTHROPIC_API_KEY=` 或 `OPENAI_API_KEY=` 后面
      （填一个就行；如果两个都填了，优先用 Anthropic）。
- [ ] 重启应用：停掉后重新运行 `streamlit run app.py`。
- [ ] 打开应用，看侧边栏的 "LLM backend" 那一行，或者侧边栏导航里的 **Setup** 页面，
      上面会实时显示是否已经连接成功。

这份 checklist 同时也内置在应用里，作为一个 Setup 页面（`pages/0_Setup.py`），
勾选状态会真实保存下来——对任何 clone 这个仓库、想要有引导地跑起来的人都有用。

### 架构

```
用户输入
    |
意图路由 Intent Router
    |
    +---------------+---------------+----------------+
    |               |               |                |
Brain Dump       新任务          Resume           打断
    |               |               |                |
整理            拆解           加载状态          捕获
    |               |               |                |
排优先级        下一步动作       恢复要点          稍后列表
    +---------------+---------------+----------------+
                     |
                专注模式 Focus Mode
                     |
                任务状态（SQLite）
                     |
               用户进度
```

用 [LangGraph](https://github.com/langchain-ai/langgraph) 实现为一个小而受控的状态机
（`focusflow/graph.py`）——而不是一个漫无边际的多智能体系统。状态本地持久化在 SQLite
（`focusflow/db.py`）中。

| 层 | 文件 |
|---|---|
| 共享状态结构 | `focusflow/state.py` |
| 路由 + 节点（LangGraph） | `focusflow/graph.py` |
| 数据库 + 图编排 | `focusflow/service.py` |
| LLM provider 封装 | `focusflow/llm.py`, `focusflow/mock_llm.py` |
| 提示词 | `focusflow/prompts.py` |
| 持久化 | `focusflow/db.py` |
| 界面文案（中/英） | `focusflow/i18n.py` |
| 界面 | `app.py`（Streamlit） |
| 设置 checklist | `pages/0_Setup.py` |
| 分析看板 | `pages/1_Analytics.py` |

### Agent 行为原则

1. 绝不用不必要的信息淹没用户；默认最多展示三个当前优先事项。
2. 始终指出一个明确的首要下一步动作。
3. 把模糊的目标转化为可观察、具体的动作。
4. 优先选择约 2-5 分钟内就能开始的第一步。
5. 专注模式期间，不会因为用户提到别的事就放弃当前任务——而是记进稍后列表。
6. 在打断之间保留任务状态；让用户在恢复时需要重建的上下文最少。
7. 不使用愧疚、羞耻或过度的激励式语言，不做任何医疗相关的宣称。

### 路线图

- **V0.1**（已完成）：Brain Dump → 任务提取 → 拆解 → 排优先级 → 一个下一步动作。
- **V0.2**（已完成）：LangGraph 工作流、专注模式、打断捕获、稍后列表、恢复、SQLite 持久化。
- **V0.3**（部分完成）：
  - 已完成：专注计时器（专注模式中实时显示已用时间）、"还是太大了——再拆一下"
    （在不丢失进度的情况下重新拆解当前步骤）、长期偏好记忆（实际/预估用时比例、
    拆解接受率，存在 SQLite 中）、把这些偏好反馈进未来拆解粒度的自适应任务拆分、
    以及基于下方指标的分析看板（`pages/1_Analytics.py`）。
  - 未完成：日历集成。

### 评估指标

产品质量应该基于实际使用效果来判断，而不是"回复听起来好不好"。FocusFlow 会把每一轮交互
记录到本地的 `events` 表（`focusflow/db.py`），为将来支持以下指标做准备：

- 任务启动率（Task Start Rate）、启动耗时（Time-to-Start）、任务完成率（Task Completion Rate）
- 拆解采纳率（Breakdown Acceptance Rate）、恢复成功率（Resume Success Rate）、放弃率（Abandonment Rate）
- 认知负荷（用户自评）
- 北极星指标：**每位用户每周成功启动任务的次数（Successful Task Starts per User per Week）**

### 隐私与安全

- 不是医疗设备：不做 ADHD 诊断、不提供用药建议、不能替代专业医疗意见。
- 所有数据都保存在本地单个 SQLite 文件中（默认 `focusflow.db`，已加入 `.gitignore`）。
- 随时可以点击应用内的"删除我的所有数据"按钮（或调用 `service.reset_all()`）
  清空已存储的状态和事件历史。

### 测试

```bash
pytest
```

图（graph）测试完全基于 mock LLM 后端运行，因此不需要任何 API key 就能验证核心控制流程
（brain dump 优先级排序、打断处理、恢复、任务完成）。
