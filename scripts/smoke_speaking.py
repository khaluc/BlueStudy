"""Exercise actual mic capture/UI + live Qwen with a simulated AssemblyAI socket.

Run smoke_speaking_live.py separately to validate the external STT service.
No real user's voice is captured: Chrome's fake audio device is mandatory here.
"""
import json
import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
SAMPLE='I I think that research is important because it help people to understand problems. Um evidence supports a clear argument and allows us to compare different ideas before making a decision.'


def main():
    created=[]
    live='--live' in sys.argv
    with sync_playwright() as p:
        args=['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']
        if live:
            args.append('--use-file-for-fake-audio-capture='+str(ROOT/'data/benchmarks/speaking-test.wav'))
        browser=p.chromium.launch(channel='chrome',headless=True,args=args)
        page=browser.new_page(viewport={'width':1440,'height':1100},permissions=['microphone'])
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        frames=[]
        def socket(ws):
            ws.send(json.dumps({'type':'Begin','id':'test-stream'}))
            words=[dict(text=w,start=i*360+(1600 if i>=15 else 0),
                        end=i*360+250+(1600 if i>=15 else 0),confidence=.98)
                   for i,w in enumerate(SAMPLE.split())]
            def received(data):
                if isinstance(data,bytes):
                    assert len(data)==3200
                    frames.append(data)
                    if len(frames)%5==0:
                        ws.send(json.dumps({'type':'Turn','turn_order':0,'end_of_turn':False,
                                            'transcript':SAMPLE,'words':words}))
                elif json.loads(data).get('type')=='Terminate':
                    ws.send(json.dumps({'type':'Turn','turn_order':0,'end_of_turn':True,
                                        'transcript':SAMPLE,'words':words}))
                    ws.send(json.dumps({'type':'Termination'}))
            ws.on_message(received)
        if not live:
            page.route_web_socket('wss://streaming.assemblyai.com/**',socket)
            page.route('**/speaking/token',lambda route:route.fulfill(json={
                'token':'test-temporary-token','speech_model':'universal-3-5-pro'}))
        def configured(route):
            response=route.fetch()
            body=response.json();body['configured']=True
            route.fulfill(response=response,json=body)
        if not live:page.route('**/speaking/config',configured)
        try:
            page.goto('http://127.0.0.1:8000/app/#speaking')
            page.locator('[data-language=en]').click()
            page.get_by_text('Or practise a custom AI question',exact=True).click()
            with page.expect_response(lambda r:r.url.endswith('/speaking/sessions') and r.request.method=='POST') as result:
                page.get_by_role('button',name='Get an AI question',exact=True).click()
            session=result.value.json()['id'];created.append(session)
            expect(page.get_by_role('button',name='Start microphone',exact=True)).to_be_enabled(timeout=200000)
            for index in range(2):
                page.get_by_role('button',name='Start microphone' if index==0 else 'Speak again',exact=True).click()
                expect(page.locator('#speaking-transcript')).to_contain_text('research is important',timeout=60000)
                if live:
                    expect(page.locator('#speaking-transcript')).to_contain_text('decision',timeout=60000)
                page.get_by_role('button',name='Finish & analyse',exact=True).click()
                expect(page.locator('.speaking-attempt')).to_have_count(index+1,timeout=20000)
                deadline=time.monotonic()+200
                while time.monotonic()<deadline:
                    row=page.request.get('http://127.0.0.1:8000/speaking/sessions/'+session).json()
                    attempt=row['attempts'][-1]
                    if attempt['status']!='queued':break
                    page.wait_for_timeout(1500)
                if attempt['status']=='failed':
                    page.request.post('http://127.0.0.1:8000/speaking/sessions/'+session+'/attempts/'+attempt['id']+'/retry')
                    deadline=time.monotonic()+200
                    while time.monotonic()<deadline:
                        page.wait_for_timeout(1500)
                        attempt=page.request.get('http://127.0.0.1:8000/speaking/sessions/'+session).json()['attempts'][-1]
                        if attempt['status']!='queued':break
                assert attempt['status']=='ready',(attempt['status'],attempt['metrics'].get('coaching_error'),attempt['metrics'].get('invalid_fields'))
                assert attempt['coaching']['pronunciation']['score'] is None
                expect(page.locator('.speaking-scores')).to_have_count(index+1,timeout=10000)
            assert live or frames
            expect(page.get_by_text('Your progress on this question',exact=True)).to_be_visible()
            page.locator('[data-language=vi]').click()
            expect(page.get_by_text('Tiến bộ với câu hỏi này',exact=True)).to_be_visible()
            page.locator('[data-language=en]').click()
            page.reload()
            expect(page.locator('.speaking-attempt')).to_have_count(2)
            expect(page.locator('.speaking-scores')).to_have_count(2)
            Path('data/benchmarks/design').mkdir(parents=True,exist_ok=True)
            page.screenshot(path='data/benchmarks/design/speaking-studio.png',full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert not errors,errors
            print('PASS: '+('real AssemblyAI with synthetic speech' if live else 'fake mic PCM + simulated AssemblyAI')+', live Qwen question/coaching, two attempts, EN/TV, reload, mobile')
        finally:
            for session in created:page.request.delete('http://127.0.0.1:8000/speaking/sessions/'+session)
            browser.close()


if __name__=='__main__':main()
