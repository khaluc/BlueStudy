"""Retry the latest failed exam assessment, preserving the submitted answers/score."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto('http://127.0.0.1:8000/app/#exams')
    page.wait_for_function("typeof token !== 'undefined' && token === 'local'")
    exams=page.request.get('http://127.0.0.1:8000/exams').json()
    selected=None
    for exam in exams:
        rows=page.request.get(f"http://127.0.0.1:8000/exams/{exam['id']}/attempts").json()
        if rows:
            selected=(exam,rows[0])
            if rows[0]['status']=='failed':break
    assert selected,'No existing exam attempt to review'
    exam,before=selected
    page.locator('[data-language=en]').click()
    page.evaluate('(id) => examView(id)',exam['id'])
    page.locator('.exam-coaching').wait_for()
    if before['status']=='failed' or not (before.get('coaching') or {}).get('roadmap'):
        page.get_by_role('button',name='Generate assessment and study plan',exact=True).click()
    deadline=time.monotonic()+210
    while time.monotonic()<deadline:
        rows=page.request.get(f"http://127.0.0.1:8000/exams/{exam['id']}/attempts").json()
        after=next(row for row in rows if row['id']==before['id'])
        if after['status']!='queued':break
        page.wait_for_timeout(1500)
    assert after['status']=='ready',after['result'].get('coaching_error',after['status'])
    assert after['answers']==before['answers']
    for field in ['score','graded_total','total','feedback']:
        assert after['result'][field]==before['result'][field]
    assert after['coaching']['roadmap']
    page.locator('.exam-study-step').first.wait_for()
    page.locator('.exam-coaching').evaluate("node=>node.scrollIntoView({block:'start'})")
    page.screenshot(path=str(ROOT/'data/benchmarks/design/exam-study-plan.png'))
    link=page.locator('.exam-plan-links button').first
    if link.count():
        number=link.inner_text()
        link.click()
        assert page.evaluate('document.activeElement.id')=='exam-question-'+number
    page.reload()
    page.locator('.exam-study-step').first.wait_for()
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.locator('.exam-coaching').evaluate("node=>node.scrollIntoView({block:'start'})")
    page.screenshot(path=str(ROOT/'data/benchmarks/design/exam-study-plan-mobile.png'))
    assert not errors,errors
    print('PASS: AI assessment and saved study plan; answers/score preserved; question links and mobile layout')
    print('Sessions:',len(after['coaching']['roadmap']),'model:',after['coaching'].get('model'))
    browser.close()
