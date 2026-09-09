"""FocusFlow -- ADHD-friendly executive-function agent (Streamlit UI).

Run with: streamlit run app.py
"""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from focusflow import db, service
from focusflow.i18n import LANGUAGES, t, urgency_label

load_dotenv()

st.set_page_config(page_title="FocusFlow", page_icon="🎯", layout="centered")

db.init_db()

if "ff_state" not in st.session_state:
    st.session_state.ff_state = service.load_or_new_state()

state = st.session_state.ff_state
lang = state.get("lang", "en")


def _update(new_state: dict) -> None:
    st.session_state.ff_state = new_state
    st.rerun()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### FocusFlow")
    st.caption(t(lang, "disclaimer"))

    lang_codes = list(LANGUAGES.keys())
    chosen = st.selectbox(
        t(lang, "language_label"),
        options=lang_codes,
        index=lang_codes.index(lang),
        format_func=lambda code: LANGUAGES[code],
    )
    if chosen != lang:
        _update(service.set_language(state, chosen))

    if os.environ.get("ANTHROPIC_API_KEY"):
        provider = t(lang, "provider_anthropic")
    elif os.environ.get("OPENAI_API_KEY"):
        provider = t(lang, "provider_openai")
    else:
        provider = t(lang, "provider_mock")
    st.caption(t(lang, "llm_backend_label", provider=provider))

    st.divider()

    later_list = state.get("later_list", [])
    st.markdown(f"**{t(lang, 'later_list_header', n=len(later_list))}**")
    if later_list:
        for item in later_list:
            st.markdown(f"- {item}")
    else:
        st.caption(t(lang, "later_list_empty"))

    st.divider()

    if st.button(t(lang, "resume_button"), use_container_width=True):
        _update(service.resume(state))

    with st.expander(t(lang, "privacy_header")):
        st.caption(t(lang, "privacy_caption"))
        if st.button(t(lang, "delete_button"), type="secondary", use_container_width=True):
            _update(service.reset_all())


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.title("🎯 FocusFlow")

response = state.get("response", {})
rtype = response.get("type")

if rtype == "resume":
    if response.get("has_active_task"):
        st.info(t(lang, "resume_welcome"))
        st.markdown(t(lang, "resume_you_were", task=response["current_task"]))
        completed = response.get("completed_steps", [])
        if completed:
            st.markdown(t(lang, "resume_completed_header"))
            for step in completed:
                st.markdown(f"- ✅ {step}")
        st.markdown(t(lang, "resume_next_action", action=response.get("next_action", "")))
        st.caption(t(lang, "resume_estimated", minutes=response.get("estimated_time", 5)))
    else:
        st.info(t(lang, "resume_nothing"))

elif rtype == "clarify":
    st.info(t(lang, "clarify_message"))

elif rtype == "brain_dump":
    st.subheader(t(lang, "brain_dump_header"))
    priorities = response.get("priorities", [])
    if not priorities:
        st.caption(t(lang, "brain_dump_empty"))
    for p in priorities:
        cols = st.columns([4, 1])
        cols[0].markdown(
            f"**{p['task']}**  \n:small[{t(lang, 'urgency_label', urgency=urgency_label(lang, p['urgency']))}]"
        )
        if cols[1].button(t(lang, "start_button"), key=f"start-{p['task']}"):
            _update(service.start_focus(state, p["task"]))
    later_additions = response.get("later_list_additions", [])
    if later_additions:
        st.caption(t(lang, "later_parked", n=len(later_additions)))
    ideas = response.get("ideas", [])
    if ideas:
        with st.expander(t(lang, "ideas_header", n=len(ideas))):
            for i in ideas:
                st.markdown(f"- {i['task']}")

# ---------------------------------------------------------------------------
# Focus mode
# ---------------------------------------------------------------------------

if state.get("focus_mode"):
    st.divider()
    st.subheader(t(lang, "focus_header"))
    st.markdown(t(lang, "focus_goal", goal=state.get("current_goal", "")))
    st.success(t(lang, "focus_start_here", step=state.get("current_step", "")))
    st.caption(t(lang, "focus_estimated", minutes=state.get("estimated_time", 5)))

    if response.get("type") == "interruption":
        if response.get("captured"):
            st.warning(t(lang, "interruption_captured"))
        else:
            st.caption(t(lang, "interruption_related"))

    completed = state.get("completed_steps", [])
    if completed:
        with st.expander(t(lang, "completed_header", n=len(completed))):
            for step in completed:
                st.markdown(f"- ✅ {step}")

    if st.button(t(lang, "done_button"), type="primary"):
        _update(service.mark_step_done(state))

    aside = st.text_input(
        t(lang, "aside_label"),
        key="interruption_input",
        placeholder=t(lang, "aside_placeholder"),
    )
    if st.button(t(lang, "send_button")) and aside.strip():
        _update(service.handle_message(state, aside.strip()))

elif response.get("type") == "task_complete":
    st.balloons()
    st.success(
        t(
            lang,
            "task_complete_message",
            task=response.get("current_task", ""),
            steps=response.get("steps_count", 0),
        )
    )

else:
    st.divider()
    st.subheader(t(lang, "whats_on_mind_header"))
    st.caption(t(lang, "whats_on_mind_caption"))
    dump = st.text_area("Brain dump", key="brain_dump_input", label_visibility="collapsed")
    if st.button(t(lang, "go_button"), type="primary") and dump.strip():
        _update(service.handle_message(state, dump.strip()))
