"""FocusFlow setup checklist -- connect a real LLM (Anthropic or OpenAI).

ADHD-friendly by design: every step is an independent checkbox with no
required order and no gating on prior steps, per PRD section 7 ("never
overwhelm", "don't force a sequence"). The one thing that genuinely can't
be faked is whether an API key is actually picked up -- that status line
is computed live from the environment, not a checkbox.
"""

from __future__ import annotations

import os
import uuid

import streamlit as st

from focusflow import db, service
from focusflow.i18n import t

st.set_page_config(page_title="FocusFlow -- Setup", page_icon="⚙️", layout="centered")

db.init_db()

# See app.py: only matters in FOCUSFLOW_MULTI_SESSION mode (public demo).
session_id = st.session_state.setdefault("session_id", str(uuid.uuid4()))

state = st.session_state.get("ff_state") or service.load_or_new_state(session_id)
lang = state.get("lang", "en")

st.title(t(lang, "setup_title"))
st.caption(t(lang, "setup_intro"))

if os.environ.get("ANTHROPIC_API_KEY"):
    st.success(t(lang, "setup_status_connected", provider="Anthropic"))
elif os.environ.get("OPENAI_API_KEY"):
    st.success(t(lang, "setup_status_connected", provider="OpenAI"))
else:
    st.warning(t(lang, "setup_status_mock"))

st.divider()
st.caption(t(lang, "setup_order_note"))

checklist = db.load_checklist(session_id=session_id)

_STEPS = [
    ("get_key", "step_get_key"),
    ("copy_env", "step_copy_env"),
    ("paste_key", "step_paste_key"),
    ("restart", "step_restart"),
    ("verify", "step_verify"),
]

for step_id, label_key in _STEPS:
    checked = st.checkbox(t(lang, label_key), value=checklist.get(step_id, False), key=f"chk_{step_id}")
    if checked != checklist.get(step_id, False):
        checklist[step_id] = checked
        db.save_checklist(checklist, session_id=session_id)

st.markdown(
    "[Anthropic console](https://console.anthropic.com/settings/keys) · "
    "[OpenAI console](https://platform.openai.com/api-keys)"
)

st.divider()
st.subheader(t(lang, "for_others_header"))
st.caption(t(lang, "for_others_body"))
