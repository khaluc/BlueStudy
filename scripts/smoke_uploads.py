"""Host smoke test through API and the real Docker/Ollama OCR worker."""
import hashlib
import json
from pathlib import Path
import time
import httpx
from scripts.generate_test_data import sample_files


def main():
    credentials = json.loads(Path('data/local-demo.json').read_text(encoding='utf-8'))
    headers = {'Authorization': 'Bearer ' + credentials['token']}
    report = []
    created = []
    with httpx.Client(base_url='http://127.0.0.1:8000', headers=headers, timeout=150, trust_env=False) as client:
        client.get('/health/ready').raise_for_status()
        try:
            for name, content in sample_files().items():
                mime = 'application/pdf' if name.endswith('.pdf') else ('image/png' if name.endswith('.png') else 'image/jpeg')
                response = client.post('/uploads', files={'file': (name, content, mime)})
                response.raise_for_status()
                document = response.json()
                doc_id = document['id']
                created.append(doc_id)
                assert document['sha256'] == hashlib.sha256(content).hexdigest()
                assert client.post('/sessions', json={'document_id': doc_id}).status_code == 409
                started = time.monotonic()
                while time.monotonic() - started < 180:
                    document = client.get('/documents/' + doc_id).json()
                    if document['status'] != 'queued':
                        break
                    time.sleep(1)
                assert document['status'] == 'review_required', (name, document.get('extraction_error'))
                assert 'since' in document['text'].lower(), document['text']
                assert client.get('/documents/' + doc_id + '/source').content == content
                if name.endswith(('.png', '.jpg')) or name == 'sample_scan.pdf':
                    assert document['pages'][0]['provider'] == 'ollama', document['pages']
                confirmation = client.post('/documents/' + doc_id + '/confirm',
                                           json={'expected_revision': document['revision']})
                confirmation.raise_for_status()
                session = client.post('/sessions', json={'document_id': doc_id})
                session.raise_for_status()
                report.append({'name': name, 'seconds': round(time.monotonic() - started, 2),
                               'text': document['text'], 'pages': document['pages'],
                               'source_verified': True, 'confirmed_session': True})
                print('PASS: ' + name, flush=True)
        finally:
            for doc_id in created:
                response = client.delete('/documents/' + doc_id)
                response.raise_for_status()
    output = Path('data/benchmarks/phase4-uploads.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(output)


if __name__ == '__main__':
    main()
