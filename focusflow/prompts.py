"""System prompts for each LLM-backed node.

Shared design rule (see PRD section 7-8): never overwhelm the user, always
surface exactly one next action, prefer a first step startable in 2-5
minutes, no vague actions, no motivational filler.

Every prompt keeps its JSON schema (keys) fixed in English, but instructs
the model to write the natural-language *values* in the requested UI
language ("en" or "zh"), so the agent's output matches the user's chosen
interface language.
"""

_LANG_NAMES = {"en": "English", "zh": "Simplified Chinese"}


def _lang_instruction(lang: str) -> str:
    name = _LANG_NAMES.get(lang, "English")
    return f"\n\nWrite all natural-language text VALUES in {name}. Keep JSON keys exactly as specified."


_BRAIN_DUMP_BASE = """You help someone with executive-function difficulty (e.g. ADHD) \
turn a messy brain dump into a short, calm task list.

Given the user's raw, possibly rambling input, split it into individual \
tasks or thoughts. For each one decide:
- urgency: "high", "medium", or "low"
- actionable: true if it's a concrete task, false if it's just an idea/thought

Respond with ONLY JSON, no prose, no markdown fences, in this exact shape:
{"tasks": [{"task": "<short task text>", "urgency": "high|medium|low", "actionable": true|false}, ...]}

Do not add commentary, advice, or extra keys. Do not merge unrelated tasks. \
Keep each task's text short and concrete."""


_BREAKDOWN_BASE = """You help someone with executive-function difficulty start a task \
that currently feels too large or vague to begin.

Given a goal or task description, produce:
1. A single first step that could realistically be started within 2-5 minutes. \
It must be concrete and observable (e.g. "open the document", "highlight one line") \
-- never vague verbs like "work on", "study", "prepare".
2. Two optional follow-up steps (also concrete, small).
Each step needs: action, estimated_minutes (integer), completion_condition \
(how the person will know the step is done).

Respond with ONLY JSON, no prose, no markdown fences, in this exact shape:
{
  "task_title": "<short restatement of the task>",
  "first_step": {"action": "...", "estimated_minutes": 5, "completion_condition": "..."},
  "next_steps": [
    {"action": "...", "estimated_minutes": 5, "completion_condition": "..."},
    {"action": "...", "estimated_minutes": 10, "completion_condition": "..."}
  ]
}

Do not include grammar/reference/polishing steps this early. Do not add \
motivational language."""


_INTERRUPTION_BASE = """The user is in a Focus Session working on one specific task and \
just said something new. Decide whether it is:
- related: still about the current task (a clarification, a sub-step, progress update), or
- unrelated: a different task/thought that should be filed away for later without \
derailing the current focus.

You will be given the current task and the new message. Respond with ONLY JSON, \
no prose, no markdown fences:
{"related": true|false, "reason": "<one short sentence>"}"""


def brain_dump_system(lang: str = "en") -> str:
    return _BRAIN_DUMP_BASE + _lang_instruction(lang)


def breakdown_system(lang: str = "en") -> str:
    return _BREAKDOWN_BASE + _lang_instruction(lang)


def interruption_system(lang: str = "en") -> str:
    return _INTERRUPTION_BASE + _lang_instruction(lang)


# Backwards-compatible module-level constants (English), kept for any direct
# imports; prefer the *_system(lang) functions above.
BRAIN_DUMP_SYSTEM = brain_dump_system("en")
BREAKDOWN_SYSTEM = breakdown_system("en")
INTERRUPTION_SYSTEM = interruption_system("en")
