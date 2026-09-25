from packages.db.models import SpeakingSession, SpeakingAttempt


def test_learning_map_private_and_separates_guided_attempts(backend):
    client, sessions, a, b, _, ids = backend
    assert client.get('/learning-map').status_code == 401
    assert client.get('/learning-map', headers=a).json()['speaking'] == []
    with sessions.begin() as db:
        session = SpeakingSession(owner_id=ids[0], lesson='opinion', question='Example')
        db.add(session); db.flush()
        db.add(SpeakingAttempt(owner_id=ids[0], session_id=session.id, words=[],
            transcript='Private transcript', metrics={'practice_mode':'model'},
            response_language='en', status='ready', coaching={'overall':3}))
    response = client.get('/learning-map', headers=a)
    assert response.headers['cache-control'] == 'no-store'
    assert response.json()['speaking'][0]['mode'] == 'model'
    assert 'Private transcript' not in response.text
    assert client.get('/learning-map', headers=b).json()['speaking'] == []


def test_blank_and_ungraded_answers_are_not_weaknesses():
    from packages.core.exam_review import review_metrics
    result = review_metrics({'feedback':[
        {'skill':'word_form','number':1,'selected':None,'correct':0,'is_correct':False},
        {'skill':'word_form','number':2,'selected':1,'correct':None,'is_correct':None},
        {'skill':'word_form','number':3,'selected':1,'correct':0,'is_correct':False},
    ]})
    assert result['skills'][0]['wrong_questions'] == [3]
    assert result['skills'][0]['answered_graded'] == 1
