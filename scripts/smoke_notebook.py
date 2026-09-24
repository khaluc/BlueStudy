"""Notebook UI checks. --live additionally creates one real paid study bundle."""
import argparse
import json
from pathlib import Path
from uuid import uuid4
import httpx
from playwright.sync_api import sync_playwright, expect


def preview(page, directory):
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    requests=[];page.on('request',lambda r:requests.append((r.method,r.url)))
    page.goto('http://127.0.0.1:8000/app/')
    expect(page.get_by_role('heading',name='Cuốn vở tri thức của bạn',exact=False)).to_be_visible()
    expect(page.locator('.map-node')).to_have_count(8)
    page.evaluate('document.fonts.ready')
    page.screenshot(path=str(directory/'notebook-desktop.png'),full_page=True,animations='disabled')
    page.get_by_role('button',name='Phóng to sơ đồ').click()
    expect(page.locator('.zoom-controls output')).to_have_text('110%')
    page.get_by_role('button',name='Đặt lại sơ đồ').click()
    page.get_by_label('Tìm trong sơ đồ').fill('thư viện')
    expect(page.locator('.map-node:not(.dimmed)')).to_have_count(1)
    page.get_by_role('button',name='Đổi cách xem sơ đồ').click()
    expect(page.locator('.map-list button:visible')).to_have_count(1)
    page.get_by_label('Tìm trong sơ đồ').fill('')
    page.get_by_role('button',name='Đổi cách xem sơ đồ').click()
    page.get_by_role('button',name='Mở trang 03: Thư viện',exact=True).click()
    expect(page.locator('.reader h2')).to_have_text('Thư viện')
    page.get_by_role('button',name='Lật thẻ · xem lời giải').click()
    expect(page.locator('.card-answer')).to_contain_text('miễn phí')
    page.get_by_role('button',name='▷ Khám phá từng bước').click()
    expect(page.get_by_role('button',name='Ⅱ Tạm dừng')).to_be_visible()
    page.get_by_role('button',name='Ⅱ Tạm dừng').click()
    page.get_by_role('tab',name='Hỏi BlueStudy').click()
    expect(page.get_by_role('button',name='Mở góc học tập')).to_be_visible()
    page.get_by_role('tab',name='Luyện tập',exact=True).click()
    page.screenshot(path=str(directory/'notebook-quiz.png'),full_page=True,animations='disabled')
    for i in range(5):
        page.locator('.quiz-option').nth(i%4).click()
        if i<4:page.get_by_role('button',name='Câu tiếp →').click()
    page.get_by_role('button',name='Nộp bài và xem giải thích').click()
    expect(page.locator('.reader .score')).to_have_text('5 / 5')
    assert not [r for r in requests if r[0]=='POST'], 'Demo must not persist scores or call AI'
    page.get_by_role('button',name='Hướng dẫn sử dụng').click()
    expect(page.get_by_role('dialog')).to_be_visible()
    page.keyboard.press('Escape')
    expect(page.get_by_role('dialog')).not_to_be_visible()
    page.set_viewport_size({'width':390,'height':844})
    page.reload()
    expect(page.locator('.map-node')).to_have_count(8)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    page.evaluate('document.fonts.ready')
    page.screenshot(path=str(directory/'notebook-mobile.png'),full_page=True,animations='disabled')
    page.get_by_role('tab',name='Bài học',exact=True).focus()
    page.keyboard.press('ArrowRight')
    expect(page.get_by_role('tab',name='Hỏi BlueStudy')).to_have_attribute('aria-selected','true')
    assert not errors, errors
    print('PASS: notebook demo, graph/list/search/zoom, cards, walkthrough, tabs, quiz, help, mobile and keyboard',flush=True)


def live(page, directory):
    credentials=json.loads(Path('data/local-demo.json').read_text(encoding='utf-8'))
    document_id=None
    with httpx.Client(base_url='http://127.0.0.1:8000',headers={'Authorization':'Bearer '+credentials['token']},timeout=30) as client:
        original=client.get('/users/me').json()
        try:
            page.set_viewport_size({'width':1440,'height':1100})
            page.get_by_role('button',name='Đăng nhập',exact=True).click()
            page.get_by_label('Mã truy cập',exact=True).fill(credentials['token'])
            page.get_by_role('button',name='Vào góc học tập').click()
            expect(page.get_by_role('heading',name='Hôm nay, mình học gì?')).to_be_visible()
            page.get_by_label('Tên ghi chú',exact=True).fill('Community notebook '+uuid4().hex[:6])
            page.get_by_label('Nội dung (tối đa 2.400 ký tự)').fill(
                'In our local community, volunteers help older neighbours. The library lends books for free. '
                'A firefighter puts out fires. A gardener plants trees in the public park. '
                'People take the bus to reduce traffic. Students clean the park every Sunday.')
            with page.expect_response(lambda r:r.url.endswith('/documents') and r.request.method=='POST') as response:
                page.get_by_role('button',name='Lưu ghi chú',exact=True).click()
            document_id=response.value.json()['id']
            page.get_by_role('button',name='Bắt đầu học →').click()
            page.get_by_text('Chủ đề, nguồn & bộ học đã lưu',exact=True).click()
            page.get_by_label('Chủ đề học (bạn tự xác nhận)').select_option('gs9-u1')
            page.get_by_role('button',name='Lưu chủ đề',exact=True).click()
            expect(page.locator('#notice')).to_have_text('Đã lưu lựa chọn chủ đề của bạn.')
            page.locator('.reader').get_by_role('button',name='Tạo bộ ôn tập',exact=True).click()
            expect(page.locator('.map-node')).to_have_count(6,timeout=300000)
            expect(page.locator('.reader-body')).to_contain_text('Ý CHÍNH CẦN NHỚ')
            page.screenshot(path=str(directory/'notebook-live.png'),full_page=True,animations='disabled')
            page.get_by_role('tab',name='Luyện tập',exact=True).click()
            for i in range(5):
                page.locator('.quiz-option').first.click()
                if i<4:page.get_by_role('button',name='Câu tiếp →').click()
            with page.expect_response(lambda r:'/attempts' in r.url and r.request.method=='POST') as response:
                page.get_by_role('button',name='Nộp bài và xem giải thích').click()
            assessment=response.value.json()
            assert assessment['score']==sum(q['correct']==0 for q in assessment['feedback'])
            expect(page.locator('.reader .score')).to_have_text(str(assessment['score'])+' / 5')
            page.locator('[data-view="progress"]').click()
            expect(page.get_by_role('heading',name='Mỗi bước nhỏ đều đáng ghi nhận.')).to_be_visible()
            assert any(a['id']==assessment['id'] for a in client.get('/users/me/progress').json()['attempts'])
            page.locator('[data-view="profile"]').click()
            page.get_by_label('Hoạt động bạn thích').select_option('flashcards')
            page.get_by_role('button',name='Lưu hồ sơ',exact=True).click()
            expect(page.locator('#notice')).to_have_text('Đã lưu hồ sơ học tập.')
            page.reload()
            expect(page.locator('.map-node')).to_have_count(6)
            page.get_by_role('button',name='Đăng xuất',exact=True).click()
            expect(page.get_by_role('heading',name='Chào bạn, cùng học nhé.')).to_be_visible()
            assert page.evaluate("sessionStorage.getItem('padayon-token')") is None
            print('PASS: real account, document/session, cloud generation, notebook graph, server quiz score, profile, persisted reload and logout',flush=True)
        finally:
            if document_id:client.delete('/documents/'+document_id).raise_for_status()
            client.patch('/users/me',json={key:original[key] for key in ('display_name','language_level','learning_preference')}).raise_for_status()


def main(run_live=False):
    directory=Path('data/benchmarks/design');directory.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1100})
        try:
            preview(page,directory)
            if run_live:live(page,directory)
        except Exception as exc:
            # No input values or credentials in output; screenshot only outside login.
            if not page.locator('input[type="password"]').count():
                page.screenshot(path=str(directory/'failure.png'),full_page=True)
            print('FAILED:',type(exc).__name__,flush=True)
            raise
        finally:browser.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true')
    main(parser.parse_args().live)
