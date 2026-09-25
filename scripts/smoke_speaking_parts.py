"""Live app/Qwen with synthetic mic + simulated AssemblyAI turns for UI regressions."""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def main():
    created=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=[
            '--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'])
        page=browser.new_page(viewport={'width':1440,'height':1000},permissions=['microphone'])
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        text='Um I I believe a local cinema is the best choice because the screen and sound make the movie enjoyable. A living room is cheaper but a garden depends on the weather.'
        words=[dict(text=w,start=i*400+(1700 if i>5 else 0),end=i*400+250+(1700 if i>5 else 0),confidence=.97)
               for i,w in enumerate(text.split())]
        frames=[]
        def socket(ws):
            ws.send(json.dumps({'type':'Begin'}))
            def received(data):
                if isinstance(data,bytes):
                    frames.append(data)
                    if len(frames)%5==0:
                        ws.send(json.dumps({'type':'Turn','turn_order':0,'transcript':text,'words':words,'end_of_turn':False}))
                elif json.loads(data).get('type')=='Terminate':
                    ws.send(json.dumps({'type':'Turn','turn_order':0,'transcript':text,'words':words,'end_of_turn':True}))
                    ws.send(json.dumps({'type':'Termination'}))
            ws.on_message(received)
        page.route_web_socket('wss://streaming.assemblyai.com/**',socket)
        page.route('**/speaking/token',lambda r:r.fulfill(json={'token':'test-token','speech_model':'universal-3-5-pro'}))
        try:
            page.goto('http://127.0.0.1:8000/app/#speaking')
            page.locator('[data-language=en]').click()
            expect(page.locator('#speaking-set-picker option')).to_have_count(16)
            with page.expect_response(lambda r:'/practice-sets/vstep-01/sessions' in r.url and r.request.method=='POST') as response:
                page.get_by_role('button',name='Open 3-part set',exact=True).click()
            rows=response.value.json();created.extend(r['id'] for r in rows)
            expect(page.get_by_role('heading',name='Morning Routines',exact=True)).to_be_visible()
            expect(page.locator('.speaking-model')).to_have_attribute('open','')
            # Verify listening invokes synthesis with the English sample.
            page.evaluate("() => {window.__spoken='';speechSynthesis.speak=(u)=>{window.__spoken=u.text};}")
            page.get_by_role('button',name='Listen to the full model',exact=True).click()
            assert 'six thirty' in page.evaluate('window.__spoken')
            page.get_by_role('button',name='Part 2 · Solution Discussion',exact=True).click()
            expect(page.get_by_text('My living room',exact=True)).to_be_visible()
            expect(page.get_by_text('A local cinema',exact=True)).to_be_visible()
            page.get_by_role('button',name='Start 1-minute preparation',exact=True).click()
            expect(page.locator('#speaking-prep-clock')).to_have_text('60 s')
            assert not frames
            page.get_by_role('button',name='Ready — start speaking',exact=True).click()
            expect(page.locator('#speaking-live-signals')).to_contain_text('Repeated word: 1',timeout=15000)
            expect(page.locator('#speaking-live-signals')).to_contain_text('Possible filler: 1')
            expect(page.locator('#speaking-live-signals')).to_contain_text('Pause: 1')
            page.get_by_role('button',name='Finish & analyse',exact=True).click()
            expect(page.locator('.speaking-attempt')).to_have_count(1,timeout=20000)
            expect(page.get_by_text('Word-sequence similarity to the sample:',exact=False)).to_be_visible()
            deadline=time.monotonic()+230
            while time.monotonic()<deadline:
                result=page.request.get('http://127.0.0.1:8000/speaking/sessions/'+rows[1]['id']).json()
                attempt=result['attempts'][0]
                if attempt['status']!='queued':break
                page.wait_for_timeout(1500)
            assert attempt['status']=='ready',attempt['metrics']
            assert attempt['coaching']['practice_mode']=='model'
            expect(page.locator('.speaking-scores')).to_have_count(1,timeout=10000)
            page.get_by_role('button',name='Part 3 · Topic Development',exact=True).click()
            expect(page.get_by_role('heading',name='Causes of Stress in the Modern Workplace')).to_be_visible()
            expect(page.locator('#speaking-clock')).to_contain_text('/ 240 s')
            page.locator('#speaking-practice-mode').select_option('independent')
            expect(page.locator('.speaking-model')).not_to_have_attribute('open','')
            page.locator('[data-language=vi]').click()
            expect(page.get_by_role('button',name='Bắt đầu chuẩn bị 1 phút',exact=True)).to_be_visible()
            page.locator('[data-language=en]').click()
            page.reload()
            expect(page.get_by_role('heading',name='Causes of Stress in the Modern Workplace')).to_be_visible()
            Path('data/benchmarks/design').mkdir(parents=True,exist_ok=True)
            page.screenshot(path='data/benchmarks/design/speaking-three-parts.png',full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert not errors,errors
            print('PASS: 16 sets, three parts, sample TTS, silent preparation, live signals, guided Qwen feedback, 4-minute Part 3, EN/TV, reload, mobile')
        finally:
            for id in created:page.request.delete('http://127.0.0.1:8000/speaking/sessions/'+id)
            browser.close()


if __name__=='__main__':main()
