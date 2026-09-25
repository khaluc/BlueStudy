"""Inline microphone placement using synthetic capture and a simulated STT socket."""
import json
from playwright.sync_api import sync_playwright,expect


def main():
    created=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=[
            '--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'])
        page=browser.new_page(viewport={'width':1440,'height':1000},permissions=['microphone'])
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/speaking/token',lambda r:r.fulfill(json={'token':'test','speech_model':'universal-3-5-pro'}))
        def socket(ws):
            ws.send(json.dumps({'type':'Begin'}))
            def received(data):
                if isinstance(data,bytes):
                    ws.send(json.dumps({'type':'Turn','turn_order':0,'transcript':'I enjoy going out.',
                        'words':[{'text':'I','start':0,'end':100},{'text':'enjoy','start':100,'end':300},
                                 {'text':'going','start':300,'end':500},{'text':'out','start':500,'end':700}]}))
            ws.on_message(received)
        page.route_web_socket('wss://streaming.assemblyai.com/**',socket)
        try:
            page.goto('http://127.0.0.1:8000/app/#speaking')
            page.locator('[data-language=en]').click()
            page.locator('#speaking-set-picker').select_option('vstep-02')
            with page.expect_response(lambda r:'/practice-sets/vstep-02/sessions' in r.url and r.request.method=='POST') as response:
                page.get_by_role('button',name='Open 3-part set',exact=True).click()
            created=[s['id'] for s in response.value.json()]
            expect(page.locator('.speaking-sample-segment')).to_have_count(6)
            expect(page.locator('.speaking-question')).to_have_count(0)
            expect(page.locator('.speaking-recorder')).to_have_count(0)
            target=page.locator('.speaking-sample-segment').nth(1)
            target.get_by_role('button',name='Start speaking',exact=True).click()
            expect(target.locator('.speaking-recorder')).to_have_count(1)
            expect(target.locator('#speaking-transcript')).to_contain_text('I enjoy going out.',timeout=15000)
            expect(target.locator('#speaking-script-live .speaking-script-board')).to_have_count(1)
            expect(target.locator('.script-token.matched').first).to_be_visible()
            alignment=page.evaluate("""() => {
              const words=text=>text.split(' ').map(text=>({text}));
              return {
                partial:speakingAlignment('I enjoy reading books',words('I enjoy')),
                final:speakingAlignment('I enjoy reading books',words('I enjoy'),true),
                mismatch:speakingAlignment('I enjoy reading books',words('I enjoy selling books'),true),
                repeat:speakingAlignment('I enjoy books',words('I enjoy enjoy books'),true),
                revised:speakingAlignment('I enjoy books',words('I enjoy books'))
              };
            }""")
            assert [t['state'] for t in alignment['partial']['tokens']]==['matched','matched','pending','pending']
            assert [t['state'] for t in alignment['final']['tokens']]==['matched','matched','missing','missing']
            assert alignment['mismatch']['tokens'][2]['state']=='different'
            assert len(alignment['repeat']['extras'])==1
            assert all(t['state']=='matched' for t in alignment['revised']['tokens'])
            expect(target.locator('#speaking-clock')).to_contain_text('/ 60 s')
            target.get_by_role('button',name='Cancel recording',exact=True).click()
            page.locator('[data-practice-mode=independent]').click()
            expect(page.locator('.speaking-sample-segment')).to_have_count(0)
            expect(page.locator('.speaking-model')).to_have_count(0)
            expect(page.locator('.speaking-question')).to_have_count(6)
            expect(page.locator('.speaking-recorder')).to_have_count(0)
            page.get_by_role('button',name='Answer this question',exact=True).nth(2).click()
            expect(page.locator('.speaking-question').nth(2).locator('.speaking-recorder')).to_have_count(1)
            expect(page.locator('#speaking-transcript')).to_contain_text('I enjoy going out.',timeout=15000)
            page.get_by_role('button',name='Cancel recording',exact=True).click()
            expect(page.locator('.speaking-page > .card > .speaking-recorder')).to_have_count(0)
            page.get_by_role('button',name='Part 2 · Solution Discussion',exact=True).click()
            expect(page.get_by_role('heading',name='Part 2 · Solution Discussion',exact=True)).to_be_visible()
            expect(page.locator('.speaking-recorder')).to_have_count(0)
            page.get_by_role('button',name='Answer this question',exact=True).click()
            expect(page.locator('.speaking-question .speaking-recorder')).to_have_count(1)
            page.get_by_role('button',name='Cancel preparation',exact=True).click()
            page.get_by_role('button',name='Part 1 · Social Interaction',exact=True).click()
            expect(page.get_by_role('heading',name='Part 1 · Social Interaction',exact=True)).to_be_visible()
            page.locator('[data-language=vi]').click()
            expect(page.get_by_role('button',name='Trả lời câu này',exact=True)).to_have_count(6)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert not errors,errors
            print('PASS: recording beside the chosen sample/question, 60-second scope, live transcript, EN/TV and mobile')
        finally:
            for id in created:page.request.delete('http://127.0.0.1:8000/speaking/sessions/'+id)
            browser.close()


if __name__=='__main__':main()
