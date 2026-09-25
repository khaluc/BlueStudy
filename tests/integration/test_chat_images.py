from io import BytesIO
from PIL import Image
import pytest
from apps.worker.tasks.chat_task import process_chat
from packages.storage.local import LocalStorage


@pytest.mark.parametrize('language', ['en', 'vi'])
def test_direct_image_no_review_and_owner_isolation(backend, language):
    client, sessions, a, b, settings, *_ = backend
    data = BytesIO()
    Image.new('RGB', (64,64), 'white').save(data, format='PNG')
    response = client.post('/uploads', headers=a, data={'purpose':'chat_image'},
                           files={'file':('photo.png',data.getvalue(),'image/png')})
    assert response.status_code == 202
    doc = response.json()
    assert doc['status'] == 'review_required' and doc['text'] == ''
    def thread(headers):
        return '/chat/threads/'+client.post('/chat/threads',headers=headers,json={}).json()['id']+'/turns'
    path, other = thread(a), thread(b)
    payload = {'message':'What is in this image?', 'image_document_id':doc['id'], 'response_language':language}
    assert client.post(other,headers=b,json=payload).status_code == 404
    assert client.post(path,headers=a,json=payload).status_code == 202
    class NoCloud:
        def ask(self, prompt):
            raise AssertionError('Must send actual image to local vision')
    def vision(image, question, history, response_language='vi'):
        assert image == data.getvalue()
        assert question == payload['message']
        assert response_language == language
        return 'A white image.', 'test-vision'
    process_chat(sessions,NoCloud(),LocalStorage(settings.storage_root),vision)
    turn = client.get(path,headers=a).json()[0]
    assert turn['answer'] == 'A white image.'
    assert turn['image_document_id'] == doc['id']
    assert turn['provenance']['provider'] == 'ollama'
    assert turn['provenance']['fallback_reason'] is None
    assert turn['provenance']['response_language'] == language
    client.post(path,headers=a,json=payload)
    client.delete('/documents/'+doc['id'],headers=a)
    process_chat(sessions,NoCloud(),LocalStorage(settings.storage_root),vision)
    assert client.get(path,headers=a).json()[-1]['error_code'] == 'image_missing'


def test_text_document_cannot_be_sent_as_image(backend):
    client, _, a, *_ = backend
    doc = client.post('/documents',headers=a,json={'title':'Text','text':'Some notes'}).json()
    tid = client.post('/chat/threads',headers=a,json={}).json()['id']
    assert client.post('/chat/threads/'+tid+'/turns',headers=a,json={
        'message':'Read','image_document_id':doc['id']}).status_code == 422
