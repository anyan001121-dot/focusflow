# Setup and development / 安装与开发

The main [README](../README.md) introduces the experience. This page covers how it actually runs.

## Local setup

Python 3.11+:

```bash
git clone https://github.com/anyan001121-dot/focusflow.git
cd focusflow
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

No API key is required. Practice mode uses deterministic templates; it is useful for exploring the flow, not assessing model quality.

## Connecting a real LLM

Copy `.env.example` to `.env`, then configure one provider key:

```dotenv
ANTHROPIC_API_KEY=your-key-here
# OR
OPENAI_API_KEY=your-key-here
```

Restart Streamlit after editing the file. Never commit `.env` or keys. Optional model overrides are `FOCUSFLOW_ANTHROPIC_MODEL` and `FOCUSFLOW_OPENAI_MODEL`; see `focusflow/llm.py` for current defaults. If both provider keys exist, Anthropic takes priority.

Provider failures fall back to practice mode. Authentication errors, rate limits and generic failures are disclosed in the interface. A fallback output is not a successful model response.

## Architecture

| File | Responsibility |
| --- | --- |
| `app.py`, `assets/app.css`, `.streamlit/config.toml` | Streamlit UI, responsive layout, theme |
| `focusflow/i18n.py` | English / Chinese UI copy |
| `focusflow/state.py` | Task, step, completion condition, pause and return state |
| `focusflow/graph.py` | Intent routing, breakdown, split, capture, completion, resume |
| `focusflow/policy.py` | Prevent an interruption proposal from replacing active work |
| `focusflow/service.py` | Persistence, explicit pause/resume, Later actions, preference hints |
| `focusflow/db.py` | SQLite state, events and preferences |
| `focusflow/llm.py`, `prompts.py`, `mock_llm.py` | Provider calls, prompts and template fallback |
| `pages/` | Setup and usage records |
| `tests/` | Unit, persistence and Streamlit AppTest journeys |

A single task starts directly. Multiple fragments go through Brain Dump, which presents up to three candidate tasks. The graph proposes one active step and queues follow-ups. Interruption handling cannot silently replace active work. Explicit pause preserves the step; resume shifts its timer origin by the paused duration. Later items can be started or resolved when no task is active.

UI styles keep native Streamlit controls and focus behavior. The system font avoids Google Fonts requests; the timer is hidden until requested. CSS test IDs are presentation hooks and should be checked when upgrading Streamlit.

## Privacy and deployment

By default this is a **single-user app**. State, event payloads (including task text), preferences and setup checklist live in `focusflow.db` on the machine running it. `FOCUSFLOW_DB_PATH` overrides that path.

With a real AI provider, task text is sent to that provider. Local storage does not mean all processing stays local. The in-app delete action clears this app's stored data for the applicable profile; it does not delete provider-side records or external backups.

A shared deployment must enable:

```dotenv
FOCUSFLOW_MULTI_SESSION=true
```

Without it, visitors share the default profile. With it, rows are scoped to a random Streamlit session ID. This is session separation, **not account authentication or durable cross-device identity**. A reload or new browser session may lose access to the prior state. Local single-user mode can restore state across restarts as long as the database persists. Hosted filesystem lifetime depends on the host.

For Streamlit hosting, use `app.py` as entry point, configure secrets on the host and enable the setting above. Do not use a public practice demo as a permanent store for private work. Uploading code does not by itself establish a successful deployment; verify the hosted build separately.

## Tests

```bash
python -m pytest -q
```

Tests use isolated databases and template suggestions. AppTest covers task entry, splitting, completion, language changes, pause/return, examples and interruption capture. Provider failure tests intentionally emit warnings. This is functional validation, not evidence of benefits for ADHD or real-world task completion.

## Metrics and limitations

The Analytics page reports completed step sets, generated sets, captured interruptions, estimated/actual elapsed-time ratios, split history and optional effort ratings. “Not recorded complete” can include work still in progress. Generating a suggestion is not a verified task start; clicking Done is not independent proof of real-world completion.

Explicit pauses are excluded from the current step timer. Unpaused time away is not automatically detected, and earlier paused time is not an attention measurement. Preference hints use historical duration ratios and split frequency after a minimum sample; they may still reflect noisy observations.

Known gaps: generic template steps, limited task-context correction, no scheduled reminders, no durable hosted identity, and no automatic follow-on set for a larger goal. See the [product review](product-review-2026-09-16.md) for the user validation plan.
