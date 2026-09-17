<p align="center"><img src="assets/logo.svg" width="64" alt="FocusFlow 的小芽头像" /></p>
<h1 align="center">FocusFlow</h1>
<p align="center"><strong>开始不了的时候，先找一小步。<br />被打断以后，留一个能回来的地方。</strong></p>
<p align="center">A small next step. A place to come back to.</p>
<p align="center"><a href="https://focusflow-j2gkquxeg2cifcxmyqxw8w.streamlit.app/">在线体验 / Try the demo</a> · <a href="#english">English</a> · <a href="docs/before-after.md">使用前与使用后</a> · <a href="docs/development.md">安装与开发</a></p>

## 也许你遇到过这样的时刻

文档已经打开很久，第一句话还没写。脑子里同时挂着论文、邮件和明天的面试，哪一件都想做，哪一件都没开始。

好不容易做了一会儿，一条消息把你带走。等你回来，又要花力气想：我刚才做到哪里了？

FocusFlow 想在这些具体的时刻帮一点忙。你可以把没整理好的想法写下来，先看一个能动手的小步骤。突然想起别的事，就先记在旁边。需要离开的时候，保存当前的位置，回来再接着做。

**你不用先把自己调整到“能专注”的状态，才有资格使用这个工具。** 今天只能做一点，也可以从这一点开始。

## 它适合谁？

需要独立完成学习或工作，已经知道大概要做什么，却常常卡在开始、或者中断后难以返回的成年人。

我们特别关注 ADHD 用户的使用困难，也欢迎因忙乱、疲惫或其他原因难以专注的人。你不需要提供诊断，也不需要解释自己为什么卡住。每个人需要的帮助不同，可以只用对你有用的部分。

## 使用前与使用后，会有什么不同？

下面是场景示例，描述工具能提供的支持，不是真实用户证言或效果保证。

| 此刻可能发生的事 | FocusFlow 能帮你做的事 | 仍然由你决定 |
| --- | --- | --- |
| “我要写论文。”任务太大，不知道从哪儿碰起 | 把当前动作单独放在眼前，并显示这一步做到哪里就可以 | 建议是否适合；太难时可以再拆小 |
| 写着写着想起另一封邮件，怕忘就想切过去 | 把这件事暂存，保留原来的步骤 | 什么时候处理；有急事可以先暂停 |
| 开会回来，忘了刚才停在哪里 | 保存目标、步骤和可选的返回提示 | 什么时候回来，不需要补打卡 |
| 做完一小段，却离整个目标还很远 | 记录完成的小步骤，不把它说成整件事已完成 | 继续下一件事，或今天先停在这里 |

[看看完整的一天：开始论文 → 想起邮件 → 暂停 → 回来继续](docs/before-after.md)

## 先试一次就好

1. **写下眼前的事。** 一句话就行。也可以一次写几件，工具会列出最多三个候选任务。
2. **看一个下一步。** 不合适或太难，可以再拆小；不用先看完一整份计划。
3. **随时停下来。** 可以留一句“结果章节，第 2 段”，也可以不写提示直接暂停。

完成后，暂存的事情可以直接开始，也可以标记为已处理。计时默认收起，想看时再打开。

无需 API key 就能体验**练习模式**。它使用固定模板，能演示操作流程，但建议可能笼统。连接 AI 服务后才会由模型生成建议，具体内容仍需要你判断。公开演示的版本取决于部署状态；仓库更新不代表线上已经更新。

## 我们希望它怎样陪你做事

- **少一点选择负担。** 聚焦当前步骤，其他内容按需展开。
- **休息有位置。** 暂停不是失败，也不会清空已经做过的部分。
- **回来不需要解释。** 不问“怎么又分心了”，直接把留下的位置给你。
- **不替你判断努力够不够。** 没有连续签到要求，也不把未完成轮次直接叫作放弃。

这些是设计选择，不是已经证实的干预效果。FocusFlow 仍是一个在完善中的原型。

## 数据会放在哪里？

本地单人运行时，任务、事件记录和偏好保存在运行应用的电脑里的 SQLite 数据库中。接入 Anthropic 或 OpenAI 后，任务内容会发给所选服务商生成建议。应用内可以删除保存的数据。

公开部署需要启用多会话隔离。它使用临时会话标识，不能保证刷新或重新访问后还能找回原来的任务；请不要把公开演示当作长期个人工作区。[详细说明与配置](docs/development.md#privacy-and-deployment)

FocusFlow 不诊断或治疗 ADHD，也不提供医疗建议。

## 在自己电脑上运行

需要 Python 3.11 或以上版本：

```bash
git clone https://github.com/anyan001121-dot/focusflow.git
cd focusflow
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

[接入 AI、部署、测试与架构说明](docs/development.md) · [产品走查与真实用户验证计划](docs/product-review-2026-09-16.md)

## English

### When knowing what to do isn't enough to begin

The document is open. You know the work matters. But you keep moving between tabs, and the first sentence is still unwritten. Or a message interrupts you, and coming back means figuring out where you left off all over again.

FocusFlow is for those moments. Write down a task in your own words. See one small next step with a clear stopping point. Park another thought without losing the current task. If you need a break, save your place and return when you're ready.

It's designed for adults who struggle to start or return to study and work, with particular attention to ADHD users. You don't need a diagnosis to use it. You can use whichever parts help.

### Before and with FocusFlow

These are illustrative situations, not measured results or testimonials.

| Without a place to keep your next step | With FocusFlow |
| --- | --- |
| A large goal sits on a list: “write my paper” | One suggested action and a visible completion condition |
| Another thought pulls you into a different task | A place to save it while keeping the current step |
| Returning from a break means rebuilding the context | Your saved step and an optional note from before the break |
| A short session feels unfinished | A record of the steps you took, without claiming the whole goal is done |

Pause whenever you need. Show the timer only if it helps. There are no streaks to repair when you return.

Practice mode works without an API key and uses templates. Connected AI suggestions may be more specific, but can still miss the context. Completing suggested steps is not proof of completing the larger real-world goal. We haven't established that FocusFlow improves ADHD symptoms or task outcomes.

### Run, connect, and contribute

Use the installation commands above. The [development guide](docs/development.md) covers AI configuration, persistence, public deployment, and tests. The [scenario guide](docs/before-after.md) walks through the intended experience and its limits.

Local data is stored on the machine running the app. If an AI provider is configured, task text is sent to that provider. Public demo sessions are temporary. FocusFlow is not a medical device.

If you try it, useful feedback is very concrete: **What were you trying to do? Which step helped you act, or made you stop?** You don't need to share private task content or medical information.

[MIT license](LICENSE)
