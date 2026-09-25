"""Real local vision reply from an image selected in the chat composer."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from scripts.generate_test_data import sample_files


def main():
    thread = document = None
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width':1440,'height':1000})
        errors = []
        page.on('pageerror',lambda e:errors.append(str(e)))
        try:
            page.goto('http://127.0.0.1:8000/app/#chat')
            expect(page.locator('.chat-send')).to_be_enabled()
            with page.expect_response(lambda r:r.url.endswith('/chat/threads') and r.request.method=='POST') as response:
                page.get_by_role('button',name='＋ Chat mới',exact=True).click()
            thread = response.value.json()['id']
            expect(page.locator('.chat-thread-select')).to_have_value(thread)
            with page.expect_response(lambda r:r.url.endswith('/uploads') and r.request.method=='POST') as response:
                page.locator('input[type=file]').set_input_files({'name':'direct-image.png','mimeType':'image/png',
                    'buffer':sample_files()['sample_note_image.png']})
            document = response.value.json()['id']
            expect(page.locator('.chat-attachment-preview')).to_be_visible()
            expect(page.get_by_role('button',name='Kiểm tra văn bản',exact=True)).to_have_count(0)
            page.locator('.chat-compose-box textarea').fill('Đọc ảnh và giải thích ngắn cách dùng since và for.')
            page.locator('.chat-send').click()
            expect(page.locator('.chat-attachment-preview')).to_have_count(0)
            expect(page.locator('.quiz-shortcut')).to_have_count(0)
            expect(page.locator('.chat-bubble.assistant')).to_have_count(1,timeout=150000)
            rows = page.request.get('http://127.0.0.1:8000/chat/threads/'+thread+'/turns').json()
            assert rows[0]['image_document_id'] == document
            assert rows[0]['provenance']['provider'] == 'ollama'
            assert rows[0]['provenance']['input_kind'] == 'image'
            assert rows[0]['provenance']['fallback_reason'] is None
            assert 'since' in rows[0]['answer'].lower()
            page.reload()
            expect(page.locator('.chat-bubble.assistant')).to_have_count(1)
            expect(page.locator('.chat-attachment-preview')).to_have_count(0)
            expect(page.locator('.chat-image-preview')).to_be_visible()
            assert page.locator('.chat-image-preview').evaluate('(image)=>image.complete && image.naturalWidth>0')
            page.locator('.chat-compose-box textarea').fill('quiz on this me')
            with page.expect_response(lambda r:r.url.endswith('/turns') and r.request.method=='POST') as sent:
                page.locator('.chat-send').click()
            assert sent.value.json()['image_document_id'] is None
            expect(page.locator('.inline-quiz')).to_be_visible(timeout=240000)
            expect(page.locator('.chat-image-preview')).to_have_count(1)
            rows = page.request.get('http://127.0.0.1:8000/chat/threads/'+thread+'/turns').json()
            assert rows[-1]['provenance']['source_kind'] == 'conversation'
            assert len(rows[-1]['quiz']['questions']) == 5
            Path('data/benchmarks/design').mkdir(parents=True,exist_ok=True)
            page.screenshot(path='data/benchmarks/design/chat-direct-image.png',full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert not errors,errors
            print('PASS: direct image + question -> local Qwen-VL answer, no review, history and mobile.')
        finally:
            if thread:page.request.delete('http://127.0.0.1:8000/chat/threads/'+thread)
            if document:page.request.delete('http://127.0.0.1:8000/documents/'+document)
            browser.close()


if __name__=='__main__':
    main()
