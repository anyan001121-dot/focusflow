---
layout: default
---

<p align="center">
  <img src="https://raw.githubusercontent.com/anyan001121-dot/focusflow/main/assets/logo.svg" width="96" alt="FocusFlow mascot" />
</p>

**FocusFlow optimizes for starting, not planning.** It's a small, deliberately bounded AI agent for ADHD-style task-initiation friction — not a chatbot with a to-do list bolted on, and not a medical device.

<p align="center">
  <a href="https://focusflow-j2gkquxeg2cifcxmyqxw8w.streamlit.app/"><strong>Try it live →</strong></a>
  &nbsp;·&nbsp;
  <a href="https://github.com/anyan001121-dot/focusflow"><strong>View source on GitHub</strong></a>
  &nbsp;·&nbsp;
  <a href="https://github.com/anyan001121-dot/focusflow#中文"><strong>中文说明</strong></a>
</p>

## What it does

- **Brain Dump** — dump everything messily; get back at most three clear priorities, with the rest quietly parked.
- **Breakdown** — a vague goal becomes one concrete step you can start in 2–5 minutes, never a full plan.
- **Focus Mode** — one goal, one step, a live elapsed-time readout.
- **Interruption capture** — a new thought mid-task gets filed to a Later list instead of taking over — a lightweight prospective-memory system, not a distraction bin.
- **Resume** — coming back shows only what's done, what's current, and what's next.

![Brain Dump screen showing three prioritized cards with a Start button on each](https://raw.githubusercontent.com/anyan001121-dot/focusflow/main/docs/screenshots/02_brain_dump_result.png)

## Why it's built this way

FocusFlow's router is a small, code-defined [LangGraph](https://github.com/langchain-ai/langgraph) workflow — but interruption handling is a genuine, *bounded* agent: the LLM can propose abandoning the current task, and a deterministic policy layer (`focusflow/policy.py`) is what actually decides whether that's ever allowed. It isn't, while you're in Focus Mode — no matter how the model argues for it. That guarantee is backed by a test that forces the model to insist on switching anyway and checks the state doesn't budge.

The full write-up — problem framing, every design decision and why, architecture, evaluation methodology, and screenshots of every screen — lives in the [README](https://github.com/anyan001121-dot/focusflow#readme).

## Try it

```bash
git clone https://github.com/anyan001121-dot/focusflow
cd focusflow
pip install -r requirements.txt
streamlit run app.py
```

No API key required to start — FocusFlow runs on a heuristic practice-mode backend out of the box. See the [README](https://github.com/anyan001121-dot/focusflow#connecting-a-real-llm) for connecting Anthropic or OpenAI.
