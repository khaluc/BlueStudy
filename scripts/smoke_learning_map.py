"""Read-only smoke test against the running local app."""
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width':1440,'height':1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:8000/app/#map')
    page.locator('[data-language=en]').click()
    expect(page.get_by_role('heading', name='Your learning map', exact=True)).to_be_visible()
    expect(page.locator('nav [data-view=roadmap],nav [data-view=library],nav [data-view=progress]')).to_have_count(0)
    expect(page.locator('#content input[type=file]')).to_have_count(0)
    expect(page.locator('.learning-plan')).to_be_visible()
    expect(page.locator('.learning-columns')).to_be_visible()
    page.evaluate('notebookDashboard()')
    expect(page.get_by_role('heading', name='Your learning map', exact=True)).to_be_visible()
    expect(page.locator('.new-notebook')).to_have_count(0)
    expect(page.locator('#notice')).to_be_empty()
    page.locator('[data-language=vi]').click()
    expect(page.locator('.learning-plan h2')).not_to_have_text('What should I study next?')
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Horizontal overflow'
    page.locator('[data-language=en]').click()
    page.get_by_role('button', name='Practice Speaking', exact=True).click()
    expect(page.locator('#speaking-set-picker')).to_be_visible()
    page.locator('nav [data-view=map]').click()
    expect(page.get_by_role('heading', name='Your learning map', exact=True)).to_be_visible()
    assert not errors, errors
    browser.close()
    print('PASS: live data, navigation, EN/TV, mobile, no PDF map or removed tabs, no JS errors')
