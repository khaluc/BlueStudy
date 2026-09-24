"""Read-only browser checks for language switching and state preservation."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:8000/app/")
    page.wait_for_function("typeof token !== 'undefined' && token === 'local'")
    page.locator('[data-language="en"]').click()
    page.locator('[data-view="library"]').click()
    page.get_by_role("heading", name="Your library", exact=True).wait_for()
    title = page.locator('.document-card h3').first.inner_text()
    page.locator('[data-language="vi"]').click()
    page.get_by_role("heading", name="Thư viện của bạn", exact=True).wait_for()
    assert page.locator('.document-card h3').first.inner_text() == title
    page.locator('[data-language="en"]').click()
    page.reload()
    page.wait_for_function("document.documentElement.lang === 'en'")
    page.locator('[data-view="chat"]').click()
    composer = page.locator('.chat-compose-box textarea')
    composer.wait_for()
    composer.fill("My draft: Tủ tài liệu")
    page.locator('[data-language="vi"]').click()
    assert composer.input_value() == "My draft: Tủ tài liệu"
    page.locator('[data-language="en"]').click()
    assert composer.input_value() == "My draft: Tủ tài liệu"
    assert composer.get_attribute('placeholder').startswith('Ask anything')
    page.locator('[data-view="exams"]').click()
    page.get_by_role('heading', name='Your exams', exact=True).wait_for()
    page.get_by_role('button', name='Open exam', exact=True).first.click()
    question = page.locator('.exam-form input[type="radio"]').first
    question.wait_for()
    passage = page.locator('.exam-passage p').first.inner_text()
    question.check()
    page.locator('[data-language="vi"]').click()
    assert question.is_checked()
    page.locator('[data-language="en"]').click()
    assert question.is_checked()
    assert page.locator('.exam-passage p').first.inner_text() == passage
    page.get_by_role('button', name='Submit and analyse results', exact=True).wait_for()
    page.screenshot(path=str(ROOT / 'data/benchmarks/design/english-exam.png'))
    for view in ['library', 'profile', 'progress', 'roadmap', 'chat']:
        page.locator(f'[data-view="{view}"]').first.click()
        page.wait_for_function('scrollY === 0')
        page.wait_for_timeout(250)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.set_viewport_size({'width':390, 'height':844})
    page.reload()
    page.locator('.chat-compose-box textarea').wait_for()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.locator('[data-language="vi"]').click()
    page.locator('[data-language="en"]').click()
    page.screenshot(path=str(ROOT / 'data/benchmarks/design/english-mobile.png'))
    assert not errors, errors
    browser.close()
    print('PASS: EN/TV, persistence, draft and answer preservation, original passages, desktop/mobile')
