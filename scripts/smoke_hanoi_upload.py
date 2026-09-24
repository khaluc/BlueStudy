"""Reproduce the reported 11-page upload in Chrome and keep the user's imported exam."""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from scripts.generate_test_data import blank_pdf


def main():
    source=next(p for p in Path('D:/').glob('*.pdf') if 'THPTQG' in p.name)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        base='http://127.0.0.1:8000'
        page.goto(base+'/app/#exams')
        page.get_by_label('Chọn PDF đề thi',exact=True).set_input_files(str(source))
        with page.expect_response(lambda r:r.url.endswith('/exams') and r.request.method=='POST') as created:
            page.get_by_role('button',name='Chuyển thành đề thi',exact=True).click()
        assert created.value.status==202
        exam=created.value.json();print('11-page PDF accepted; exam',exam['id'],flush=True)
        page.goto(base+'/app/#exams')
        page.get_by_label('Chọn PDF đề thi',exact=True).set_input_files({'name':'too-many-pages.pdf','mimeType':'application/pdf','buffer':blank_pdf(21)})
        page.get_by_role('button',name='Chuyển thành đề thi',exact=True).click()
        expect(page.locator('#notice')).to_contain_text('21 trang')
        expect(page.locator('#notice')).to_contain_text('20 trang')
        print('Specific page-limit error is visible.',flush=True)
        last=None
        for _ in range(300):
            exam=page.request.get(base+'/exams/'+exam['id']).json()
            state=(exam['status'],exam['classified_count'])
            if state!=last:print(state,exam['error_code'],flush=True);last=state
            if exam['status'] not in ('queued','analyzing'):break
            time.sleep(2)
        Path('data/benchmarks/hanoi-exam.json').write_text(json.dumps(exam,ensure_ascii=False,indent=2),encoding='utf-8')
        assert exam['status']=='ready',exam['error_code']
        assert len(exam['structure']['questions'])==40
        assert 'HẾT' not in exam['structure']['questions'][-1]['options'][-1]
        page.goto(base+'/app/#exam='+exam['id'])
        expect(page.locator('.exam-form fieldset')).to_have_count(40)
        expect(page.locator('.exam-form input').first).to_be_enabled()
        page.screenshot(path='data/benchmarks/design/hanoi-exam-ready.png',full_page=False)
        assert not errors,errors
        browser.close()
        print('PASS: Hanoi PDF uploaded through UI; 40 classified questions ready; precise oversized-page error.',flush=True)


if __name__=='__main__':main()
