"""Import an explicitly selected local PDF and wait for durable exam processing."""
import argparse
import hashlib
import json
import time
from pathlib import Path
import httpx


def main(path):
    source=Path(path)
    data=source.read_bytes()
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=60) as client:
        client.post('/local-session').raise_for_status()
        digest=hashlib.sha256(data).hexdigest()
        docs=client.get('/documents?limit=100').json()
        doc=next((doc for doc in docs if doc.get('sha256')==digest),None)
        if doc is None:
            response=client.post('/uploads',files={'file':(source.name,data,'application/pdf')},data={'title':source.stem[:160]})
            response.raise_for_status();doc=response.json()
        response=client.post('/exams',json={'document_id':doc['id']})
        response.raise_for_status();exam=response.json()
        report=Path('data/benchmarks/imported-exam.json')
        report.parent.mkdir(parents=True,exist_ok=True)
        last=None
        for _ in range(450):
            response=client.get('/exams/'+exam['id']);response.raise_for_status();exam=response.json()
            report.write_text(json.dumps(exam,ensure_ascii=False,indent=2),encoding='utf-8')
            status=(exam['status'],exam['classified_count'])
            if status!=last:print('exam',exam['id'],'status',status,'error',exam['error_code'],flush=True);last=status
            if exam['status'] not in ('queued','analyzing'):break
            time.sleep(2)
        if exam['status']!='ready':raise SystemExit('Exam is not ready; inspect persisted status')
        assert len(exam['structure']['questions'])==len(exam['classification'])
        print('Ready:',len(exam['structure']['questions']),'questions;',len(exam['structure']['passages']),'shared passages',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('pdf');main(parser.parse_args().pdf)
