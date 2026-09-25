import json
import pytest
from apps.chat.agents.orchestrator import Orchestrator
from apps.worker.main import process_one
from packages.core.material import Bundle
from packages.curriculum.grade9_topics import suggest

SOURCE = 'A community volunteer helps neighbours. Trees provide shade. Buses carry people. Parks are public spaces. Libraries lend books.'


def test_academic_topics_are_default_and_selectable(backend):
    client, _, owner, *_ = backend
    topics = client.get('/curriculum', headers=owner).json()
    assert topics and all(t['id'].startswith('ae-') for t in topics)
    doc = client.post('/documents', headers=owner,
                      json={'title':'Research', 'text':'Research evidence supports the hypothesis.'}).json()
    session = client.post('/sessions', headers=owner, json={'document_id':doc['id']}).json()
    path = '/sessions/' + session['id'] + '/curriculum'
    matches = client.get(path, headers=owner).json()['matches']
    assert matches[0]['topic']['id'] == 'ae-research'
    assert client.patch(path, headers=owner, json={'topic_id':'ae-research'}).status_code == 200


def bundle():
    facts = [('Who helps neighbours?', 'A community volunteer', 'A community volunteer helps neighbours.'),
             ('What provides shade?', 'Trees', 'Trees provide shade.'),
             ('What carries people?', 'Buses', 'Buses carry people.'),
             ('What are public spaces?', 'Parks', 'Parks are public spaces.'),
             ('What lends books?', 'Libraries', 'Libraries lend books.')]
    return dict(summary='Các dịch vụ trong cộng đồng.', notes=['Thư viện cho mượn sách.'],
                cards=[dict(front=q, back=a, quote=quote) for q,a,quote in facts],
                quiz=[dict(question=q, options=[a,'The moon','The sun','The ocean'], correct=0,
                           explanation=a, quote=quote) for q,a,quote in facts])


def flow(backend):
    client, sessions, a, b, *_ = backend
    d=client.post('/documents', headers=a, json=dict(title='Community',text=SOURCE)).json()
    s=client.post('/sessions', headers=a, json=dict(document_id=d['id'])).json()
    j=client.post('/sessions/'+s['id']+'/jobs', headers=a, json=dict(kind='generate_bundle')).json()
    class Model:
        def ask(self, prompt):
            assert SOURCE in prompt
            return json.dumps(bundle()), 'test-model'
    assert process_one(sessions, Orchestrator(Model()))
    result=client.get('/jobs/'+j['id'],headers=a).json()
    assert result['status']=='succeeded'
    return d,s,result['result']['material_id'],j


def correct_answers(backend, material_id):
    from packages.db.models import Material
    with backend[1]() as db:
        return [q['correct'] for q in db.get(Material, material_id).content['quiz']]


def test_full_study_assessment_isolation_and_cascade(backend):
    client, sessions, a, b, *_ = backend
    d,s,mid,j=flow(backend)
    for path in ['/jobs/'+j['id'],'/materials/'+mid,'/sessions/'+s['id']+'/materials']:
        response=client.get(path,headers=a)
        assert response.status_code==200
        assert '"correct"' not in response.text
        assert '"explanation"' not in response.text
        assert client.get(path,headers=b).status_code==404
    assert client.post('/materials/'+mid+'/attempts',headers=b,json={'answers':[0]*5}).status_code==404
    answers=correct_answers(backend,mid)
    answers[1]=(answers[1]+1)%4
    answers[3]=(answers[3]+1)%4
    r=client.post('/materials/'+mid+'/attempts',headers=a,json={'answers':answers})
    assert r.status_code==201
    assert r.json()['score']==3
    assert len(r.json()['feedback'])==5
    assert client.get('/users/me/progress',headers=a).json()['average_percent']==60
    assert client.get('/users/me/progress',headers=b).json()['attempt_count']==0
    assert client.get('/sessions/'+s['id']+'/curriculum',headers=a).json()['status']=='suggested'
    assert client.get('/sessions/'+s['id']+'/curriculum',headers=b).status_code==404
    assert client.delete('/documents/'+d['id'],headers=a).status_code==204
    assert client.get('/materials/'+mid,headers=a).status_code==404
    assert client.get('/users/me/progress',headers=a).json()['attempt_count']==0


@pytest.mark.parametrize('answers',[[0]*4,[0]*6,[4]*5,[-1]*5,[True]*5,['0']*5])
def test_invalid_answers(backend,answers):
    client,_,a,*_=backend
    _,_,mid,_=flow(backend)
    assert client.post('/materials/'+mid+'/attempts',headers=a,json={'answers':answers}).status_code==422


def test_fabricated_citations_and_invalid_choices_rejected():
    data=bundle()
    data['cards'][0]['quote']='This does not exist in the source.'
    with pytest.raises(ValueError): Bundle.model_validate(data).check_source(SOURCE)
    data=bundle();data['quiz'][0]['options']=['a',' A ','b','c']
    with pytest.raises(ValueError): Bundle.model_validate(data)
    assert suggest('Completely unrelated algebra: x + y = 3')==[]
    assert suggest('deviceship communityship')==[]


def test_web_entry_and_clear_progress(backend):
    client,_,a,b,*_=backend
    assert client.get('/app/').status_code==200
    assert client.get('/app/app.js').status_code==200
    assert client.get('/users/me/progress').status_code==401
    _,_,mid,_=flow(backend)
    client.post('/materials/'+mid+'/attempts',headers=a,json={'answers':[0]*5})
    assert client.delete('/users/me/progress',headers=b).status_code==204
    assert client.get('/users/me/progress',headers=a).json()['attempt_count']==1
    assert client.delete('/users/me/progress',headers=a).status_code==204
    assert client.get('/users/me/progress',headers=a).json()['attempt_count']==0


def test_topic_preferences_and_owner_scoped_memory(backend):
    from apps.chat.tools.memory_tool import recent_mistakes
    client, sessions, a, b, _, ids=backend
    _,s,mid,_=flow(backend)
    path='/sessions/'+s['id']+'/curriculum'
    assert client.patch(path,headers=b,json={'topic_id':'gs9-u1'}).status_code==404
    assert client.patch(path,headers=a,json={'topic_id':'made-up'}).status_code==422
    assert client.patch(path,headers=a,json={'topic_id':'gs9-u1'}).status_code==200
    assert client.get(path,headers=a).json()['status']=='learner_selected'
    for _ in range(3):
        assert client.post('/materials/'+mid+'/attempts',headers=a,
            json={'answers':[(v+1)%4 for v in correct_answers(backend,mid)]}).status_code==201
    progress = client.get('/users/me/progress',headers=a).json()['topics']
    assert next(t for t in progress if t['topic_id']=='gs9-u1')['status']=='needs_practice'
    assert len(client.get('/users/me/review',headers=a).json())==5
    assert client.get('/users/me/review',headers=b).json()==[]
    with sessions() as db:
        assert len(recent_mistakes(db,ids[0]))==3
        assert recent_mistakes(db,ids[1])==[]
    assert client.patch('/users/me',headers=a,json={'display_name':'Learner','language_level':'support',
        'learning_preference':'flashcards'}).status_code==200
    assert client.get('/users/me',headers=a).json()['learning_preference']=='flashcards'
    assert client.get('/documents?q=community',headers=a).json()
    assert client.get('/documents?q=community',headers=b).json()==[]
    assert client.get('/documents?q=%25',headers=a).json()==[]
    # A newer correct attempt removes earlier mistakes from review.
    client.post('/materials/'+mid+'/attempts',headers=a,json={'answers':correct_answers(backend,mid)})
    assert client.get('/users/me/review',headers=a).json()==[]
