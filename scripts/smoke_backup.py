"""Verify a nonempty DB/source backup without modifying any existing document."""
import json
from pathlib import Path
import httpx
from scripts.backup import main as backup
from scripts.verify_backup import main as verify


def main():
    credentials=json.loads(Path('data/local-demo.json').read_text(encoding='utf-8'))
    with httpx.Client(base_url='http://127.0.0.1:8000',headers={'Authorization':'Bearer '+credentials['token']},timeout=30) as client:
        response=client.post('/documents',json={'title':'Backup verification fixture','text':'A library lends books to the local community.'})
        response.raise_for_status();document_id=response.json()['id']
        try:
            verify(backup())
        finally:
            import time
            for _ in range(30):
                try:
                    client.delete('/documents/'+document_id).raise_for_status()
                    break
                except httpx.HTTPError:
                    time.sleep(1)
            else:
                raise RuntimeError('Could not clean up backup fixture after restart')


if __name__=='__main__':main()
