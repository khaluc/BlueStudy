"""Real model quiz, radio choices, server grading and persisted results in Chrome."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def main():
    thread = document = None
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        base='http://127.0.0.1:8000'
        try:
            page.goto(base+'/app/#chat')
            expect(page.locator('.chat-send')).to_be_enabled()
            doc=page.request.post(base+'/documents',data={'title':'Quiz smoke vocabulary','text':
                'environment (noun): môi trường. protect (verb): bảo vệ. '
                'protect the environment: bảo vệ môi trường. pollution (noun): ô nhiễm. '
                'We should protect the environment: Chúng ta nên bảo vệ môi trường.'}).json()
            document=doc['id']
            session=page.request.post(base+'/sessions',data={'document_id':document}).json()
            with page.expect_response(lambda r:r.url.endswith('/chat/threads') and r.request.method=='POST') as response:
                page.get_by_role('button',name='＋ Chat mới',exact=True).click()
            thread=response.value.json()['id']
            expect(page.locator('.chat-thread-select')).to_have_value(thread)
            assert page.request.patch(base+'/chat/threads/'+thread,data={'session_id':session['id']}).ok
            page.reload()
            expect(page.get_by_role('button',name='Bỏ đính kèm',exact=True)).to_be_visible()
            page.locator('.chat-compose-box textarea').fill('Tạo quiz về các từ trong ghi chú để mình chọn đáp án.')
            page.locator('.chat-send').click()
            expect(page.locator('.inline-quiz')).to_be_visible(timeout=240000)
            expect(page.locator('.inline-quiz-question')).to_have_count(5)
            expect(page.locator('.inline-quiz input[type=radio]')).to_have_count(20)
            rows=page.request.get(base+'/chat/threads/'+thread+'/turns').json()
            assert all('correct' not in q for q in rows[-1]['quiz']['questions'])
            assert all(stage['status']=='done' for stage in rows[-1]['provenance']['agent_trace'])
            expect(page.get_by_role('button',name='Nộp bài',exact=True)).to_be_disabled()
            for index in range(5):
                page.locator('.inline-quiz-question').nth(index).locator('input').nth(index%4).check()
            expect(page.get_by_role('button',name='Nộp bài',exact=True)).to_be_enabled()
            page.locator('.inline-quiz').scroll_into_view_if_needed()
            Path('data/benchmarks/design').mkdir(parents=True,exist_ok=True)
            page.screenshot(path='data/benchmarks/design/chat-inline-quiz.png',full_page=True)
            page.get_by_role('button',name='Nộp bài',exact=True).click()
            expect(page.locator('.quiz-saved')).to_be_visible()
            expect(page.locator('.quiz-explanation')).to_have_count(5)
            page.reload()
            expect(page.locator('.quiz-saved')).to_be_visible()
            expect(page.locator('.inline-quiz input').first).to_be_disabled()
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.locator('.inline-quiz').scroll_into_view_if_needed()
            page.screenshot(path='data/benchmarks/design/chat-inline-quiz-mobile.png',full_page=True)
            assert not errors,errors
            print('PASS: real generated quiz, 20 choices, hidden key, server score, explanations, reload and mobile.')
        finally:
            if thread:page.request.delete(base+'/chat/threads/'+thread)
            if document:page.request.delete(base+'/documents/'+document)
            browser.close()


if __name__=='__main__':
    main()
