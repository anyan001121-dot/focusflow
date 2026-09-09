"""FocusFlow -- ADHD-friendly executive-function agent (Streamlit UI).

Run with: streamlit run app.py
"""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from focusflow import db, service

load_dotenv()

st.set_page_config(page_title="FocusFlow", page_icon="🎯", layout="centered")

db.init_db()

if "ff_state" not in st.session_state:
    st.session_state.ff_state = service.load_or_new_state()

state = st.session_state.ff_state


def _update(new_state: dict) -> None:
    st.session_state.ff_state = new_state
    st.rerun()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### FocusFlow")
    st.caption(
        "An executive-function assistant. Not a medical device -- it does not "
        "diagnose or treat ADHD."
    )

    provider = os.environ.get("ANTHROPIC_API_KEY") and "Anthropic"
    provider = provider or (os.environ.get("OPENAI_API_KEY") and "OpenAI")
    provider = provider or "Mock (no API key set)"
    st.caption(f"LLM backend: {provider}")

    st.divider()

    later_list = state.get("later_list", [])
    st.markdown(f"**Later list** ({len(later_list)})")
    if later_list:
        for item in later_list:
            st.markdown(f"- {item}")
    else:
        st.caption("Nothing parked here yet.")

    st.divider()

    if st.button("Where was I? (Resume)", use_container_width=True):
        _update(service.resume(state))

    with st.expander("Privacy"):
        st.caption("All data is stored locally in focusflow.db.")
        if st.button("Delete all my data", type="secondary", use_container_width=True):
            _update(service.reset_all())


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.title("🎯 FocusFlow")

response = state.get("response", {})
rtype = response.get("type")

if rtype == "resume":
    if response.get("has_active_task"):
        st.info("**Welcome back.**")
        st.markdown(f"You were: **{response['current_task']}**")
        completed = response.get("completed_steps", [])
        if completed:
            st.markdown("Completed:")
            for step in completed:
                st.markdown(f"- ✅ {step}")
        st.markdown(f"**Next action:** {response.get('next_action', '')}")
        st.caption(f"Estimated time: ~{response.get('estimated_time', 5)} min")
    else:
        st.info("Nothing to resume yet. Start by telling me what's on your mind below.")

elif rtype == "clarify":
    st.info(response.get("message", ""))

elif rtype == "brain_dump":
    st.subheader("Here's what I heard")
    priorities = response.get("priorities", [])
    if not priorities:
        st.caption("I couldn't find a clear task in there -- try naming one thing directly.")
    for p in priorities:
        cols = st.columns([4, 1])
        cols[0].markdown(f"**{p['task']}**  \n:small[urgency: {p['urgency']}]")
        if cols[1].button("Start", key=f"start-{p['task']}"):
            _update(service.start_focus(state, p["task"]))
    later_additions = response.get("later_list_additions", [])
    if later_additions:
        st.caption(f"Parked {len(later_additions)} lower-priority item(s) in the Later list.")
    ideas = response.get("ideas", [])
    if ideas:
        with st.expander(f"Ideas / non-actionable ({len(ideas)})"):
            for i in ideas:
                st.markdown(f"- {i['task']}")

# ---------------------------------------------------------------------------
# Focus mode
# ---------------------------------------------------------------------------

if state.get("focus_mode"):
    st.divider()
    st.subheader("Current focus")
    st.markdown(f"**Goal:** {state.get('current_goal', '')}")
    st.success(f"**Start here:** {state.get('current_step', '')}")
    st.caption(f"~{state.get('estimated_time', 5)} min")

    if response.get("type") == "interruption":
        if response.get("captured"):
            st.warning("Captured for later. Back to your current focus above.")
        else:
            st.caption("Noted -- looks related to what you're already doing.")

    completed = state.get("completed_steps", [])
    if completed:
        with st.expander(f"Completed ({len(completed)})"):
            for step in completed:
                st.markdown(f"- ✅ {step}")

    if st.button("✅ Done with this step", type="primary"):
        _update(service.mark_step_done(state))

    aside = st.text_input(
        "Anything else on your mind right now?",
        key="interruption_input",
        placeholder="e.g. I just remembered I need to buy detergent",
    )
    if st.button("Send") and aside.strip():
        _update(service.handle_message(state, aside.strip()))

elif response.get("type") == "task_complete":
    st.balloons()
    st.success(response.get("session_summary", "Done."))

else:
    st.divider()
    st.subheader("What's on your mind?")
    st.caption(
        "Dump everything messily, or name one thing you want to start right now."
    )
    dump = st.text_area("Brain dump", key="brain_dump_input", label_visibility="collapsed")
    if st.button("Go", type="primary") and dump.strip():
        _update(service.handle_message(state, dump.strip()))
