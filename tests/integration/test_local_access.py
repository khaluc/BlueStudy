import json
from fastapi.testclient import TestClient
from apps.api.main import create_app


def test_local_session_preserves_user_and_blocks_other_origins(backend, tmp_path):
    _, _, headers, _, settings, ids = backend
    path = tmp_path / 'access.json'
    path.write_text(json.dumps({'token': headers['Authorization'].split()[1]}))
    settings.local_access_file = path
    with TestClient(create_app(settings)) as client:
        assert client.get('/users/me').status_code == 401
        assert client.post('/local-session', headers={'Origin':'https://other.test'}).status_code == 403
        result = client.post('/local-session')
        assert result.json() == {'mode':'local'}
        assert 'httponly' in result.headers['set-cookie'].lower()
        assert client.get('/users/me').json()['id'] == ids[0]
        assert client.get('/users/me', headers={'Sec-Fetch-Site':'cross-site'}).status_code == 403
        assert client.post('/chat/threads', json={}).status_code == 201


def test_local_session_disabled_by_default(backend):
    assert backend[0].post('/local-session').status_code == 404
