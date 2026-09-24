from playwright.sync_api import sync_playwright, expect


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width':390,'height':844})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://127.0.0.1:8000/app/#chat')
        expect(page.locator('.chat-compose-box textarea')).to_be_enabled()
        expect(page.locator('.chat-send')).to_be_enabled()
        expect(page.locator('#logout')).not_to_be_visible()
        assert page.evaluate("sessionStorage.getItem('padayon-token')") is None
        assert 'padayon-local' not in page.evaluate('document.cookie')
        response = page.request.get('http://127.0.0.1:8000/users/me')
        assert response.status == 200
        user_id = response.json()['id']
        page.reload()
        expect(page.locator('.chat-compose-box textarea')).to_be_enabled()
        assert page.request.get('http://127.0.0.1:8000/users/me').json()['id'] == user_id
        page.locator('[data-view="library"]').click()
        expect(page.locator('input[type=file]')).to_be_attached()
        assert not errors, errors
        browser.close()
        print('PASS: no login, persistent account, chat enabled, library, HttpOnly cookie, mobile reload.')


if __name__ == '__main__':
    main()
