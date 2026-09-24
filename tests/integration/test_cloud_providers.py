import json
from PIL import Image
import httpx
import pytest
from fastapi.testclient import TestClient
from apps.chat.config import Settings
from apps.chat.main import create_app
from packages.llm.cloud_config import CloudSettings
from packages.ocr.vision_ocr import recognize
from packages.ocr.errors import ExtractionError


def sse(answer='Câu trả lời cloud.', reason='stop'):
    events = [
        {'choices': [{'delta': {'reasoning_content': 'PRIVATE THINKING'}, 'finish_reason': None}]},
        {'choices': [{'delta': {'content': answer}, 'finish_reason': None}]},
        {'choices': [{'delta': {}, 'finish_reason': reason}]},
        {'choices': [], 'usage': {'completion_tokens': 50}},
    ]
    return '\n\n'.join('data: ' + json.dumps(event) for event in events) + '\n\ndata: [DONE]\n\n'


def test_chat_uses_requested_endpoint_model_and_hides_reasoning():
    def handler(request):
        assert str(request.url) == 'https://maas.qwencloudapi.com/compatible-mode/v1/chat/completions'
        assert request.headers['Authorization'] == 'Bearer test-key'
        payload = json.loads(request.content)
        assert payload['model'] == 'qwen3.8-max-0902'
        assert payload['enable_thinking'] is True and payload['stream'] is True
        return httpx.Response(200, text=sse(), headers={'content-type': 'text/event-stream'})
    settings = Settings(_env_file=None, chat_provider='qwen_cloud', dashscope_api_key='test-key')
    with TestClient(create_app(settings, httpx.MockTransport(handler))) as client:
        response = client.post('/chat', json={'message': 'Xin chào'})
        assert response.status_code == 200
        assert response.json()['provider'] == 'qwen_cloud'
        assert response.json()['model'] == 'qwen3.8-max-0902'
        assert response.json()['answer'] == 'Câu trả lời cloud.'
        assert 'PRIVATE' not in response.text and 'test-key' not in response.text


@pytest.mark.parametrize('failure,code', [('auth','cloud_auth_error'), ('rate','cloud_rate_limit'),
    ('timeout','cloud_timeout'), ('truncated','cloud_incomplete_response'), ('malformed','cloud_invalid_response')])
def test_chat_fallback_is_explicit_and_key_never_goes_to_ollama(failure, code):
    calls = []
    def handler(request):
        calls.append(request.url.host)
        if request.url.host == 'maas.qwencloudapi.com':
            if failure == 'timeout':
                raise httpx.ReadTimeout('secret endpoint')
            if failure == 'truncated':
                return httpx.Response(200, text=sse('partial', 'length'))
            if failure == 'malformed':
                return httpx.Response(200, text='data: invalid\n\n')
            return httpx.Response(401 if failure == 'auth' else 429, text='secret upstream message')
        assert 'authorization' not in request.headers
        return httpx.Response(200, json={'done': True, 'message': {'content': 'Local answer'}})
    settings = Settings(_env_file=None, chat_provider='qwen_cloud', dashscope_api_key='test-key')
    with TestClient(create_app(settings, httpx.MockTransport(handler))) as client:
        response = client.post('/chat', json={'message': 'Xin chào'})
        assert response.status_code == 200
        assert response.json()['provider'] == 'ollama'
        assert response.json()['fallback_reason'] == code
        assert 'secret' not in response.text
    assert len(calls) == 2


def test_missing_key_does_not_send_network_request_when_fallback_disabled():
    settings = Settings(_env_file=None, chat_provider='qwen_cloud', local_fallback_enabled=False)
    def handler(request):
        pytest.fail('Missing key must not issue request')
    with TestClient(create_app(settings, httpx.MockTransport(handler))) as client:
        assert client.post('/chat', json={'message': 'hello'}).json()['detail'] == 'missing_api_key'
        assert client.get('/health/ready').status_code == 503


def test_vision_uses_image_and_returns_no_fake_confidence():
    def handler(request):
        payload = json.loads(request.content)
        assert request.url.host == '127.0.0.1' and request.url.path == '/api/chat'
        assert 'authorization' not in request.headers
        assert payload['model'] == 'qwen3-vl:2b-instruct-q8_0'
        assert payload['messages'][1]['images'][0]
        return httpx.Response(200, json={'done': True, 'message': {
            'content': 'Ghi chú tiếng Việt', 'thinking': 'PRIVATE'}})
    settings = CloudSettings(_env_file=None, vision_provider='ollama', dashscope_api_key='test-key')
    result = recognize(Image.new('RGB', (50, 50)), settings, httpx.MockTransport(handler))
    assert result['provider'] == 'ollama' and result['confidence'] is None
    assert result['text'] == 'Ghi chú tiếng Việt' and 'PRIVATE' not in str(result)


def test_vision_error_falls_back_and_can_be_disabled():
    settings = CloudSettings(_env_file=None, vision_provider='ollama')
    transport = httpx.MockTransport(lambda request: httpx.Response(503))
    def local(image):
        return {'text': 'Local OCR', 'method': 'ocr'}
    result = recognize(Image.new('RGB', (10, 10)), settings, transport, local=local)
    assert result['fallback_reason'] == 'vision_unavailable' and result['provider'] == 'tesseract'
    settings.local_fallback_enabled = False
    with pytest.raises(ExtractionError, match='vision_unavailable'):
        recognize(Image.new('RGB', (10, 10)), settings, transport, local=local)


def test_cloud_endpoint_requires_https():
    with pytest.raises(ValueError):
        CloudSettings(_env_file=None, qwen_base_url='http://example.com')


def test_bundle_has_separate_generation_budget_without_changing_chat():
    payloads=[]
    def handler(request):
        payloads.append(json.loads(request.content))
        return httpx.Response(200, text=sse('{}'))
    settings=Settings(_env_file=None, chat_provider='qwen_cloud', dashscope_api_key='test-key',
                      qwen_max_tokens=4096, qwen_enable_thinking=True)
    with TestClient(create_app(settings,httpx.MockTransport(handler))) as client:
        assert client.post('/chat',json={'message':'Create bundle','purpose':'study_bundle'}).status_code==200
        assert client.post('/chat',json={'message':'Explain source'}).status_code==200
        assert client.post('/chat',json={'message':'hello','purpose':'arbitrary'}).status_code==422
    assert payloads[0]['enable_thinking'] is False
    assert payloads[0]['max_tokens']==8192
    assert payloads[1]['enable_thinking'] is True
    assert payloads[1]['max_tokens']==4096
