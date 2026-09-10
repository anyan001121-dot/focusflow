"""FocusFlow -- ADHD-friendly executive-function agent (Streamlit UI).

Run with: streamlit run app.py
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv

from focusflow import db, service
from focusflow.i18n import LANGUAGES, t, urgency_label

load_dotenv()

st.set_page_config(page_title="FocusFlow", page_icon="assets/logo.svg", layout="wide")
st.logo("assets/logo.svg", size="large")

db.init_db()

# Only matters when FOCUSFLOW_MULTI_SESSION=true (e.g. a public demo
# deployment) -- see focusflow/db.py. Ignored for local personal use, so
# this never affects the single-profile persistence Resume relies on.
session_id = st.session_state.setdefault("session_id", str(uuid.uuid4()))

if "ff_state" not in st.session_state:
    st.session_state.ff_state = service.load_or_new_state(session_id)

state = st.session_state.ff_state
lang = state.get("lang", "en")


def _update(new_state: dict) -> None:
    st.session_state.ff_state = new_state
    st.rerun()


@st.fragment(run_every="1s")
def _focus_timer(step_start_time: str, estimated_minutes: float, lang: str) -> None:
    """Live-updating elapsed time for the current step, no auto-refresh of the rest of the page."""
    if not step_start_time:
        return
    try:
        started = datetime.fromisoformat(step_start_time)
    except ValueError:
        return
    elapsed_seconds = max(0, (datetime.now(timezone.utc) - started).total_seconds())
    mm, ss = divmod(int(elapsed_seconds), 60)
    st.caption(t(lang, "timer_elapsed", mmss=f"{mm:02d}:{ss:02d}"))
    if estimated_minutes and elapsed_seconds > estimated_minutes * 60:
        st.caption(t(lang, "timer_over_estimate", minutes=estimated_minutes))


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
        _update(service.set_language(state, chosen, session_id))

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
        _update(service.resume(state, session_id))

    with st.expander(t(lang, "privacy_header")):
        st.caption(t(lang, "privacy_caption"))
        if st.button(t(lang, "delete_button"), type="secondary", use_container_width=True):
            _update(service.reset_all(session_id))


# ---------------------------------------------------------------------------
# Main area -- kept in a wide-but-centered column so the page doesn't feel
# like a narrow strip lost in empty space on larger screens.
# ---------------------------------------------------------------------------

_gutter_l, main_col, _gutter_r = st.columns([1, 5, 1])

with main_col:
    _header_icon, _header_title = st.columns([1, 6], vertical_alignment="center")
    with _header_icon:
        st.image("assets/logo.svg", width=80)
    with _header_title:
        st.title("FocusFlow")

    response = state.get("response", {})
    rtype = response.get("type")

    if response.get("llm_fallback"):
        st.caption(t(lang, "llm_fallback_notice"))

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
            with st.container(border=True):
                st.markdown(
                    f"**{p['task']}**  \n:small[{t(lang, 'urgency_label', urgency=urgency_label(lang, p['urgency']))}]"
                )
                if st.button(t(lang, "start_button"), key=f"start-{p['task']}", use_container_width=True):
                    _update(service.start_focus(state, p["task"], session_id))
        later_additions = response.get("later_list_additions", [])
        if later_additions:
            st.caption(t(lang, "later_parked", n=len(later_additions)))
        ideas = response.get("ideas", [])
        if ideas:
            with st.expander(t(lang, "ideas_header", n=len(ideas))):
                for i in ideas:
                    st.markdown(f"- {i['task']}")

    # -----------------------------------------------------------------------
    # Focus mode
    # -----------------------------------------------------------------------

    if state.get("focus_mode"):
        st.divider()
        st.subheader(t(lang, "focus_header"))
        st.markdown(t(lang, "focus_goal", goal=state.get("current_goal", "")))
        st.success(t(lang, "focus_start_here", step=state.get("current_step", "")))
        st.caption(t(lang, "focus_estimated", minutes=state.get("estimated_time", 5)))
        _focus_timer(state.get("step_start_time", ""), state.get("estimated_time", 5), lang)

        if response.get("type") == "interruption":
            if response.get("captured"):
                st.warning(t(lang, "interruption_captured"))
            else:
                st.caption(t(lang, "interruption_related"))
            if response.get("policy_downgraded"):
                st.caption(t(lang, "policy_kept_on_track", task=state.get("current_task", "")))
        elif response.get("type") == "step_split":
            st.caption(t(lang, "step_split_notice"))

        completed = state.get("completed_steps", [])
        if completed:
            with st.expander(t(lang, "completed_header", n=len(completed))):
                for step in completed:
                    st.markdown(f"- ✅ {step}")

        if st.button(t(lang, "done_button"), type="primary", use_container_width=True):
            _update(service.mark_step_done(state, session_id))
        if st.button(t(lang, "split_button"), use_container_width=True):
            _update(service.split_current_step(state, session_id))

        aside = st.text_input(
            t(lang, "aside_label"),
            key="interruption_input",
            placeholder=t(lang, "aside_placeholder"),
        )
        if st.button(t(lang, "send_button")) and aside.strip():
            _update(service.handle_message(state, aside.strip(), session_id))

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
        task_id = response.get("current_task", "")
        if st.session_state.get("rated_task") == task_id:
            st.caption(t(lang, "cognitive_load_thanks"))
        else:
            st.caption(t(lang, "cognitive_load_prompt"))
            rating_cols = st.columns(3)
            ratings = [
                ("easy", "cognitive_load_easy"),
                ("okay", "cognitive_load_okay"),
                ("hard", "cognitive_load_hard"),
            ]
            for col, (rating, key) in zip(rating_cols, ratings):
                if col.button(t(lang, key), key=f"rate-{rating}", use_container_width=True):
                    service.record_cognitive_load(rating, session_id)
                    st.session_state.rated_task = task_id
                    st.rerun()

    else:
        st.divider()
        st.subheader(t(lang, "whats_on_mind_header"))
        st.caption(t(lang, "whats_on_mind_caption"))
        dump = st.text_area(
            "Brain dump",
            key="brain_dump_input",
            label_visibility="collapsed",
            height=180,
        )
        if st.button(t(lang, "go_button"), type="primary", use_container_width=True) and dump.strip():
            _update(service.handle_message(state, dump.strip(), session_id))
