"""Manual end-to-end smoke test through the same service layer app.py uses.

Not part of the pytest suite (no assertions needed there) -- this is a
one-off script to sanity-check the full user journey against a real
SQLite file, since browser automation isn't available in this environment.
Run: python tests/smoke_journey.py
"""

import os

os.environ["FOCUSFLOW_DB_PATH"] = "smoke_test.db"

from focusflow import db, service  # noqa: E402

db.init_db()
db.delete_all()

print("== Brain dump ==")
state = service.load_or_new_state()
state = service.handle_message(
    state,
    "I need to apply for jobs, fix my CV, prepare for an AI PM interview, go to the gym",
)
print(state["response"])
assert len(state["response"]["priorities"]) <= 3

print("\n== Start focus on a priority ==")
goal = state["response"]["priorities"][0]["task"]
state = service.start_focus(state, goal)
print("focus_mode:", state["focus_mode"])
print("current_step:", state["current_step"])
assert state["focus_mode"] is True

print("\n== Interruption ==")
state = service.handle_message(state, "I just remembered I need to buy detergent")
print(state["response"])
print("later_list:", state["later_list"])
assert "I just remembered I need to buy detergent" in state["later_list"]
assert state["focus_mode"] is True

print("\n== Mark step done ==")
state = service.mark_step_done(state)
print(state["response"])
print("completed_steps:", state["completed_steps"])

print("\n== Resume (simulating app restart) ==")
reloaded = service.load_or_new_state()
resumed = service.resume(reloaded)
print(resumed["response"])
assert resumed["response"]["has_active_task"] is True

print("\n== Reset ==")
service.reset_all()
assert db.load_state() is None

print("\nSMOKE TEST OK")
