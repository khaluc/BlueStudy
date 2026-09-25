import base64
import json
from io import BytesIO
import httpx
import pytest
from PIL import Image
from packages.llm.vision_chat import ask_image
from packages.llm.cloud_config import CloudSettings


@pytest.mark.parametrize('language,expected', [('en', 'English'), ('vi', 'Vietnamese')])
def test_multimodal_payload_contains_image_and_question(language, expected):
    image = BytesIO()
    Image.new('RGB',(32,32),'white').save(image,format='PNG')
    def handler(request):
        payload = json.loads(request.content)
        assert request.url.path == '/api/chat'
        assert payload['messages'][-1]['content'] == 'Explain this'
        assert base64.b64decode(payload['messages'][-1]['images'][0]).startswith(b'\x89PNG')
        assert payload['messages'][1]['content'] == 'Earlier question'
        assert f'in {expected}, even if' in payload['messages'][0]['content']
        assert 'preserve the original visible words' in payload['messages'][0]['content']
        return httpx.Response(200,json={'done':True,'message':{'content':'An image'}})
    answer, model = ask_image(image.getvalue(),'Explain this',
        [{'user':'Earlier question','assistant':'Earlier answer'}],
        settings=CloudSettings(_env_file=None),transport=httpx.MockTransport(handler),response_language=language)
    assert answer == 'An image'
    assert model == 'qwen3-vl:2b-instruct-q8_0'
