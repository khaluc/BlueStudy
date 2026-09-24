"""Browser PDF -> structured questions -> submission -> AI revision advice."""
import json
from io import BytesIO
from pathlib import Path
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
from playwright.sync_api import sync_playwright,expect


def exam_pdf():
    writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    lines=['Read the following passage and answer questions 1 to 2.',
        'Libraries lend books. Parks provide shade.',
        'Question 1. What do libraries lend?', 'A. Books B. Cars C. Houses D. Planes',
        'Question 2. What provides shade?', 'A. Oceans B. Parks C. Computers D. Roads']
    stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 35 740 Td '+' 0 -28 Td '.join('('+line+') Tj' for line in lines)+' ET').encode('ascii'))
    page[NameObject('/Contents')]=writer._add_object(stream)
    out=BytesIO();writer.write(out);return out.getvalue()


def main():
    document=None
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        base='http://127.0.0.1:8000'
        try:
            report=json.loads(Path('data/benchmarks/imported-exam.json').read_text(encoding='utf-8'))
            page.goto(base+'/app/#exam='+report['id'])
            expect(page.locator('.exam-form fieldset')).to_have_count(40,timeout=15000)
            expect(page.locator('.exam-passage')).to_have_count(6)
            expect(page.locator('.exam-form input[type=radio]')).to_have_count(160)
            assert '"correct"' not in page.request.get(base+'/exams/'+report['id']).text()
            page.screenshot(path='data/benchmarks/design/structured-exam.png',full_page=False)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path='data/benchmarks/design/structured-exam-mobile.png',full_page=False)
            page.goto(base+'/app/#exams')
            page.get_by_label('Chọn PDF đề thi',exact=True).set_input_files({'name':'exam-browser-test.pdf','mimeType':'application/pdf','buffer':exam_pdf()})
            with page.expect_response(lambda r:r.url.endswith('/uploads') and r.request.method=='POST') as uploaded:
                page.get_by_role('button',name='Chuyển thành đề thi',exact=True).click()
            document=uploaded.value.json()['id']
            expect(page.locator('.exam-form fieldset')).to_have_count(2,timeout=300000)
            expect(page.locator('.exam-form input').first).to_be_enabled(timeout=300000)
            page.locator('.exam-form fieldset').nth(0).locator('input').nth(0).check()
            page.locator('.exam-form fieldset').nth(1).locator('input').nth(0).check()
            page.reload()
            expect(page.locator('.exam-form fieldset').nth(0).locator('input').nth(0)).to_be_checked()
            page.get_by_role('button',name='Nộp bài và phân tích kết quả').click()
            expect(page.locator('.exam-results')).to_be_visible()
            expect(page.get_by_role('heading',name='AI hỗ trợ ôn tập',exact=True)).to_be_visible(timeout=180000)
            expect(page.locator('.exam-results h2')).to_contain_text('1 / 2')
            page.reload()
            expect(page.locator('.exam-results h2')).to_contain_text('1 / 2')
            expect(page.locator('.exam-form input').first).to_be_disabled()
            page.screenshot(path='data/benchmarks/design/exam-results-mobile.png',full_page=True)
            assert not errors,errors
            print('PASS: 40-question PDF layout; browser upload, draft restore, score, AI coaching, saved results and mobile.')
        finally:
            if document:page.request.delete(base+'/documents/'+document)
            browser.close()


if __name__=='__main__':main()
