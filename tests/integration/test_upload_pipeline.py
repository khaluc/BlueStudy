import hashlib
from io import BytesIO
import subprocess
from PIL import Image
import pytest
from apps.worker.tasks.ocr_task import process_upload
from packages.db.models import Document
from packages.storage.local import LocalStorage
from packages.ocr.errors import ExtractionError
from packages.ocr.extraction import extract
from packages.ocr.process import run_parser
from packages.ocr.validation import inspect_source, MAX_BYTES
from scripts.generate_test_data import text_pdf, blank_pdf, sample_files


@pytest.mark.parametrize('count',[11,20])
def test_accept_up_to_twenty_pages(count):
    assert inspect_source(blank_pdf(count))['page_count']==count


def test_page_limit_reports_actual_count(backend):
    client,_,headers,*_=backend
    response=client.post('/uploads',headers=headers,files={'file':('large.pdf',blank_pdf(21),'application/pdf')})
    assert response.status_code==422
    assert response.json()['detail']['code']=='page_limit'
    assert '21' in response.json()['detail']['message'] and '20' in response.json()['detail']['message']


def png_bytes():
    out = BytesIO()
    Image.new('RGB', (100, 100), 'white').save(out, format='PNG')
    return out.getvalue()


def upload(client, headers, data=None, name='note.pdf', mime='application/pdf'):
    return client.post('/uploads', headers=headers,
                       files={'file': (name, text_pdf() if data is None else data, mime)})


def test_pdf_upload_extract_review_confirm_and_snapshot(backend):
    client, sessions, a, b, settings, ids = backend
    raw = text_pdf()
    response = upload(client, a, raw)
    assert response.status_code == 202, response.text
    doc = response.json()
    doc_id = doc['id']
    assert doc['status'] == 'queued' and doc['sha256'] == hashlib.sha256(raw).hexdigest()
    assert client.post('/sessions', headers=a, json={'document_id': doc_id}).status_code == 409
    assert process_upload(sessions, LocalStorage(settings.storage_root))
    doc = client.get('/documents/' + doc_id, headers=a).json()
    assert doc['status'] == 'review_required'
    assert 'Since 2020' in doc['text']
    assert doc['pages'][0]['method'] == 'pdf_text'
    assert client.post('/sessions', headers=a, json={'document_id': doc_id}).status_code == 409
    # Reject stale edits and cross-user modifications.
    assert client.patch(f'/documents/{doc_id}/text', headers=a,
                        json={'text': 'wrong revision', 'expected_revision': 1}).status_code == 409
    for path in ['confirm', 'retry']:
        assert client.post(f'/documents/{doc_id}/{path}', headers=b,
                           json={'expected_revision': doc['revision']}).status_code == 404
    assert client.patch(f'/documents/{doc_id}/text', headers=b,
                        json={'text': 'other user', 'expected_revision': doc['revision']}).status_code == 404
    edited = client.patch(f'/documents/{doc_id}/text', headers=a,
                          json={'text': 'Since indicates a starting point.', 'expected_revision': doc['revision']}).json()
    assert edited['pages'] == doc['pages']  # Raw extraction remains available for comparison.
    assert client.post(f'/documents/{doc_id}/confirm', headers=a,
                       json={'expected_revision': doc['revision']}).status_code == 409
    assert client.post(f'/documents/{doc_id}/confirm', headers=a,
                       json={'expected_revision': edited['revision']}).status_code == 200
    session = client.post('/sessions', headers=a, json={'document_id': doc_id}).json()
    assert session['source_text'] == edited['text']
    client.patch(f'/documents/{doc_id}/text', headers=a,
                 json={'text': 'A newer draft.', 'expected_revision': edited['revision']}).raise_for_status()
    assert client.get('/sessions/' + session['id'], headers=a).json()['source_text'] == edited['text']
    source = client.get(f'/documents/{doc_id}/source', headers=a)
    assert source.content == raw and source.headers['content-type'] == 'application/pdf'
    assert client.get(f'/documents/{doc_id}/source', headers=b).status_code == 404
    assert client.delete('/documents/' + doc_id, headers=a).status_code == 204
    assert not list(settings.storage_root.iterdir())


@pytest.mark.parametrize('data,name,mime,code', [
    (b'', 'empty.pdf', 'application/pdf', 422),
    (b'%PDF-broken', 'broken.pdf', 'application/pdf', 422),
    (b'not image', 'note.jpg', 'image/jpeg', 422),
    (b'html', 'note.html', 'text/html', 415),
    (text_pdf(), 'wrong.png', 'image/png', 415),
    (text_pdf(), 'note.pdf', 'image/png', 415),
    (blank_pdf(21), 'large.pdf', 'application/pdf', 422),
    (blank_pdf(encrypted=True), 'locked.pdf', 'application/pdf', 422),
    (b'x' * (MAX_BYTES + 1), 'huge.pdf', 'application/pdf', 413),
], ids=['empty', 'broken-pdf', 'broken-image', 'unsupported', 'wrong-extension', 'wrong-mime', 'too-many-pages', 'encrypted', 'over-size'])
def test_bad_upload_rejected_without_saved_source(backend, data, name, mime, code):
    client, sessions, a, b, settings, ids = backend
    response = upload(client, a, data, name, mime)
    assert response.status_code == code, response.text
    assert client.get('/documents', headers=a).json() == []
    assert not list(settings.storage_root.iterdir())


def test_chunked_request_bound_before_full_multipart_parse(backend):
    client, sessions, a, b, settings, ids = backend
    def chunks():
        yield b'--test\r\nContent-Disposition: form-data; name="file"; filename="note.pdf"\r\nContent-Type: application/pdf\r\n\r\n'
        for _ in range(12):
            yield b'x' * (1024 * 1024)
        yield b'\r\n--test--\r\n'
    response = client.post('/uploads', headers={**a, 'Content-Type': 'multipart/form-data; boundary=test'}, content=chunks())
    assert response.status_code == 413


@pytest.mark.parametrize('error', ['ocr_timeout', 'ocr_unavailable', 'extraction_timeout'])
def test_ocr_failure_keeps_source_and_can_retry(backend, error):
    client, sessions, a, b, settings, ids = backend
    raw = png_bytes()
    doc = upload(client, a, raw, 'note.png', 'image/png').json()
    def failed(*args):
        raise ExtractionError(error)
    assert process_upload(sessions, LocalStorage(settings.storage_root), parser=failed)
    result = client.get('/documents/' + doc['id'], headers=a).json()
    assert result['status'] == 'failed' and result['extraction_error'] == error
    assert client.get('/documents/' + doc['id'] + '/source', headers=a).content == raw
    response = client.post('/documents/' + doc['id'] + '/retry', headers=a,
                           json={'expected_revision': result['revision']})
    assert response.status_code == 202 and response.json()['status'] == 'queued'


def test_empty_ocr_requires_manual_correction(backend):
    client, sessions, a, b, settings, ids = backend
    doc = upload(client, a, png_bytes(), 'note.png', 'image/png').json()
    def empty(*args):
        return {'text': '', 'pages': [{'page': 1, 'text': '', 'method': 'ocr', 'warnings': ['empty_page']}], 'page_count': 1}
    process_upload(sessions, LocalStorage(settings.storage_root), parser=empty)
    doc = client.get('/documents/' + doc['id'], headers=a).json()
    assert doc['status'] == 'failed' and doc['extraction_error'] == 'empty_text'
    assert client.post('/documents/' + doc['id'] + '/confirm', headers=a,
                       json={'expected_revision': doc['revision']}).status_code == 409
    response = client.patch('/documents/' + doc['id'] + '/text', headers=a,
                            json={'text': 'Manually transcribed.', 'expected_revision': doc['revision']})
    assert response.status_code == 200 and response.json()['status'] == 'review_required'


def test_long_document_requires_explicit_excerpt(backend):
    client, sessions, a, b, settings, ids = backend
    doc = client.post('/documents', headers=a, json={'title': 'Long', 'text': 'Initial.'}).json()
    draft = client.patch('/documents/' + doc['id'] + '/text', headers=a,
                          json={'text': 'word ' * 1000, 'expected_revision': 1}).json()
    client.post('/documents/' + doc['id'] + '/confirm', headers=a,
                json={'expected_revision': draft['revision']}).raise_for_status()
    assert client.post('/sessions', headers=a, json={'document_id': doc['id']}).status_code == 422
    response = client.post('/sessions', headers=a,
                           json={'document_id': doc['id'], 'start_offset': 0, 'end_offset': 1000})
    assert response.status_code == 201 and len(response.json()['source_text']) == 1000


def test_pdf_text_and_scan_are_selected_per_page():
    files = sample_files()
    calls = []
    def fake_ocr(image):
        calls.append(image.size)
        return {'text': 'Ảnh được nhận dạng', 'method': 'ocr', 'confidence': 80,
                'warnings': ['review_ocr'], 'low_confidence_words': []}
    result = extract(files['sample_mixed.pdf'], ocr=fake_ocr)
    assert [p['method'] for p in result['pages']] == ['pdf_text', 'ocr']
    assert len(calls) == 1 and 'Ảnh được nhận dạng' in result['text']


def test_parser_timeout_is_reported(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired('parser', 20)
    monkeypatch.setattr('packages.ocr.process.subprocess.run', timeout)
    with pytest.raises(ExtractionError, match='extraction_timeout'):
        run_parser(b'anything', 'inspect')


def test_image_size_bound():
    out = BytesIO()
    Image.new('1', (5000, 5000)).save(out, format='PNG')
    with pytest.raises(ExtractionError, match='20 megapixel'):
        inspect_source(out.getvalue())


def test_uploaded_filename_cannot_choose_storage_path(backend):
    client, sessions, a, b, settings, ids = backend
    response = upload(client, a, text_pdf(), '../../source.pdf', 'application/pdf')
    assert response.status_code == 202
    assert response.json()['source_name'] == 'source.pdf'
    files = list(settings.storage_root.iterdir())
    assert len(files) == 1 and files[0].name == response.json()['id'] + '.pdf'
