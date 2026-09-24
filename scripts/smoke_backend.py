"""Run inside the API container. Creates isolated users and cleans them up."""
import json
import time
import httpx
from sqlalchemy import delete
from apps.api.config import Settings
from apps.api.services.auth import provision_user
from packages.db.database import build_database
from packages.db.models import User


def main():
    engine, sessions = build_database(Settings().database_url)
    with sessions.begin() as db:
        a, token_a = provision_user(db, 'Smoke A')
        b, token_b = provision_user(db, 'Smoke B')
        ids = [a.id, b.id]
    headers_a = {'Authorization': 'Bearer ' + token_a}
    headers_b = {'Authorization': 'Bearer ' + token_b}
    document_id = None
    report = {'backend': 'PostgreSQL + Docker worker + live Ollama', 'jobs': []}
    with httpx.Client(base_url='http://api:8000', timeout=150, trust_env=False) as client:
        try:
            client.get('/health/ready').raise_for_status()
            assert client.get('/users/me').status_code == 401
            response = client.post('/documents', headers=headers_a, json={
                'title': 'Since and for — smoke test',
                'text': 'Since introduces a starting point: since 2020. For introduces a duration: for two years. I have lived here since 2020. I have studied English for two years.',
            })
            response.raise_for_status()
            document = response.json()
            document_id = document['id']
            assert client.get('/documents/' + document_id, headers=headers_b).status_code == 404
            assert client.get('/documents/' + document_id + '/source', headers=headers_a).text == document['text']
            response = client.post('/sessions', headers=headers_a, json={'document_id': document_id})
            response.raise_for_status()
            session_id = response.json()['id']
            for task in [{'kind': 'classify'}, {'kind': 'teach', 'question': 'Giải thích since và for theo ghi chú.'}]:
                response = client.post(f'/sessions/{session_id}/jobs', headers=headers_a, json=task)
                response.raise_for_status()
                job_id = response.json()['id']
                assert client.get('/jobs/' + job_id, headers=headers_b).status_code == 404
                deadline = time.monotonic() + 150
                while time.monotonic() < deadline:
                    response = client.get('/jobs/' + job_id, headers=headers_a)
                    response.raise_for_status()
                    job = response.json()
                    if job['status'] != 'queued':
                        break
                    time.sleep(1)
                report['jobs'].append(job)
                assert job['status'] == 'succeeded', job.get('error_code')
                assert job['result']['source_document_id'] == document_id
                assert job['result']['review_status'] == 'unreviewed'
            assert client.delete('/documents/' + document_id, headers=headers_a).status_code == 204
            assert client.get('/jobs/' + job_id, headers=headers_a).status_code == 404
            assert client.get('/sessions/' + session_id, headers=headers_a).status_code == 404
            report['ownership_and_delete_cascade'] = 'passed'
            print(json.dumps(report, ensure_ascii=False, indent=2))
        finally:
            if document_id:
                response = client.delete('/documents/' + document_id, headers=headers_a)
                if response.status_code not in (204, 404):
                    response.raise_for_status()
            with sessions.begin() as db:
                db.execute(delete(User).where(User.id.in_(ids)))
            engine.dispose()


if __name__ == '__main__':
    main()
