"""One bounded live generation; never prints tokens or provider credentials."""
import json
import time
from pathlib import Path
import httpx


def main():
    credentials=json.loads(Path('data/local-demo.json').read_text(encoding='utf-8'))
    with httpx.Client(base_url='http://127.0.0.1:8000', headers={'Authorization':'Bearer '+credentials['token']}, timeout=30) as client:
        document_id=None
        try:
            response=client.post('/documents',json={'title':'Live study verification', 'text':
                'In our local community, volunteers help older neighbours. The library lends books for free. '
                'A firefighter puts out fires. A gardener plants trees in the public park. '
                'People take the bus to reduce traffic. Students clean the park every Sunday.'})
            response.raise_for_status();document_id=response.json()['id']
            response=client.post('/sessions',json={'document_id':document_id})
            response.raise_for_status();session_id=response.json()['id']
            response=client.post('/sessions/'+session_id+'/jobs',json={'kind':'generate_bundle'})
            response.raise_for_status();job_id=response.json()['id']
            for _ in range(150):
                result=client.get('/jobs/'+job_id).json()
                if result['status']!='queued':break
                time.sleep(2)
            if result['status']!='succeeded':
                raise SystemExit('Generation failed: '+str(result.get('error_code') or result['status']))
            mid=result['result']['material_id']
            public=client.get('/materials/'+mid);public.raise_for_status()
            assert '"correct"' not in public.text
            attempt=client.post('/materials/'+mid+'/attempts',json={'answers':[0,1,2,3,0]})
            attempt.raise_for_status()
            progress=client.get('/users/me/progress');progress.raise_for_status()
            output={'provider':result['result']['provider'],'fallback_reason':result['result']['fallback_reason'],
                    'model':result['result']['model'],'material':public.json(), 'assessment':attempt.json(),
                    'progress_saved':any(x['id']==attempt.json()['id'] for x in progress.json()['attempts'])}
            target=Path('data/benchmarks/live-study.json');target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({key:output[key] for key in ('provider','fallback_reason','model','progress_saved')}))
            print('Live study flow passed; output saved for quality review.')
        finally:
            if document_id:
                response=client.delete('/documents/'+document_id)
                response.raise_for_status()


if __name__=='__main__':main()
