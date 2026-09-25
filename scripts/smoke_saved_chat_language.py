"""Verify opening an existing conversation in EN, switching TV/EN and reloading."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto('http://127.0.0.1:8000/app/#exams')
    page.wait_for_function("typeof token !== 'undefined' && token === 'local'")
    selected=None
    for thread in page.request.get('http://127.0.0.1:8000/chat/threads').json():
        rows=page.request.get(f"http://127.0.0.1:8000/chat/threads/{thread['id']}/turns").json()
        complete=[r for r in rows if r['status']=='succeeded']
        if complete:
            if selected is None:selected=(thread,complete[-1])
            hello=next((r for r in complete if r['message'].strip().lower()=='hello'),None)
            if hello:selected=(thread,hello);break
    assert selected,'No saved conversation'
    thread,original=selected
    page.locator('[data-language=en]').click()
    page.evaluate('(id)=>chatWorkspace(id)',thread['id'])
    base=f"http://127.0.0.1:8000/chat/threads/{thread['id']}/turns"
    deadline=time.monotonic()+240
    queued=False
    while time.monotonic()<deadline:
        rows=page.request.get(base).json()
        turn=next(r for r in rows if r['id']==original['id'])
        if turn.get('translations',{}).get('en') or (turn.get('provenance') or {}).get('response_language')=='en':break
        state=(turn.get('provenance') or {}).get('translation_status')
        queued=queued or state=='queued'
        if queued:assert state!='failed',turn['provenance']
        page.wait_for_timeout(1500)
    assert turn.get('translations',{}).get('en') or (turn.get('provenance') or {}).get('response_language')=='en'
    assert turn['answer']==original['answer'] and turn['quiz_result']==original['quiz_result']
    page.wait_for_timeout(3000)
    def english_visible():
        text=page.locator('.chat-bubble.assistant').last.inner_text()
        assert not any(c in text.lower() for c in 'ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ'),text
        assert 'Translating' not in text
    english_visible()
    page.locator('[data-language=vi]').click()
    page.locator('[data-language=en]').click()
    english_visible()
    page.reload()
    page.locator('.chat-bubble.assistant').last.wait_for()
    english_visible()
    page.wait_for_timeout(500)
    page.screenshot(path=str(ROOT/'data/benchmarks/design/saved-chat-english.png'))
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors,errors
    print('PASS: saved chat opens in English; EN/TV/EN and reload; original answer and score preserved')
    print('Original response language:',(original.get('provenance') or {}).get('response_language','legacy vi'))
    browser.close()
