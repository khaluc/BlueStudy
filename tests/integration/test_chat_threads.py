import json
import httpx
import pytest
from sqlalchemy import select
from apps.worker.tasks.chat_task import process_chat
from packages.db.models import ChatTurn


class Model:
    last_metadata = {'provider': 'test'}

    def ask(self, prompt):
        self.context = json.loads(prompt.split('\n', 1)[1])
        return 'Use since for a starting point.', 'test-model'


def test_chat_history_isolation_queue_and_delete(backend):
    client, sessions, a, b, *_ = backend
    assert client.get('/chat/threads').status_code == 401
    thread = client.post('/chat/threads', headers=a, json={}).json()
    path = '/chat/threads/' + thread['id']
    for method, suffix, body in [('GET', '', None), ('GET', '/turns', None),
                                  ('POST', '/turns', {'message': 'hello'}),
                                  ('PATCH', '', {}), ('DELETE', '', None)]:
        assert client.request(method, path+suffix, headers=b, json=body).status_code == 404
    assert client.get('/chat/threads', headers=b).json() == []
    assert client.post(path+'/turns', headers=a, json={'message': 'since or for?'}).status_code == 202
    assert client.post(path+'/turns', headers=a, json={'message': 'again'}).status_code == 409
    assert client.delete(path, headers=a).status_code == 409
    model = Model()
    assert process_chat(sessions, model)
    assert model.context['current_source'] is None
    assert model.context['recent_history'] == []
    rows = client.get(path+'/turns', headers=a).json()
    assert rows[0]['status'] == 'succeeded'
    assert rows[0]['provenance']['provider'] == 'test'
    client.post(path+'/turns', headers=a, json={'message': 'Give an example'})
    assert process_chat(sessions, model)
    assert model.context['recent_history'][0]['user'] == 'since or for?'
    assert not process_chat(sessions, model)
    assert client.delete(path, headers=a).status_code == 204
    with sessions() as db:
        assert db.scalar(select(ChatTurn)) is None


@pytest.mark.parametrize('message', ['', '   ', 'x'*1501, 'bad\x00input'])
def test_chat_validation(backend, message):
    client, _, a, *_ = backend
    thread = client.post('/chat/threads', headers=a, json={}).json()
    assert client.post('/chat/threads/'+thread['id']+'/turns', headers=a,
                       json={'message': message}).status_code == 422


def test_chat_source_switch_and_document_deletion(backend):
    client, sessions, a, b, *_ = backend
    doc = client.post('/documents', headers=a, json={'title': 'Source', 'text': 'Since 2020. For two days.'}).json()
    session = client.post('/sessions', headers=a, json={'document_id': doc['id']}).json()
    assert client.post('/chat/threads', headers=b, json={'session_id': session['id']}).status_code == 404
    thread = client.post('/chat/threads', headers=a, json={'session_id': session['id']}).json()
    path = '/chat/threads/'+thread['id']
    client.post(path+'/turns', headers=a, json={'message': 'Explain my notes'})
    model = Model()
    process_chat(sessions, model)
    assert model.context['current_source'] == doc['text']
    assert client.patch(path, headers=a, json={'session_id': None}).status_code == 200
    client.post(path+'/turns', headers=a, json={'message': 'A new question'})
    process_chat(sessions, model)
    assert model.context['recent_history'] == []
    assert model.context['current_source'] is None
    client.patch(path, headers=a, json={'session_id': session['id']})
    assert client.delete('/documents/'+doc['id'], headers=a).status_code == 204
    assert client.get(path, headers=a).json()['session_id'] is None


def test_chat_failure_sanitized_and_crash_retried(backend):
    client, sessions, a, *_ = backend
    thread = client.post('/chat/threads', headers=a, json={}).json()
    path = '/chat/threads/'+thread['id']+'/turns'
    client.post(path, headers=a, json={'message': 'Help'})
    class Crash:
        def ask(self, prompt):
            raise RuntimeError('secret')
    with pytest.raises(RuntimeError):
        process_chat(sessions, Crash())
    assert client.get(path, headers=a).json()[0]['status'] == 'queued'
    class Timeout:
        def ask(self, prompt):
            raise httpx.ReadTimeout('secret')
    process_chat(sessions, Timeout())
    response = client.get(path, headers=a)
    assert response.json()[0]['error_code'] == 'model_timeout'
    assert 'secret' not in response.text
