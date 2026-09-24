"""Browser PDF upload/review path; text PDF requires no cloud model call."""
import json
import re
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright, expect
from scripts.generate_test_data import text_pdf


def main():
    credentials=json.loads(Path('data/local-demo.json').read_text(encoding='utf-8'))
    document_id=None
    with httpx.Client(base_url='http://127.0.0.1:8000',headers={'Authorization':'Bearer '+credentials['token']},timeout=30) as client:
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(channel='chrome',headless=True)
                page=browser.new_page(viewport={'width':390,'height':844})
                page.goto('http://127.0.0.1:8000/app/')
                page.get_by_role('button',name='Đăng nhập',exact=True).click()
                page.get_by_label('Mã truy cập',exact=True).fill(credentials['token'])
                page.get_by_role('button',name='Vào góc học tập').click()
                page.get_by_label('Chọn tài liệu').set_input_files({'name':'browser-upload.pdf','mimeType':'application/pdf','buffer':text_pdf()})
                with page.expect_response(lambda r:r.url.endswith('/uploads') and r.request.method=='POST') as response:
                    page.get_by_role('button',name='Tải lên',exact=True).click()
                document_id=response.value.json()['id']
                text=page.get_by_label('Kiểm tra và sửa văn bản trích xuất')
                expect(text).to_have_value(re.compile('.*Since 2020.*',re.S),timeout=45000)
                text.fill(text.input_value()+'\nFor three days.')
                page.get_by_role('button',name='Lưu và xác nhận nội dung').click()
                expect(page.get_by_role('button',name='Bắt đầu học →')).to_be_visible()
                actual=client.get('/documents/'+document_id).json()
                assert actual['status']=='confirmed' and 'For three days.' in actual['text']
                page.get_by_role('button',name='Bắt đầu học →').click()
                expect(page.get_by_role('heading',name='Cuốn vở tri thức của bạn',exact=False)).to_be_visible()
                expect(page.get_by_role('button',name='Đăng xuất',exact=True)).to_be_visible()
                page.get_by_role('button',name='Đăng xuất',exact=True).click()
                expect(page.get_by_role('heading',name='Chào bạn, cùng học nhé.')).to_be_visible()
                assert page.evaluate("sessionStorage.getItem('padayon-token')") is None
                browser.close()
                print('Browser PDF upload, edit, confirm, session creation and mobile logout passed')
        finally:
            if document_id:client.delete('/documents/'+document_id).raise_for_status()


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Browser upload failed:',type(exc).__name__)
        raise SystemExit(1)
