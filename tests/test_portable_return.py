import json
import pytest
from focusflow import db, service
from focusflow.state import new_state
from focusflow.return_file import export_return_file, read_return_file

@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_PATH', str(tmp_path / 'portable.db'))
    monkeypatch.setattr(db, 'MULTI_SESSION', True)
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    db.init_db()


def test_return_file_restores_in_new_session_without_overwriting():
    a = service.start_focus(new_state(), 'Write thesis', 'a')
    a = service.mark_step_done(a, 'a')
    a = service.capture_thought(a, 'Buy milk', 'a')
    raw = export_return_file(a)
    assert 'undo_snapshot' not in raw.decode()
    b = service.start_focus(new_state(), 'Reply email', 'b')
    merged = service.import_return_file(b, raw, 'b')
    assert merged['current_step'] == b['current_step']
    assert len(merged['parked_tasks']) == 1
    again = service.import_return_file(merged, raw, 'b')
    assert len(again['parked_tasks']) == 1
    assert again['later_list'] == ['Buy milk']
    idle = service.park_focus(service.pause_focus(again, session_id='b'), 'b')
    restored = service.restore_parked(idle, 0, 'b')
    assert restored['current_step'] == a['current_step']
    assert restored['completed_steps'] == a['completed_steps']
    assert restored['step_start_time']
    assert service.load_or_new_state('a')['current_goal'] == 'Write thesis'


@pytest.mark.parametrize('raw', [b'[]', b'null', b'bad', b' ' * 256001,
    json.dumps({'format':'focusflow-return','version':1,'tasks':[{'current_goal':5}], 'later_list':[]}).encode()])
def test_invalid_import_does_not_write(raw):
    original = service.start_focus(new_state(), 'Write report', 'a')
    with pytest.raises(ValueError):
        service.import_return_file(original, raw, 'a')
    assert service.load_or_new_state('a')['current_step'] == original['current_step']


@pytest.mark.parametrize('reason', ['how','missing'])
def test_prerequisite_returns_to_original_step(reason):
    state = service.start_focus(dict(new_state(), lang='zh'), '写论文', 'a')
    prep = service.add_preparation_step(state, reason, '回归结果表', 'a')
    assert '回归结果表' in prep['current_step']
    assert prep['task_queue'][0]['action'] == state['current_step']
    assert prep['completed_steps'] == []
    assert service.undo_edit(prep, 'a')['current_step'] == state['current_step']
    advanced = service.mark_step_done(prep, 'a')
    assert advanced['current_step'] == state['current_step']
    assert advanced['task_queue'] == state['task_queue']


def test_prerequisite_ui_and_backup_controls(tmp_path, monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(db, 'MULTI_SESSION', False)
    app = AppTest.from_file(Path(__file__).parent.parent / 'app.py').run()
    assert len(app.get('download_button')) == 1
    assert len(app.get('file_uploader')) == 1
    app.text_area(key='brain_dump_input').set_value('Write thesis').run()
    app.button(key='begin-task').click().run()
    original = app.session_state['ff_state']['current_step']
    app.selectbox(key='stuck-reason').set_value("I'm missing something").run()
    next(x for x in app.text_input if x.label == 'What resource is missing?').set_value('results table')
    next(x for x in app.button if x.label == 'Do this prerequisite first').click().run()
    assert not app.exception
    assert 'results table' in app.session_state['ff_state']['current_step']
    assert app.session_state['ff_state']['task_queue'][0]['action'] == original
