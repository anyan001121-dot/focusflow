<p align="center">
  <img src="assets/logo.svg" width="96" alt="FocusFlow mascot" />
</p>
<h1 align="center">FocusFlow</h1>
<p align="center"><em>An AI executive-function assistant for ADHD-style task-initiation friction — a small, deliberately non-autonomous LangGraph workflow, not a chatbot with a to-do list bolted on.</em></p>

<p align="center">
  <a href="https://github.com/anyan001121-dot/focusflow/actions/workflows/tests.yml"><img src="https://github.com/anyan001121-dot/focusflow/actions/workflows/tests.yml/badge.svg" alt="tests"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="python 3.11+">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="MIT license"></a>
</p>

<p align="center">
  <a href="https://focusflow-j2gkquxeg2cifcxmyqxw8w.streamlit.app/"><strong>Try it live → / 在线试用 →</strong></a>　(practice mode, no signup — see <a href="#connecting-a-real-llm">Connecting a real LLM</a> / <a href="#接入真实-llm">接入真实 LLM</a>)
</p>

<p align="center"><strong><a href="#english">English</a> · <a href="#中文">中文</a></strong></p>

---

## English

### tl;dr

- FocusFlow closes the gap between *"I know what I need to do"* and *"I can actually start."* It is not a to-do app and not a medical device.
- Messy thoughts in → at most 3 priorities out. A vague goal in → one concrete step you can start in 2-5 minutes. Get distracted mid-task → the new thought is parked, not adopted, and you're handed straight back to what you were doing.
- Try it in under a minute, no API key required:
  ```bash
  pip install -r requirements.txt && streamlit run app.py
  ```

<img src="docs/screenshots/01_brain_dump_empty.png" width="720" alt="FocusFlow landing screen with an empty brain-dump box">

### The problem

Most task-initiation friction isn't a planning problem, it's a *first-step* problem. Someone with ADHD (or just an overloaded week) usually knows the shape of what needs doing — the blocker is that "prepare for an interview" doesn't have an obvious verb attached to it, and a wall of unsorted thoughts is itself exhausting to look at.

Generic to-do apps make this worse: they reward capturing more, not starting sooner. FocusFlow is built around one constraint instead: **don't maximize information — minimize the cognitive effort required to take the next useful action.** Concretely, it targets four failure modes:

| Failure mode | What FocusFlow does about it |
|---|---|
| Cognitive overload from unsorted thoughts | Brain Dump caps output at 3 priorities, parks the rest |
| Abstract goals never get started | Breakdown always returns one 2-5 min first step, never a plan |
| A new thought derails the current task | Focus Mode parks it in a Later list instead of switching tasks |
| Coming back after an interruption is disorienting | Resume shows only done / current / next — not the whole project |

### What it does

**Brain Dump** — dump everything messily; get back at most three clear priorities, with the rest quietly parked.

<img src="docs/screenshots/02_brain_dump_result.png" width="720" alt="Brain Dump screen showing three prioritized cards with a Start button on each">

**Focus Mode** — one goal, one step, a live elapsed-time readout, and a "still too big" escape hatch that re-breaks the current step instead of giving up on it.

<img src="docs/screenshots/03_focus_mode.png" width="720" alt="Focus Mode screen showing the current goal, the first step, and a timer">

**Interruption capture** — a new thought mid-task gets filed to Later without touching the active step.

<img src="docs/screenshots/04_interruption_captured.png" width="720" alt="Focus Mode screen after an interruption was captured to the Later list">

**Resume** — coming back shows only what's done, what's current, and what's next.

<img src="docs/screenshots/05_resume.png" width="720" alt="Resume screen showing completed steps and the next action">

### Design decisions

Written for whoever's reviewing this as a work sample, not just a user:

**1. Interruption handling is a real agent, and its limits are hard-coded.** FocusFlow's top-level router (`focusflow/graph.py`) is plain code — brain dump, breakdown, and resume are fixed branches. Interruption handling works differently: the LLM looks at the current task and the new message and **proposes** one of three actions, and it's explicitly allowed to propose abandoning the current task if it thinks the new message is urgent enough (`focusflow/prompts.py`). Every proposal has to clear `focusflow/policy.py` first. While `focus_mode` is on, "abandon the active task" simply isn't in the set of allowed outcomes — the model can argue for it all it wants, the answer stays no. [`test_policy_blocks_agent_even_when_it_insists_on_switching_tasks`](tests/test_graph.py) forces the model to insist on switching and checks that the state doesn't budge. This is Anthropic's own [workflow vs. agent](https://www.anthropic.com/research/building-effective-agents) split in practice: the guarantee lives in code, and the model only gets to make calls that can't break it.

**2. The evaluation framework showed up before the LLM output did.** The spec was explicit: don't judge this by whether the responses sound good. So the events log (`focusflow/db.py`) and the personalization loop (`focusflow/service.py`) have been tracking *actual-vs-estimated time* and *breakdown-acceptance rate* since day one — see [Evaluation](#evaluation).

**3. It runs with zero setup.** A heuristic "mock" LLM (`focusflow/mock_llm.py`) covers the whole loop — brain dump, breakdown, interruption handling — with no API key, just at lower quality. Anyone who clones the repo sees real behavior in thirty seconds instead of after signing up for a key.

**4. Personalization needed two numbers, not a machine-learning pipeline.** The actual/estimated time ratio and the breakdown-rejection rate are enough signal to nudge future step sizing — no fine-tune, no recommender system. A heavier approach would need to earn its keep against the failure surface it adds, and here it wouldn't.

**5. It's single-user by default, and multi-tenant is one flag away.** Every SQLite row is keyed `"default"` unless `FOCUSFLOW_MULTI_SESSION=true` is set, in which case `focusflow/db.py` keys rows by a per-browser-session id instead. A public demo (strangers sharing one process) and a personal install (one person, state that has to survive restarts) want opposite things from the database, and the flag lets one codebase serve both without the local Resume experience paying for the demo's requirements.

**6. A failing LLM call degrades instead of crashing the page.** Real provider calls get a bounded timeout and the SDK's own retry/backoff (`focusflow/llm.py`). If a call still fails, or the model's output doesn't parse as JSON, FocusFlow logs a warning and falls back to the same heuristic output a missing API key would produce. The whole pitch here is staying calm and not overwhelming anyone — a stack trace after a rate limit would undercut that far more than a slightly duller suggestion would.

<details>
<summary><strong>Architecture</strong> (click to expand)</summary>

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

Implemented with [LangGraph](https://github.com/langchain-ai/langgraph) as a small, controlled state machine (`focusflow/graph.py`). State persists locally in SQLite (`focusflow/db.py`).

| Layer | File |
|---|---|
| Shared state schema | `focusflow/state.py` |
| Router + nodes (LangGraph) | `focusflow/graph.py` |
| Bounded-agency policy engine | `focusflow/policy.py` |
| DB + graph orchestration, personalization | `focusflow/service.py` |
| LLM provider wrapper | `focusflow/llm.py`, `focusflow/mock_llm.py` |
| Prompts | `focusflow/prompts.py` |
| Persistence (state, events, preferences) | `focusflow/db.py` |
| UI strings (EN/中文) | `focusflow/i18n.py` |
| Main UI | `app.py` (Streamlit) |
| Setup checklist | `pages/0_Setup.py` |
| Analytics dashboard | `pages/1_Analytics.py` |

</details>

<details>
<summary><strong>Tech stack</strong></summary>

Python · [Streamlit](https://streamlit.io) (UI) · [LangGraph](https://github.com/langchain-ai/langgraph) (orchestration) · SQLite (persistence) · Anthropic / OpenAI APIs, with a heuristic offline fallback · pytest + Streamlit `AppTest` (headless UI testing) · GitHub Actions (CI)

</details>

### More screens

<img src="docs/screenshots/06_setup.png" width="720" alt="Setup page: an order-independent checklist for connecting a real LLM API key">

Setup is a real, persistent, order-independent checklist (`pages/0_Setup.py`) — deliberately not a linear wizard, per the same "don't force a sequence" principle the product applies to tasks.

<img src="docs/screenshots/07_analytics.png" width="720" alt="Analytics dashboard showing completion rate, abandonment rate, and other metrics">

### Evaluation

Product quality here is judged on usage outcomes, not on whether responses "sound good" (PRD requirement, not an afterthought). Every turn is logged to a local `events` table; the Analytics page (`pages/1_Analytics.py`) surfaces:

- Task Start Rate, Time-to-Start, Task Completion Rate
- Breakdown Acceptance Rate, Resume Success Rate, Abandonment Rate
- Cognitive Load (self-reported, one tap after each completed task)
- North Star: **Successful Task Starts per User per Week**

### Roadmap

- **V0.1** (done): Brain Dump → Task Extraction → Breakdown → Prioritization → One Next Action.
- **V0.2** (done): LangGraph workflow, Focus Mode, interruption capture, Later list, Resume, SQLite persistence.
- **V0.3** (partial): done — Focus Timer, step-splitting, long-term preference memory, adaptive breakdown, Analytics dashboard. Not done — calendar integration.

### Tests

```bash
pip install -r requirements.txt
pytest
```

24 tests, three layers: pure graph-logic tests against the mock LLM (no API key needed), SQLite persistence tests, and headless Streamlit `AppTest` runs that click through the real UI (brain dump → start → split → done, language switch, privacy reset) to catch widget-wiring bugs that unit tests miss. CI runs the full suite on every push against Python 3.11 and 3.13 (see the badge above).

### Connecting a real LLM

FocusFlow works with **no API key** (heuristic mock backend). These steps are independent — do them in any order:

- [ ] Get an API key: [Anthropic console](https://console.anthropic.com/settings/keys) or [OpenAI console](https://platform.openai.com/api-keys).
- [ ] Copy `.env.example` to a new file named `.env` in the project root.
- [ ] Open `.env` and paste your key after `ANTHROPIC_API_KEY=` or `OPENAI_API_KEY=` (Anthropic is used if both are set).
- [ ] Restart the app: stop it and run `streamlit run app.py` again.
- [ ] Check the sidebar's "LLM backend" line, or the in-app **Setup** page, for a live connection status.

### Deploying your own copy

Deploying to something like [Streamlit Community Cloud](https://share.streamlit.io) works out of the box (point it at this repo, main file `app.py`). One setting matters if more than one person will use the same deployed instance at once:

```
FOCUSFLOW_MULTI_SESSION=true
```

Without it, every visitor to a shared deployment reads and writes the same local-profile row — fine for your own single-user instance, not fine for a public demo with concurrent strangers. See [Design decisions](#design-decisions) point 5.

### Privacy & safety

- Not a medical device: no ADHD diagnosis, no medication advice, no replacement for professional care.
- All data stays in one local SQLite file (`focusflow.db` by default, gitignored).
- "Delete all my data" in the app (or `service.reset_all()`) wipes stored state and event history at any time.

### License

[MIT](LICENSE)

---

## 中文

### 一句话版

- FocusFlow 想缩小"我知道要做什么"和"我真的能开始做"之间的差距。它不是待办事项应用，也不是医疗设备。
- 杂乱的想法丢进去 → 最多给你 3 个优先事项。模糊的目标丢进去 → 给你一个 2-5 分钟就能开始的具体动作。做到一半分心了 → 新想法被记下来，不会取代你正在做的事，随时能被原样接回去。
- 一分钟内跑起来，不需要任何 API key：
  ```bash
  pip install -r requirements.txt && streamlit run app.py
  ```

<img src="docs/screenshots/01_brain_dump_empty.png" width="720" alt="FocusFlow 首页，一个空的 brain dump 输入框">

### 要解决的问题

大部分"启动困难"其实不是规划问题，而是"第一步"问题。ADHD（或者只是这周太满）的人通常知道大概要做什么——卡住的地方是"准备面试"这四个字没有一个明确的动词，而一堆没整理的想法本身看着就很累。

普通的待办事项应用只会让这更糟：它们奖励"记录更多"，而不是"更快开始"。FocusFlow 的设计只围绕一个约束：**不追求信息最大化，而是把"采取下一步有用行动"所需的认知负担降到最低。** 具体针对四类失败场景：

| 失败场景 | FocusFlow 的应对 |
|---|---|
| 一堆没整理的想法带来认知过载 | Brain Dump 最多输出 3 个优先事项，其余悄悄放进稍后列表 |
| 抽象目标永远无法开始 | 拆解永远给一个 2-5 分钟的第一步，不给完整计划 |
| 新想法打断当前任务 | 专注模式把它记进稍后列表，而不是切换任务 |
| 打断后回来无所适从 | 恢复功能只展示"完成/当前/下一步"，不是整个项目 |

### 它能做什么

**Brain Dump**——随意倒出所有想法，拿回最多三个清晰的优先事项，其余安静地放进稍后列表。

<img src="docs/screenshots/02_brain_dump_result.png" width="720" alt="Brain Dump 界面，显示三张带优先级的卡片，每张卡片下面有开始按钮">

**专注模式**——一个目标、一个步骤、实时显示已用时间，"还是太大了"按钮可以重新拆解当前步骤而不是放弃它。

<img src="docs/screenshots/03_focus_mode.png" width="720" alt="专注模式界面，显示当前目标、第一步和计时器">

**打断捕获**——任务进行中冒出的新想法会被记进稍后列表，不会碰到正在进行的步骤。

<img src="docs/screenshots/04_interruption_captured.png" width="720" alt="专注模式界面，显示一次打断被记录进稍后列表之后的状态">

**恢复**——回来的时候只看到完成了什么、现在在做什么、下一步是什么。

<img src="docs/screenshots/05_resume.png" width="720" alt="恢复界面，显示已完成的步骤和下一步动作">

### 设计决策

这部分是写给"把这当作作品来评估的人"看的，不只是给用户看的：

**1. 打断处理是一个真正会拿主意的 Agent，边界写死在代码里。** FocusFlow 顶层的路由（`focusflow/graph.py`）就是普通代码——brain dump、拆解、恢复都是固定分支。打断处理不一样：LLM 会看当前任务和新消息，然后**提议**三个动作之一，而且它被明确允许提议放弃当前任务，只要它判断新消息够紧急（见 `focusflow/prompts.py`）。但每个提议都要先过 `focusflow/policy.py` 这一关。只要专注模式开着，"放弃当前任务"根本不在允许的结果范围内——模型怎么论证都没用，答案就是不行。[`test_policy_blocks_agent_even_when_it_insists_on_switching_tasks`](tests/test_graph.py) 这个测试专门强迫模型坚持要切换任务，然后检查状态有没有被动摇。这其实就是 Anthropic 自己提出的 [workflow vs. agent](https://www.anthropic.com/research/building-effective-agents) 区分在实际项目里的样子：保证写在代码里，模型只能在不会破坏这个保证的地方做判断。

**2. 评估框架在 LLM 输出之前就先搭好了。** 需求文档写得很直接：不要靠"回复听起来好不好"来评估。所以事件日志（`focusflow/db.py`）和个性化反馈循环（`focusflow/service.py`）从第一天起就在记录*实际用时/预估用时的比例*和*拆解接受率*——详见下面的"评估指标"。

**3. 零配置就能跑起来。** 内置的启发式"mock" LLM（`focusflow/mock_llm.py`）覆盖了 brain dump、拆解、打断处理这一整套逻辑，不需要 API key，只是质量会打点折扣。谁 clone 了仓库，30 秒内就能看到真实的产品行为，不用先去申请 key。

**4. 个性化用两个数字就够了，不需要上机器学习。** 实际/预估用时的比例、拆解被拒绝的频率——这两个数字就足够在下一次拆解时微调步骤大小，不需要微调模型也不需要推荐系统。方案更重带来的准确率提升，得先证明配得上它多背的那些故障风险，这里显然不配。

**5. 默认单用户，多租户只是一个开关的事。** SQLite 里每一行数据默认都用 `"default"` 当 key，设置了 `FOCUSFLOW_MULTI_SESSION=true` 之后，`focusflow/db.py` 就会改成按每个浏览器会话的 id 区分数据。公开 demo（一堆陌生人挤在同一个进程里）和个人本地安装（只有你自己，状态要能跨重启保留）对数据库的要求正好相反，这个开关让同一套代码能伺候好两种场景，本地版的 Resume 体验也不用为公开 demo 的需求让步。

**6. LLM 调用失败了，页面不会跟着崩。** 真实的 API 调用设了超时时间，交给 SDK 自带的重试和退避机制处理（`focusflow/llm.py`）。如果调用还是失败了，或者模型吐出来的内容解析不成 JSON，FocusFlow 会记一条警告日志，然后自动退回成"没配 API key"时的那套启发式输出。这个工具卖的就是"保持冷静、别让人过载"，因为触发了限流就甩一个报错堆栈出来，比给一个稍微逊色点的建议破坏力大得多。

<details>
<summary><strong>架构</strong>（点击展开）</summary>

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

用 [LangGraph](https://github.com/langchain-ai/langgraph) 实现为一个小而受控的状态机（`focusflow/graph.py`）。状态本地持久化在 SQLite（`focusflow/db.py`）中。

| 层 | 文件 |
|---|---|
| 共享状态结构 | `focusflow/state.py` |
| 路由 + 节点（LangGraph） | `focusflow/graph.py` |
| 有边界的 Agent 策略引擎 | `focusflow/policy.py` |
| 数据库 + 图编排、个性化 | `focusflow/service.py` |
| LLM provider 封装 | `focusflow/llm.py`, `focusflow/mock_llm.py` |
| 提示词 | `focusflow/prompts.py` |
| 持久化（状态、事件、偏好） | `focusflow/db.py` |
| 界面文案（中/英） | `focusflow/i18n.py` |
| 主界面 | `app.py`（Streamlit） |
| 设置 checklist | `pages/0_Setup.py` |
| 分析看板 | `pages/1_Analytics.py` |

</details>

<details>
<summary><strong>技术栈</strong></summary>

Python · [Streamlit](https://streamlit.io)（界面）· [LangGraph](https://github.com/langchain-ai/langgraph)（编排）· SQLite（持久化）· Anthropic / OpenAI API，带启发式离线回退 · pytest + Streamlit `AppTest`（无浏览器界面测试）· GitHub Actions（CI）

</details>

### 更多界面

<img src="docs/screenshots/06_setup.png" width="720" alt="设置页面：一个顺序无关的 checklist，用来接入真实 LLM API key">

Setup 是一个真实的、会持久化的、不分先后顺序的 checklist（`pages/0_Setup.py`）——刻意没有做成线性向导，和这个产品"不强迫顺序"的核心原则一致。

<img src="docs/screenshots/07_analytics.png" width="720" alt="分析看板，显示完成率、放弃率等指标">

### 评估指标

产品质量在这里靠使用效果来判断，而不是"回复听起来好不好"（这是需求文档里写明的要求，不是事后补的）。每一轮交互都会记录到本地的 `events` 表，Analytics 页面（`pages/1_Analytics.py`）呈现：

- 任务启动率、启动耗时、任务完成率
- 拆解接受率、恢复成功率、放弃率
- 认知负荷（每次任务完成后一次自评点击）
- 北极星指标：**每位用户每周成功启动任务的次数**

### 路线图

- **V0.1**（已完成）：Brain Dump → 任务提取 → 拆解 → 排优先级 → 一个下一步动作。
- **V0.2**（已完成）：LangGraph 工作流、专注模式、打断捕获、稍后列表、恢复、SQLite 持久化。
- **V0.3**（部分完成）：已完成——专注计时器、步骤再拆分、长期偏好记忆、自适应拆解、分析看板。未完成——日历集成。

### 测试

```bash
pip install -r requirements.txt
pytest
```

24 个测试，三个层次：针对 mock LLM 的纯图逻辑测试（不需要 API key）、SQLite 持久化测试，以及无浏览器的 Streamlit `AppTest`，会真的点击走一遍界面（brain dump → 开始 → 拆分 → 完成、切换语言、清空隐私数据），用来抓单元测试抓不到的控件接线问题。CI 在每次 push 时对 Python 3.11 和 3.13 跑全套测试（见上方徽章）。

### 接入真实 LLM

FocusFlow **不需要任何 API key** 也能跑（启发式 mock 后端）。以下步骤彼此独立，按任意顺序完成：

- [ ] 申请一个 API key：[Anthropic 控制台](https://console.anthropic.com/settings/keys) 或 [OpenAI 控制台](https://platform.openai.com/api-keys)。
- [ ] 把项目根目录的 `.env.example` 复制一份，命名为 `.env`。
- [ ] 打开 `.env`，把你的 key 粘贴到 `ANTHROPIC_API_KEY=` 或 `OPENAI_API_KEY=` 后面（两个都填时优先用 Anthropic）。
- [ ] 重启应用：停掉后重新运行 `streamlit run app.py`。
- [ ] 看侧边栏的 "LLM backend" 那一行，或者应用内的 **Setup** 页面，会实时显示连接状态。

### 部署自己的版本

部署到 [Streamlit Community Cloud](https://share.streamlit.io) 这类平台开箱即用（指向这个仓库，主文件填 `app.py`）。如果会有不止一个人同时用同一个部署实例，有一个设置很重要：

```
FOCUSFLOW_MULTI_SESSION=true
```

不设这个的话，共享部署的每个访问者都会读写同一行"本地档案"数据——自己一个人用没问题，公开 demo 有多个陌生人同时访问就不行了。详见"设计决策"第 5 条。

### 隐私与安全

- 不是医疗设备：不做 ADHD 诊断、不提供用药建议、不能替代专业医疗意见。
- 所有数据都保存在本地单个 SQLite 文件中（默认 `focusflow.db`，已加入 `.gitignore`）。
- 应用内的"删除我的所有数据"（或调用 `service.reset_all()`）可以随时清空已存储的状态和事件历史。

### 许可证

[MIT](LICENSE)
