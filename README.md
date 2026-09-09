# FocusFlow

An AI executive-function assistant for people with ADHD or attention/task-management
difficulties. **FocusFlow does not diagnose or treat ADHD.** It exists to close the
gap between *"I know what I need to do"* and *"I can actually start and continue
doing it."*

Design principle: **do not maximize information — minimize the cognitive effort
required to take the next useful action.**

## What it does

- **Brain Dump** — turn messy, unstructured thoughts into at most three clear
  priorities, without dumping a huge list back at you.
- **Task Breakdown** — turn a vague goal ("prepare for an interview") into one
  concrete first step you can start in a few minutes.
- **Focus Mode** — while you're working, a new thought ("I need to buy detergent")
  is captured to a Later list instead of derailing your current task.
- **Resume** — after an interruption, see only what you were doing, what's done,
  and what's next — not the whole project again.

## Quickstart

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

## Architecture

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
| UI | `app.py` (Streamlit) |

## Agent behaviour rules

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

## Roadmap

- **V0.1** (done): Brain Dump -> Task Extraction -> Breakdown -> Prioritization ->
  One Next Action.
- **V0.2** (done): LangGraph workflow, Focus Mode, interruption capture, Later
  list, Resume, SQLite persistence.
- **V0.3** (future, only after the core loop is validated): calendar/timer
  integration, long-term preference memory, adaptive task sizing, an
  analytics dashboard over the metrics below.

## Evaluation

Product quality should be judged on usage outcomes, not on whether responses
"sound good." FocusFlow logs each turn to a local `events` table
(`focusflow/db.py`) to eventually support:

- Task Start Rate, Time-to-Start, Task Completion Rate
- Breakdown Acceptance Rate, Resume Success Rate, Abandonment Rate
- Cognitive Load (self-reported)
- North Star: **Successful Task Starts per User per Week**

## Privacy & safety

- Not a medical device: no ADHD diagnosis, no medication advice, no
  replacement for professional care.
- All data is stored locally in a single SQLite file (`focusflow.db` by
  default, gitignored).
- Use the "Delete all my data" button in the app (or `service.reset_all()`)
  to wipe stored state and event history at any time.

## Tests

```bash
pytest
```

Graph tests run entirely against the mock LLM backend, so no API key is
needed to verify the core control flow (brain dump prioritization,
interruption handling, resume, task completion).
