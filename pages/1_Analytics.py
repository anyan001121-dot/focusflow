"""FocusFlow analytics -- local, single-user approximations of PRD section 10's metrics.

Everything here is computed from the same `events` and `preferences` tables
app.py already writes to (focusflow/db.py, focusflow/service.py). No new
tracking is added on this page; it only reads and summarizes.
"""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

import streamlit as st

from focusflow import db, service
from focusflow.i18n import t

st.set_page_config(page_title="FocusFlow -- Analytics", page_icon="📊", layout="centered")

db.init_db()

# See app.py: only matters in FOCUSFLOW_MULTI_SESSION mode (public demo).
session_id = st.session_state.setdefault("session_id", str(uuid.uuid4()))

state = st.session_state.get("ff_state") or service.load_or_new_state(session_id)
lang = state.get("lang", "en")

st.title(t(lang, "analytics_title"))
st.caption(t(lang, "analytics_caption"))

events = db.get_events(limit=5000, session_id=session_id)
prefs = db.load_preferences(session_id=session_id)

if not events:
    st.info(t(lang, "no_data_yet"))
    st.stop()

responses = [e["payload"].get("response", {}) for e in events]
now = datetime.now(timezone.utc)
week_ago = now - timedelta(days=7)


def _parsed_ts(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


starts_total = sum(1 for r in responses if r.get("type") == "focus_start")
completions_total = sum(1 for r in responses if r.get("type") == "task_complete")
interruptions_captured = sum(
    1 for r in responses if r.get("type") == "interruption" and r.get("captured")
)

completions_last_7d = sum(
    1
    for e, r in zip(events, responses)
    if r.get("type") == "task_complete" and (_parsed_ts(e["ts"]) or now) >= week_ago
)

abandonment_rate = None
if starts_total > 0:
    abandonment_rate = 1 - min(completions_total, starts_total) / starts_total

acceptance_rate = None
if prefs.get("breakdown_total", 0) > 0:
    acceptance_rate = 1 - prefs["breakdown_rejections"] / prefs["breakdown_total"]

avg_ratio = None
if prefs.get("estimate_ratio_count", 0) > 0:
    avg_ratio = prefs["estimate_ratio_sum"] / prefs["estimate_ratio_count"]

_LOAD_SCORES = {"easy": 1, "okay": 2, "hard": 3}
load_ratings = [
    e["payload"].get("rating") for e in events if e["event_type"] == "cognitive_load"
]
avg_load = None
if load_ratings:
    scores = [_LOAD_SCORES[r] for r in load_ratings if r in _LOAD_SCORES]
    if scores:
        avg_load = sum(scores) / len(scores)

col1, col2 = st.columns(2)
col1.metric(t(lang, "metric_north_star"), completions_last_7d)
col2.metric(
    t(lang, "metric_completion_rate"),
    f"{completions_total}/{starts_total}" if starts_total else "--",
)

col3, col4 = st.columns(2)
col3.metric(
    t(lang, "metric_abandonment_rate"),
    f"{abandonment_rate:.0%}" if abandonment_rate is not None else "--",
)
col4.metric(
    t(lang, "metric_acceptance_rate"),
    f"{acceptance_rate:.0%}" if acceptance_rate is not None else "--",
)

col5, col6 = st.columns(2)
col5.metric(
    t(lang, "metric_estimate_ratio"),
    f"{avg_ratio:.1f}x" if avg_ratio is not None else "--",
)
col6.metric(t(lang, "metric_interruptions"), interruptions_captured)

if avg_load is not None:
    st.metric(t(lang, "metric_cognitive_load"), f"{avg_load:.1f} / 3")

st.divider()
st.subheader(t(lang, "section_activity"))
activity_counts = Counter(e["event_type"] for e in events)
st.bar_chart(dict(activity_counts))
