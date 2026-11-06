"""FocusFlow -- ADHD-friendly executive-function agent (Streamlit UI).

Run with: streamlit run app.py
"""

from __future__ import annotations

import os
import base64
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from focusflow import db, service
from focusflow.return_file import export_return_file, read_return_file
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


def copy(zh: str, en: str) -> str:
    return zh if lang == "zh" else en


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

    with st.expander(copy("带走进度 / 找回进度", "Save / restore progress")):
        st.caption(copy("下载一份进度文件。下次打开页面后上传，就能接着做。文件包含任务文字，请保存在自己的设备上。", "Download a return file and upload it next time. It contains your task text; keep it on your own device."))
        try:
            backup = export_return_file(state)
        except ValueError:
            st.caption(copy("当前进度超出单份文件容量，暂时无法导出；本地保存仍然有效。", "This progress exceeds the return-file limit; local saving still works."))
        else:
            st.download_button(copy("下载进度文件", "Download return file"), data=backup,
                               file_name="focusflow-return.json", mime="application/json", key="download-return")
        uploaded = st.file_uploader(copy("选择之前保存的进度文件", "Choose a saved return file"), type=["json"])
        if uploaded is not None:
            try:
                preview = read_return_file(uploaded.getvalue())
                st.caption(copy(f"找到 {len(preview['parked_tasks'])} 个返回点，将加入待接回，不覆盖眼前的任务。", f"Found {len(preview['parked_tasks'])} return points. They will be added without replacing your current task."))
                if st.button(copy("加入待接回", "Add return points"), key="import-return"):
                    _update(service.import_return_file(state, uploaded.getvalue(), session_id))
            except ValueError:
                st.warning(copy("这份文件无法识别，请选择 FocusFlow 下载的进度文件（不超过 256 KB）。", "Choose a FocusFlow return file no larger than 256 KB."))

    with st.expander(t(lang, "privacy_header")):
        st.caption(t(lang, "privacy_caption"))
        confirmed = st.checkbox(copy("我确认清空任务、暂存和使用记录", "Clear my tasks, saved thoughts and history"))
        if st.button(t(lang, "delete_button"), disabled=not confirmed, type="secondary", use_container_width=True):
            st.session_state.pop("rated_task", None)
            _update(service.reset_all(session_id))


# ---------------------------------------------------------------------------
# Main area -- kept in a wide-but-centered column so the page doesn't feel
# like a narrow strip lost in empty space on larger screens.
# ---------------------------------------------------------------------------

main_col = st.container()

with main_col:
    assets = Path(__file__).with_name("assets")
    def artwork(name):
        return "data:image/svg+xml;base64," + base64.b64encode((assets / name).read_bytes()).decode()
    st.html(f'<div class="ff-brand"><img class="ff-mark" src="{artwork("logo.svg")}" alt="" /> FocusFlow <span class="ff-brand-note">ONE SMALL STEP</span></div>')
    if not state.get("focus_mode") and not state.get("parked_tasks"):
        st.html(f'<div class="ff-art"><img src="{artwork("first-step.svg")}" alt="一条从小芽旁延伸的路径，沿途只有几个小小的落脚点" /></div>')
    if not state.get("focus_mode"):
        st.caption(t(lang, "product_promise"))

    if state.get("undo_snapshot"):
        if st.button(copy("撤销上一步操作", "Undo last action"), key="undo-action"):
            _update(service.undo_edit(state, session_id))

    if not state.get("focus_mode") and state.get("parked_tasks"):
        st.subheader(copy("接着上次这一点就好", "Pick up where you left off"))
        for index, task in enumerate(state["parked_tasks"]):
            with st.container(border=True):
                st.caption(task.get("current_goal", ""))
                st.write(task.get("current_step", ""))
                if task.get("resume_note"):
                    st.caption(task["resume_note"])
                if st.button(copy("接着来", "Pick it up"), key=f"restore-{index}"):
                    _update(service.restore_parked(state, index, session_id))

    if db.MULTI_SESSION:
        st.caption(copy("访客模式：离开前可在侧栏下载进度文件，下次上传找回。", "Guest mode: download a return file in the sidebar before leaving, then upload it next time."))

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
        if st.button(t(lang, "return_button"), type="primary", key="return-focus", use_container_width=True):
            _update(service.resume(state, session_id))
        if st.button(copy("保存到待接回，先做另一件事", "Save for later and do something else"), key="park-focus", use_container_width=True):
            _update(service.park_focus(state, session_id))

    elif state.get("focus_mode"):
        st.caption(t(lang, "focus_header"))
        st.markdown(t(lang, "focus_goal", goal=state.get("current_goal", "")))
        with st.container(border=False, key="focus-card"):
            st.caption(t(lang, "next_step_label"))
            st.subheader(state.get("current_step", ""))
            if state.get("completion_condition"):
                st.write(t(lang, "completion_condition", condition=state["completion_condition"]))
        if state.get("resume_note"):
            st.caption(t(lang, "return_note", note=state["resume_note"]))
        if response.get("type") == "interruption":
            if response.get("captured"):
                st.caption(t(lang, "interruption_captured"))
            else:
                st.caption(t(lang, "interruption_related"))
            if response.get("policy_downgraded"):
                st.caption(t(lang, "policy_kept_on_track", task=state.get("current_task", "")))
        elif response.get("type") == "step_split":
            st.caption(t(lang, "step_split_notice"))

        if st.button(t(lang, "done_button"), key="complete-step", type="primary", use_container_width=True):
            _update(service.mark_step_done(state, session_id))
        with st.expander(copy("这一步有点卡 / 换个做法", "I'm stuck / Try another way")):
            if st.button(t(lang, "split_button"), use_container_width=True):
                with st.spinner(copy("把这一步再缩小一点…", "Making this step smaller…")):
                    _update(service.split_current_step(state, session_id))
            reason = st.selectbox(copy("哪里不太合适？", "What is getting in the way?"),
                                  [copy("建议不适合，想自己改", "I'd like to edit this step"),
                                   copy("不知道怎么做", "I don't know how"),
                                   copy("缺材料，暂时做不了", "I'm missing something")], key="stuck-reason")
            if reason == copy("不知道怎么做", "I don't know how"):
                st.info(copy("可以把这一步改成：写下一个不懂的问题，再找一个例子。", "Try: write down one question, then find one example."))
            elif reason == copy("缺材料，暂时做不了", "I'm missing something"):
                st.info(copy("可以改成获取材料的具体动作，也可以先停一下，保存后去做别的事。", "Edit this into an action to get what you need, or pause and save it for later."))
            if reason != copy("建议不适合，想自己改", "I'd like to edit this step"):
                with st.form("prepare-step"):
                    missing = reason == copy("缺材料，暂时做不了", "I'm missing something")
                    detail = st.text_input(copy("缺少哪份材料？", "What resource is missing?") if missing else copy("具体哪一点不明白？", "What exactly is unclear?"))
                    st.caption(copy("先解决这个前提，再回到原步骤。已有进度会保留。", "Address this prerequisite, then return to the original step. Your progress stays intact."))
                    if st.form_submit_button(copy("先做这件小事", "Do this prerequisite first")):
                        if detail.strip():
                            _update(service.add_preparation_step(state, "missing" if missing else "how", detail, session_id))
                        st.warning(copy("写几个字就好。", "A few words are enough."))
            with st.form("edit-step"):
                action = st.text_input(copy("换成我能做的一步", "An action I can take"), value=state.get("current_step", ""))
                condition = st.text_input(copy("做到哪里就算完成（可不填）", "What counts as done? (optional)"), value=state.get("completion_condition", ""))
                if st.form_submit_button(copy("用这一步", "Use this step")):
                    if action.strip():
                        _update(service.edit_step(state, action, condition, session_id))
                    st.warning(copy("先写下一个动作。", "Enter an action first."))
            if st.button(copy("这一步已经做过了", "I've already done this step"), key="already-done"):
                _update(service.mark_step_done(state, session_id))

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
                _update(service.capture_thought(state, aside.strip(), session_id))

        completed = state.get("completed_steps", [])
        if completed:
            with st.expander(t(lang, "completed_header", n=len(completed))):
                for step in completed:
                    st.markdown(f"-  {step}")

        with st.expander(copy("时间参考 · 不用赶", "Time reference · No rush")):
            st.caption(t(lang, "focus_estimated", minutes=state.get("estimated_time", 5)))
            if st.toggle(t(lang, "show_timer"), value=False, key="show_timer"):
                _focus_timer(state.get("step_start_time", ""), state.get("estimated_time", 5), lang)

    elif response.get("type") == "task_complete":
        st.success(
            t(
                lang,
                "task_complete_message",
                task=response.get("current_task", ""),
                steps=response.get("steps_count", 0),
            )
        )
        with st.expander(copy("还想接着做这个任务？", "Continue with this goal?")):
            with st.form("continue-goal"):
                next_action = st.text_input(copy("接下来想做的一小步", "Your next small action"))
                if st.form_submit_button(copy("接着来", "Keep going")) and next_action.strip():
                    _update(service.continue_goal(state, next_action, session_id))
        st.caption(copy("今天先到这里也可以，已经做过的步骤会保留。", "You can stop here today. Your completed steps are saved."))
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
        if st.button(t(lang, "go_button"), key="begin-task", type="primary", use_container_width=True):
            if dump.strip():
                with st.spinner(copy("一起找一个能开始的地方…", "Finding a place to start…")):
                    _update(service.handle_message(state, dump.strip(), session_id))
            st.caption(t(lang, "input_placeholder"))
        st.caption(t(lang, "start_reassurance"))
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
            st.caption(copy("当前使用离线步骤模板，你可以随时修改不合适的建议。", "Using offline step templates. You can edit any suggestion."))
