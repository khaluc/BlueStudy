"""Standalone chat browser smoke; one real model call and PDF attachment."""
import json
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright, expect
from scripts.generate_test_data import text_pdf


def main():
    credentials = json.loads(Path('data/local-demo.json').read_text(encoding='utf-8'))
    output = Path('data/benchmarks/design')
    output.mkdir(parents=True, exist_ok=True)
    thread_id = document_id = None
    with httpx.Client(base_url='http://127.0.0.1:8000', headers={
        'Authorization': 'Bearer '+credentials['token']}, timeout=30) as client:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel='chrome', headless=True)
                page = browser.new_page(viewport={'width':1440, 'height':1000})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto('http://127.0.0.1:8000/app/#chat')
                expect(page.locator('.chat-send')).to_be_disabled()
                page.get_by_role('button', name='Đăng nhập để bắt đầu', exact=True).click()
                page.get_by_label('Mã truy cập', exact=True).fill(credentials['token'])
                page.get_by_role('button', name='Vào góc học tập').click()
                expect(page.locator('.chat-compose-box textarea')).to_be_enabled()
                with page.expect_response(lambda r:r.url.endswith('/chat/threads') and r.request.method=='POST') as response:
                    page.get_by_role('button', name='＋ Chat mới', exact=True).click()
                thread_id = response.value.json()['id']
                expect(page.locator('.chat-thread-select')).to_have_value(thread_id)
                page.locator('.chat-compose-box textarea').fill('Giải thích ngắn sự khác nhau giữa since và for, kèm một ví dụ.')
                page.locator('.chat-send').click()
                expect(page.locator('.chat-bubble.assistant')).to_have_count(1, timeout=240000)
                rows = client.get('/chat/threads/'+thread_id+'/turns').json()
                assert rows[0]['status']=='succeeded' and rows[0]['provenance']['model']
                page.reload()
                expect(page.locator('.chat-bubble.assistant')).to_have_count(1)
                with page.expect_response(lambda r:r.url.endswith('/uploads') and r.request.method=='POST') as response:
                    page.locator('input[type=file]').set_input_files({'name':'chat-notes.pdf','mimeType':'application/pdf','buffer':text_pdf()})
                document_id = response.value.json()['id']
                page.get_by_role('button', name='Kiểm tra văn bản', exact=True).click(timeout=60000)
                expect(page.get_by_label('Văn bản trích xuất', exact=True)).not_to_have_value('')
                page.get_by_role('button', name='Xác nhận và dùng trong chat', exact=True).click()
                expect(page.locator('.chat-review-dialog')).not_to_be_visible()
                expect(page.get_by_role('button', name='Bỏ đính kèm', exact=True)).to_be_visible()
                assert client.get('/chat/threads/'+thread_id).json()['session_id']
                page.screenshot(path=str(output/'chat-desktop.png'), full_page=True)
                page.set_viewport_size({'width':390, 'height':844})
                page.reload()
                expect(page.locator('.chat-bubble.assistant')).to_have_count(1)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                expect(page.locator('.chat-monitor')).not_to_be_visible()
                page.get_by_role('button', name='◉ Hoạt động', exact=True).click()
                expect(page.locator('.chat-monitor')).to_be_visible()
                page.get_by_role('button', name='◉ Hoạt động', exact=True).click()
                page.locator('.chat-compose-box').scroll_into_view_if_needed()
                page.screenshot(path=str(output/'chat-mobile.png'), full_page=True)
                assert not errors, errors
                browser.close()
                print('Chat: real answer, persistent history, PDF review/source, desktop/mobile passed.')
        finally:
            if thread_id:
                response = client.delete('/chat/threads/'+thread_id)
                if response.status_code not in (204,409): response.raise_for_status()
            if document_id: client.delete('/documents/'+document_id).raise_for_status()


if __name__=='__main__':
    main()
