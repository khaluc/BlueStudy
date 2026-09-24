import json

import httpx
import pytest
from fastapi.testclient import TestClient

from apps.chat.config import Settings
from apps.chat.main import create_app


def client(handler):
    return TestClient(create_app(Settings(_env_file=None), httpx.MockTransport(handler)))


def test_chat_sends_system_prompt_and_keeps_only_answer():
    def handler(request):
        payload = json.loads(request.content)
        assert payload['model'] == 'gemma4:e2b'
        assert payload['stream'] is False
        assert payload['messages'][0]['role'] == 'system'
        assert payload['messages'][1]['content'] == 'Xin chào'
        return httpx.Response(200, json={'done': True, 'message': {
            'content': 'Chào bạn!', 'thinking': 'private'}})
    with client(handler) as app:
        response = app.post('/chat', json={'message': ' Xin chào '})
        assert response.status_code == 200
        assert response.json() == {'answer': 'Chào bạn!', 'model': 'gemma4:e2b',
                                   'provider': 'ollama', 'fallback_reason': None}


@pytest.mark.parametrize('message', ['', '   ', 'x' * 8001])
def test_invalid_input_does_not_call_model(message):
    def handler(request):
        pytest.fail('Invalid input reached model')
    with client(handler) as app:
        assert app.post('/chat', json={'message': message}).status_code == 422


@pytest.mark.parametrize('failure,expected', [('timeout', 504), ('connection', 503),
                                             ('missing', 503), ('invalid', 502),
                                             ('empty', 502), ('truncated', 502)])
def test_model_failures(failure, expected):
    def handler(request):
        if failure == 'timeout':
            raise httpx.ReadTimeout('secret backend address', request=request)
        if failure == 'connection':
            raise httpx.ConnectError('secret backend address', request=request)
        if failure == 'missing':
            return httpx.Response(404, text='secret backend address')
        if failure == 'invalid':
            return httpx.Response(200, text='not json')
        return httpx.Response(200, json={'done': True,
            'done_reason': 'length' if failure == 'truncated' else 'stop',
            'message': {'content': 'partial' if failure == 'truncated' else ''}})
    with client(handler) as app:
        response = app.post('/chat', json={'message': 'Giải thích giúp em'})
        assert response.status_code == expected
        assert 'secret' not in response.text


@pytest.mark.parametrize('models,expected', [([], 503),
    ([{'name': 'other:model'}], 503), ([{'name': 'gemma4:e2b'}], 200)])
def test_readiness_checks_configured_model(models, expected):
    with client(lambda request: httpx.Response(200, json={'models': models})) as app:
        assert app.get('/health/live').status_code == 200
        assert app.get('/health/ready').status_code == expected
