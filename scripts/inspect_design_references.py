from pathlib import Path
from playwright.sync_api import sync_playwright

if __name__ == '__main__':
    directory = Path('data/benchmarks/design'); directory.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        for name, url in [('reference-1','https://nuesj4c5tehcg.kimi.page/'),
                          ('reference-2','https://7inif7p6jcz2y.kimi.page/')]:
            page = browser.new_page(viewport={'width':1440,'height':1000})
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=45000)
                page.screenshot(path=str(directory / (name+'.png')), full_page=False)
                (directory/(name+'.txt')).write_text(page.locator('body').inner_text(), encoding='utf-8')
                print(name, page.title(), flush=True)
            except Exception as exc:
                print(name, type(exc).__name__, flush=True)
            finally: page.close()
        browser.close()
