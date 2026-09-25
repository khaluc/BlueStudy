import json
from apps.worker.tasks.chat_task import process_chat


def test_each_turn_keeps_requested_language_and_rejects_invalid_language(backend):
    client, sessions, headers, *_ = backend
    thread = client.post('/chat/threads', headers=headers, json={}).json()
    path = '/chat/threads/' + thread['id'] + '/turns'
    assert client.post(path, headers=headers, json={
        'message':'Hello', 'response_language':'invalid'}).status_code == 422

    class Model:
        def ask(self, prompt, response_language='vi'):
            self.prompt = prompt
            assert response_language == ('en' if 'entire response in clear English' in prompt else 'vi')
            return 'An explanation.', 'test'

    model = Model()
    for language in ['en', 'vi']:
        response = client.post(path, headers=headers, json={
            'message':'Giải thích thành ngữ này', 'response_language':language})
        assert response.status_code == 202
        assert response.json()['provenance']['response_language'] == language
        process_chat(sessions, model)
        if language == 'en':
            assert 'entire response in clear English' in model.prompt
        else:
            assert 'Trò chuyện bằng tiếng Việt dễ hiểu.' in model.prompt
        assert client.get(path, headers=headers).json()[-1]['provenance']['response_language'] == language


def test_english_quiz_from_vietnamese_chat_has_english_feedback(backend):
    client, sessions, headers, *_ = backend
    thread = client.post('/chat/threads', headers=headers, json={}).json()
    path = '/chat/threads/' + thread['id'] + '/turns'

    class Chat:
        def ask(self, prompt):
            return '**Piece of cake** nghĩa là rất dễ dàng.', 'test'

    client.post(path, headers=headers, json={'message':'Giải thích piece of cake'})
    process_chat(sessions, Chat())
    turn = client.post(path, headers=headers, json={
        'message':'Tạo quiz về bài này', 'action':'quiz', 'response_language':'en'}).json()
    assert 'Recognised' in turn['provenance']['agent_trace'][0]['detail']

    class Quiz:
        def ask(self, prompt, response_language='vi'):
            assert response_language == 'en'
            assert 'ALL answer options and ALL explanations in English only' in prompt
            assert 'Use Vietnamese explanations' not in prompt
            assert 'Piece of cake nghĩa là rất dễ dàng.' in prompt
            assert '**Piece of cake**' not in prompt
            return json.dumps({'title':'English idioms', 'questions':[
                {'question':f'Which meaning fits example {i}?',
                 'options':['Very easy','Very expensive','Feeling unwell','Very rare'],
                 'correct':0,'explanation':'A piece of cake is something very easy to do.',
                 'quote':'Piece of cake nghĩa là rất dễ dàng.'} for i in range(5)]}), 'test'

    process_chat(sessions, Quiz())
    process_chat(sessions, Quiz())
    result = client.get(path, headers=headers).json()[-1]
    assert result['status'] == 'succeeded'
    assert result['answer'].startswith('Choose one answer')
    assert result['provenance']['response_language'] == 'en'
    assert 'Created 5 questions' in result['provenance']['agent_trace'][2]['detail']
    assert 'correct' not in result['quiz']['questions'][0]
    graded = client.post(path+'/'+turn['id']+'/quiz-submit', headers=headers,
                         json={'answers':[0]*5}).json()
    assert all(item['explanation'].startswith('A piece of cake') for item in graded['feedback'])
