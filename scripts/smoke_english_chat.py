"""Live language regression check. Creates and deletes its own temporary thread."""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def no_vietnamese(text):
    return not any(char in text.lower() for char in 'ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ')

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width':1440, 'height':1000})
    page.goto('http://127.0.0.1:8000/app/#chat')
    page.locator('.chat-compose-box textarea').wait_for()
    page.locator('[data-language=en]').click()
    created = page.request.post('http://127.0.0.1:8000/chat/threads', data={})
    assert created.status == 201
    thread_id = created.json()['id']
    base = 'http://127.0.0.1:8000/chat/threads/' + thread_id
    def wait_turn():
        deadline = time.monotonic() + 210
        while time.monotonic() < deadline:
            rows = page.request.get(base+'/turns').json()
            if rows and rows[-1]['status'] != 'queued':
                assert rows[-1]['status'] == 'succeeded', rows[-1].get('error_code')
                return rows[-1]
            page.wait_for_timeout(1500)
        raise AssertionError('Chat generation timed out')
    try:
        page.evaluate('(id) => chatWorkspace(id)', thread_id)
        page.locator('.chat-compose-box textarea').fill(
            'Giải thích ngắn các thành ngữ: piece of cake, break the ice, '
            'cost an arm and a leg, once in a blue moon, under the weather.')
        page.locator('.chat-send').click()
        answer = wait_turn()
        assert answer['provenance']['response_language'] == 'en'
        assert no_vietnamese(answer['answer']), 'Chat response is not entirely English'
        print('English chat passed:', answer['provenance'].get('model'), flush=True)
        page.locator('.quiz-shortcut').wait_for(state='visible')
        page.wait_for_function("!document.querySelector('.quiz-shortcut').disabled")
        page.locator('.quiz-shortcut').click()
        quiz = wait_turn()
        # The new request may reach the server just after the previous turn was read.
        if quiz['id'] == answer['id']:
            page.wait_for_timeout(1500)
            quiz = wait_turn()
        assert quiz['quiz'] and quiz['provenance']['response_language'] == 'en'
        assert no_vietnamese(json.dumps(quiz['quiz'], ensure_ascii=False))
        assert no_vietnamese(quiz['answer']) and no_vietnamese(quiz['message'])
        result = page.request.post(base+'/turns/'+quiz['id']+'/quiz-submit', data={'answers':[0]*5})
        assert result.status == 200
        assert no_vietnamese(json.dumps(result.json()['feedback'], ensure_ascii=False))
        page.evaluate('(id) => chatWorkspace(id)', thread_id)
        page.locator('.inline-quiz').wait_for()
        page.screenshot(path=str(ROOT/'data/benchmarks/design/english-chat-quiz.png'))
        print('English quiz, options, instructions and graded explanations passed:',
              quiz['provenance'].get('model'), flush=True)
    finally:
        response = page.request.delete(base)
        if response.status != 204:
            print('Temporary thread cleanup pending:', thread_id, response.status, flush=True)
        browser.close()
