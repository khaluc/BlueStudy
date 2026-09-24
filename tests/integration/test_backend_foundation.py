from pathlib import Path
import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select, func

from apps.api.config import Settings
from apps.api.main import create_app
from apps.api.services.auth import provision_user
from apps.chat.agents.orchestrator import Orchestrator
from apps.worker.main import process_one
from packages.db.database import build_database
from packages.db.models import User, Document, StudySession, Job
from packages.storage.local import LocalStorage


def create_flow(client, headers):
    response = client.post('/documents', headers=headers,
                           json={'title': 'English notes', 'text': 'Use since for a starting point; for for a duration.'})
    assert response.status_code == 201
    document = response.json()
    response = client.post('/sessions', headers=headers, json={'document_id': document['id']})
    assert response.status_code == 201
    session = response.json()
    response = client.post(f"/sessions/{session['id']}/jobs", headers=headers, json={'kind': 'classify'})
    assert response.status_code == 202
    return document, session, response.json()


class FakeModel:
    def ask(self, prompt):
        return '{"category":"notes"}', 'test-model'


def test_flow_worker_persistence_and_delete_cascade(backend):
    client, sessions, a, b, settings, ids = backend
    assert client.get('/health/ready').status_code == 200
    document, session, job = create_flow(client, a)
    assert client.get(f"/documents/{document['id']}/source", headers=a).text == document['text']
    assert process_one(sessions, Orchestrator(FakeModel()))
    assert not process_one(sessions, Orchestrator(FakeModel()))
    result = client.get(f"/jobs/{job['id']}", headers=a).json()
    assert result['status'] == 'succeeded'
    assert result['result']['content']['category'] == 'notes'
    assert result['result']['source_document_id'] == document['id']
    assert result['result']['review_status'] == 'unreviewed'
    # A new app instance must see committed data.
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get(f"/jobs/{job['id']}", headers=a).json() == result
    assert client.delete(f"/documents/{document['id']}", headers=a).status_code == 204
    assert client.get(f"/jobs/{job['id']}", headers=a).status_code == 404
    assert client.get(f"/sessions/{session['id']}", headers=a).status_code == 404
    assert not list(settings.storage_root.glob('*.txt'))
    with sessions() as db:
        assert db.scalar(select(func.count()).select_from(Job)) == 0


def test_other_user_cannot_access_any_resource_or_enqueue(backend):
    client, sessions, a, b, settings, ids = backend
    document, session, job = create_flow(client, a)
    paths = [f"/documents/{document['id']}", f"/documents/{document['id']}/source",
             f"/sessions/{session['id']}", f"/sessions/{session['id']}/jobs", f"/jobs/{job['id']}"]
    for path in paths:
        assert client.get(path, headers=b).status_code == 404
    assert client.get('/documents', headers=b).json() == []
    assert client.delete(paths[0], headers=b).status_code == 404
    assert client.post('/sessions', headers=b, json={'document_id': document['id']}).status_code == 404
    assert client.post(paths[3], headers=b, json={'kind': 'classify'}).status_code == 404
    assert client.get(paths[0], headers=a).status_code == 200


def test_auth_and_profile_no_token_leak(backend):
    client, sessions, a, b, settings, ids = backend
    assert client.get('/documents').status_code == 401
    assert client.get('/users/me', headers={'Authorization': 'Bearer invalid'}).status_code == 401
    user = client.get('/users/me', headers=a).json()
    assert set(user) == {'id', 'display_name', 'language_level', 'learning_preference'}
    assert client.patch('/users/me', headers=a, json={
        'display_name': 'Updated', 'language_level': 'support', 'id': ids[1]}).status_code == 422
    assert client.patch('/users/me', headers=a, json={
        'display_name': 'Updated', 'language_level': 'support'}).status_code == 200
    assert client.get('/users/me', headers=b).json()['display_name'] == 'Learner B'
    with sessions() as db:
        assert db.get(User, ids[0]).token_hash != a['Authorization'].removeprefix('Bearer ')


def test_invalid_requests(backend):
    client, sessions, a, b, settings, ids = backend
    for payload in [ {'title': '  ', 'text': 'x'}, {'title': 'x', 'text': ' '},
                     {'title': 'x', 'text': 'x' * 2401},
                     {'title': 'x', 'text': 'x', 'owner_id': ids[1]} ]:
        assert client.post('/documents', headers=a, json=payload).status_code == 422
    document, session, job = create_flow(client, a)
    for payload in [{'kind': 'delete'}, {'kind': 'teach'}, {'kind': 'teach', 'question': ' '},
                    {'kind': 'classify', 'question': 'unexpected'}]:
        assert client.post(f"/sessions/{session['id']}/jobs", headers=a, json=payload).status_code == 422


@pytest.mark.parametrize('failure,code', [('json', 'invalid_model_output'),
    ('category', 'invalid_model_output'), ('timeout', 'model_timeout'), ('network', 'model_unavailable')])
def test_failure_is_persisted_without_backend_secrets(backend, failure, code):
    client, sessions, a, b, settings, ids = backend
    document, session, job = create_flow(client, a)
    class BrokenModel:
        def ask(self, prompt):
            if failure == 'timeout':
                raise httpx.ReadTimeout('secret')
            if failure == 'network':
                raise httpx.ConnectError('secret')
            return ('not json' if failure == 'json' else '{"category":"invented"}'), 'fake'
    assert process_one(sessions, Orchestrator(BrokenModel()))
    response = client.get(f"/jobs/{job['id']}", headers=a)
    assert response.json()['status'] == 'failed'
    assert response.json()['error_code'] == code
    assert response.json()['result'] is None
    assert 'secret' not in response.text


def test_unexpected_crash_rolls_back_and_allows_retry(backend):
    client, sessions, a, b, settings, ids = backend
    document, session, job = create_flow(client, a)
    class CrashedModel:
        def ask(self, prompt):
            raise RuntimeError('simulated worker crash')
    with pytest.raises(RuntimeError):
        process_one(sessions, Orchestrator(CrashedModel()))
    assert client.get(f"/jobs/{job['id']}", headers=a).json()['status'] == 'queued'
    assert process_one(sessions, Orchestrator(FakeModel()))


def test_worker_rechecks_ownership(backend):
    client, sessions, a, b, settings, ids = backend
    document, session, job = create_flow(client, a)
    with sessions.begin() as db:
        db.get(Job, job['id']).owner_id = ids[1]
    class NeverCalled:
        def run(self, *args):
            pytest.fail('Cross-user job reached model')
    assert process_one(sessions, NeverCalled())
    with sessions() as db:
        assert db.get(Job, job['id']).error_code == 'invalid_ownership'


def test_teaching_uses_source_and_marks_unreviewed(backend):
    client, sessions, a, b, settings, ids = backend
    document, session, job = create_flow(client, a)
    process_one(sessions, Orchestrator(FakeModel()))
    class TeachingModel:
        def ask(self, prompt):
            assert document['text'] in prompt
            assert 'How to use since?' in prompt
            return 'Since chỉ mốc thời gian.', 'fake'
    response = client.post(f"/sessions/{session['id']}/jobs", headers=a,
                           json={'kind': 'teach', 'question': 'How to use since?'})
    assert response.status_code == 202
    assert process_one(sessions, Orchestrator(TeachingModel()))
    result = client.get('/jobs/' + response.json()['id'], headers=a).json()['result']
    assert result['review_status'] == 'unreviewed'
    assert result['content']['answer'] == 'Since chỉ mốc thời gian.'


@pytest.mark.parametrize('key', ['../secret.txt', '/tmp/secret.txt', 'bad.txt', 'bad.pdf'])
def test_storage_rejects_paths(tmp_path, key):
    storage = LocalStorage(tmp_path)
    with pytest.raises(ValueError):
        storage.read(key)
