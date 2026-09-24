import json
import pytest
from packages.db.models import ChatTurn
from apps.worker.tasks.chat_task import process_chat
from apps.chat.agents.quiz_intent_agent import wants_quiz

SOURCE = 'Environment means moi truong. Protect means bao ve.'


class Model:
    last_metadata = {'provider':'test','fallback_reason':None}
    def ask(self,prompt):
        assert SOURCE in prompt
        return json.dumps({'title':'Environment and protect','questions':[
            {'question':f'Question {i}?','options':['moi truong','bao ve','water','sky'],
             'correct':i%2,'explanation':'Explanation '+str(i),'quote':SOURCE}
            for i in range(5)]}), 'test-model'


def setup(backend):
    client, sessions, a, b, *_ = backend
    doc=client.post('/documents',headers=a,json={'title':'Vocab','text':SOURCE}).json()
    session=client.post('/sessions',headers=a,json={'document_id':doc['id']}).json()
    thread=client.post('/chat/threads',headers=a,json={'session_id':session['id']}).json()
    path='/chat/threads/'+thread['id']+'/turns'
    response=client.post(path,headers=a,json={'message':'quiz on me this'})
    assert response.status_code==202
    return path,response.json()['id']


def test_quiz_stages_private_key_grading_and_reload(backend):
    client,sessions,a,b,*_=backend
    path,tid=setup(backend)
    assert process_chat(sessions,Model())
    turn=client.get(path,headers=a).json()[0]
    assert turn['status']=='queued'
    assert turn['provenance']['agent_trace'][1]['status']=='done'
    assert 'work_context' not in turn
    assert process_chat(sessions,Model())
    response=client.get(path,headers=a)
    turn=response.json()[0]
    assert turn['status']=='succeeded'
    assert len(turn['quiz']['questions'])==5
    assert '"correct"' not in response.text and '"explanation"' not in response.text
    assert all(stage['status']=='done' for stage in turn['provenance']['agent_trace'])
    with sessions() as db:
        answers=[q['correct'] for q in db.get(ChatTurn,tid).quiz['questions']]
    submit=path+'/'+tid+'/quiz-submit'
    assert client.post(submit,headers=b,json={'answers':answers}).status_code==404
    assert client.post(submit,headers=a,json={'answers':[True]*5}).status_code==422
    answers[0]=(answers[0]+1)%4
    result=client.post(submit,headers=a,json={'answers':answers})
    assert result.json()['score']==4
    assert len(result.json()['feedback'])==5
    assert client.post(submit,headers=a,json={'answers':answers}).json()==result.json()
    answers[1]=(answers[1]+1)%4
    assert client.post(submit,headers=a,json={'answers':answers}).status_code==409
    assert client.get(path,headers=a).json()[0]['quiz_result']['score']==4


def test_invalid_quiz_does_not_publish_answers(backend):
    client,sessions,a,*_=backend
    path,_=setup(backend)
    process_chat(sessions,Model())
    class BadModel:
        def ask(self,prompt):return '{"secret":"private"}', 'bad'
    process_chat(sessions,BadModel())
    turn=client.get(path,headers=a).json()[0]
    assert turn['status']=='failed' and turn['quiz'] is None
    assert turn['provenance']['agent_trace'][2]['status']=='failed'
    assert 'private' not in json.dumps(turn)


@pytest.mark.parametrize('message',['quiz on me this','Quiz me on this','tạo cho tui quiz để tui chọn đáp án','tạo bài trắc nghiệm','quiz'])
def test_intent(message):
    assert wants_quiz(message)


def test_non_quiz_intent():
    assert not wants_quiz('quiz nghĩa là gì?')
    assert not wants_quiz('không tạo quiz')
    assert not wants_quiz('quiz me','chat')
    assert wants_quiz('Some vocabulary','quiz')
