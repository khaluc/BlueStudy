"""Verify automatic translation and cached EN/TV switching on a saved assessment."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]; page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto('http://127.0.0.1:8000/app/#exams')
    page.wait_for_function("typeof token !== 'undefined' && token === 'local'")
    selected=None
    for exam in page.request.get('http://127.0.0.1:8000/exams').json():
        rows=page.request.get(f"http://127.0.0.1:8000/exams/{exam['id']}/attempts").json()
        if rows and rows[0].get('coaching'):
            selected=(exam,rows[0]);break
    assert selected,'A saved assessment is required'
    exam,before=selected
    page.evaluate('(id)=>examView(id)',exam['id'])
    def stored():
        return next(row for row in page.request.get(
            f"http://127.0.0.1:8000/exams/{exam['id']}/attempts").json() if row['id']==before['id'])
    for language in ['en','vi','en']:
        page.locator(f'[data-language={language}]').click()
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            row=stored()
            if row['status']=='ready' and row['coaching'].get('response_language')==language:
                break
            if row['status']=='failed':raise AssertionError(row['result'].get('coaching_error'))
            page.wait_for_timeout(1500)
        assert row['status']=='ready' and row['coaching']['response_language']==language
        page.wait_for_function('(summary)=>document.querySelector(".exam-coaching")?.textContent.includes(summary)',
                               arg=row['coaching']['summary'])
        assert row['result']['score']==before['result']['score']
        assert row['answers']==before['answers']
        assert row['result']['feedback']==before['result']['feedback']
        print('PASS saved assessment language:',language,flush=True)
    assert set(stored()['result']['coaching_translations'])=={'en','vi'}
    page.reload()
    page.wait_for_function('(summary)=>document.querySelector(".exam-coaching")?.textContent.includes(summary)',
                           arg=row['coaching']['summary'])
    page.locator('.exam-coaching').evaluate("node=>node.scrollIntoView({block:'start'})")
    page.screenshot(path=str(ROOT/'data/benchmarks/design/exam-language-en.png'))
    assert not errors,errors
    browser.close()
