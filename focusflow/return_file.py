"""Portable return points. Import only task data, never identity or executable content."""
from __future__ import annotations
import json
from datetime import datetime, timezone

MAX_BYTES = 256_000
TEXT_FIELDS = ('current_goal', 'current_task', 'current_step', 'completion_condition', 'resume_note')


def _text(value):
    if not isinstance(value, str) or len(value) > 8000:
        raise ValueError('Invalid text')
    return value


def _task(value):
    if not isinstance(value, dict):
        raise ValueError('Invalid task')
    task = {k: _text(value.get(k, '')) for k in TEXT_FIELDS}
    if not task['current_goal'].strip() or not task['current_step'].strip():
        raise ValueError('Missing return point')
    completed = value.get('completed_steps', [])
    queue = value.get('task_queue', [])
    if not isinstance(completed, list) or len(completed) > 200 or not isinstance(queue, list) or len(queue) > 100:
        raise ValueError('Too many steps')
    task['completed_steps'] = [_text(s) for s in completed]
    task['task_queue'] = []
    for step in queue:
        if not isinstance(step, dict):
            raise ValueError('Invalid step')
        task['task_queue'].append(dict(action=_text(step.get('action')), completion_condition=_text(step.get('completion_condition', '')), estimated_minutes=5))
    task.update(focus_mode=True, paused_at=datetime.now(timezone.utc).isoformat(),
                step_start_time='', estimated_time=5, next_action=task['current_step'])
    return task


def export_return_file(state):
    tasks = list(state.get('parked_tasks', []))
    if state.get('focus_mode') and state.get('current_step'):
        tasks = [state, *tasks]
    payload = {'format': 'focusflow-return', 'version': 1,
               'tasks': [_task(task) for task in tasks],
               'later_list': state.get('later_list', [])}
    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
    read_return_file(raw)  # Every exported file must also be importable.
    return raw


def read_return_file(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('File too large')
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict) or payload.get('format') != 'focusflow-return' or payload.get('version') != 1:
            raise ValueError('Unknown format')
        tasks, later = payload.get('tasks'), payload.get('later_list')
        if not isinstance(tasks, list) or len(tasks) > 50 or not isinstance(later, list) or len(later) > 200:
            raise ValueError('Invalid list')
        return {'parked_tasks': [_task(t) for t in tasks], 'later_list': [_text(t) for t in later]}
    except (TypeError, KeyError, UnicodeError, RecursionError) as exc:
        raise ValueError('Invalid return file') from exc
