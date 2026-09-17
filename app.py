"""FocusFlow -- ADHD-friendly executive-function agent (Streamlit UI).

Run with: streamlit run app.py
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from focusflow import db, service
from focusflow.i18n import LANGUAGES, t, urgency_label

load_dotenv()

st.set_page_config(page_title="FocusFlow", page_icon="assets/logo.svg", layout="centered", initial_sidebar_state="collapsed")
st.logo("assets/logo.svg", size="large")
st.html(Path(__file__).with_name("assets").joinpath("app.css").read_text())

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


def _fill_example(text: str) -> None:
    st.session_state.brain_dump_input = text


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
        with st.expander(t(lang, "later_review"), expanded=not state.get("focus_mode")):
            for index, item in enumerate(later_list):
                st.write(item)
                if not state.get("focus_mode"):
                    left, right = st.columns(2)
                    if left.button(t(lang, "later_start"), key=f"later-start-{index}"):
                        _update(service.resolve_later(state, index, start=True, session_id=session_id))
                    if right.button(t(lang, "later_resolved"), key=f"later-resolved-{index}"):
                        _update(service.resolve_later(state, index, session_id=session_id))
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

main_col = st.container()

with main_col:
    mascot = Path(__file__).with_name("assets").joinpath("logo.svg").read_text()
    st.html(f'<div class="ff-brand"><span class="ff-seed" aria-hidden="true">{mascot}</span> FocusFlow <span class="ff-brand-note">ONE SMALL STEP</span></div>')
    if not state.get("focus_mode"):
        st.caption(t(lang, "product_promise"))

    response = state.get("response", {})
    rtype = response.get("type")

    fallback_reason = response.get("llm_fallback")
    if fallback_reason == "auth":
        st.error(t(lang, "llm_fallback_auth"))
    elif fallback_reason == "rate_limit":
        st.warning(t(lang, "llm_fallback_rate_limit"))
    elif fallback_reason:
        st.caption(t(lang, "llm_fallback_notice"))

    if rtype == "resume":
        if response.get("has_active_task"):
            st.info(t(lang, "resume_welcome"))
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

    if state.get("focus_mode") and state.get("paused_at"):
        st.info(t(lang, "pause_saved"))
        st.markdown(t(lang, "focus_goal", goal=state.get("current_goal", "")))
        with st.container(border=True):
            st.caption(t(lang, "next_step_label"))
            st.subheader(state.get("current_step", ""))
        if state.get("resume_note"):
            st.write(state["resume_note"])
        if st.button(t(lang, "return_button"), type="primary", key="return-focus"):
            _update(service.resume(state, session_id))

    elif state.get("focus_mode"):
        st.subheader(t(lang, "focus_header"))
        st.markdown(t(lang, "focus_goal", goal=state.get("current_goal", "")))
        with st.container(border=True):
            st.caption(t(lang, "next_step_label"))
            st.subheader(state.get("current_step", ""))
            if state.get("completion_condition"):
                st.caption(t(lang, "completion_condition", condition=state["completion_condition"]))
        if state.get("resume_note"):
            st.caption(t(lang, "return_note", note=state["resume_note"]))
        st.caption(t(lang, "focus_estimated", minutes=state.get("estimated_time", 5)))
        if st.toggle(t(lang, "show_timer"), value=False, key="show_timer"):
            _focus_timer(state.get("step_start_time", ""), state.get("estimated_time", 5), lang)

        if response.get("type") == "interruption":
            if response.get("captured"):
                st.caption(t(lang, "interruption_captured"))
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

        with st.expander(t(lang, "pause_header")):
            note = st.text_input(t(lang, "pause_note"), key="pause_note", value=state.get("resume_note", ""))
        if st.button(t(lang, "pause_button"), key="pause-focus", use_container_width=True):
            _update(service.pause_focus(state, note, session_id))

        with st.form("capture_thought", clear_on_submit=True, border=False):
            aside = st.text_input(
                t(lang, "aside_label"), key="interruption_input",
                placeholder=t(lang, "aside_placeholder"),
            )
            if st.form_submit_button(t(lang, "send_button")) and aside.strip():
                _update(service.handle_message(state, aside.strip(), session_id))

    elif response.get("type") == "task_complete":
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

    if not state.get("focus_mode"):
        st.title(t(lang, "whats_on_mind_header"))
        st.write(t(lang, "whats_on_mind_caption"))
        with st.expander(t(lang, "example_header")):
            for key in ("example_study", "example_work", "example_return"):
                st.button(t(lang, key), key=key, on_click=_fill_example,
                          args=(t(lang, key),), use_container_width=True)
        dump = st.text_area(
            t(lang, "input_label"),
            key="brain_dump_input",
            placeholder=t(lang, "input_placeholder"),
            height=140,
        )
        if st.button(t(lang, "go_button"), type="primary", use_container_width=True):
            if dump.strip():
                _update(service.handle_message(state, dump.strip(), session_id))
            st.caption(t(lang, "input_placeholder"))
        st.caption(t(lang, "start_reassurance"))
