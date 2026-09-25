import json
from packages.db.models import ChatTurn
from apps.worker.tasks.chat_translation_task import process_chat_translation


def saved_turn(backend, quiz=False):
    client,sessions,a,*_=backend
    thread=client.post('/chat/threads',headers=a,json={}).json()
    questions=[{'question':f'Câu hỏi {i}', 'options':['Một','Hai','Ba','Bốn'],
                'correct':i%4,'explanation':'Giải thích đáp án.','quote':''} for i in range(5)]
    with sessions.begin() as db:
        turn=ChatTurn(thread_id=thread['id'],message='Hello',answer='Xin chào, mình là BlueStudy.',
                      status='succeeded',provenance={},quiz={'title':'Bài kiểm tra','questions':questions} if quiz else None)
        db.add(turn);db.flush();tid=turn.id
    return '/chat/threads/'+thread['id']+'/turns',tid


class Translator:
    def ask(self,prompt,response_language='vi'):
        assert response_language=='en'
        data=json.loads(prompt.split('\n',1)[1])
        quiz=None if data['quiz'] is None else {'title':'Quiz','questions':[
            {'question':f'Question {i}','options':['One','Two','Three','Four'],'explanation':'Answer explained.'}
            for i in range(5)]}
        return json.dumps({'answer':'Hello, I am BlueStudy.','quiz':quiz}),'test'


def test_legacy_chat_translation_cached_private_and_owner_scoped(backend):
    client,sessions,a,b,*_=backend
    path,tid=saved_turn(backend)
    endpoint=path+'/'+tid+'/translation'
    assert client.post(endpoint,headers=b,json={'response_language':'en'}).status_code==404
    assert client.post(endpoint,headers=a,json={'response_language':'xx'}).status_code==422
    queued=client.post(endpoint,headers=a,json={'response_language':'en'}).json()
    assert queued['status']=='succeeded'
    assert queued['provenance']['translation_status']=='queued'
    assert process_chat_translation(sessions,Translator())
    translated=client.get(path,headers=a).json()[0]
    assert translated['answer']=='Xin chào, mình là BlueStudy.'
    assert translated['translations']['en']['answer']=='Hello, I am BlueStudy.'
    assert 'work_context' not in translated
    for language in ['vi','en']:
        assert client.post(endpoint,headers=a,json={'response_language':language}).status_code==202
        assert not process_chat_translation(sessions,Translator())


def test_quiz_translation_keeps_keys_private_and_grading_unchanged(backend):
    client,sessions,a,*_=backend
    path,tid=saved_turn(backend,quiz=True)
    client.post(path+'/'+tid+'/translation',headers=a,json={'response_language':'en'})
    process_chat_translation(sessions,Translator())
    before=client.get(path,headers=a)
    assert '"correct":' not in before.text
    assert '"explanation":' not in before.text
    assert before.json()[0]['translations']['en']['quiz']['questions'][0]['options']==['One','Two','Three','Four']
    result=client.post(path+'/'+tid+'/quiz-submit',headers=a,json={'answers':[i%4 for i in range(5)]}).json()
    assert result['score']==5
    localized=client.get(path,headers=a).json()[0]['translations']['en']['quiz_result']
    assert localized['score']==5 and localized['answers']==result['answers']
    assert localized['feedback'][0]['explanation']=='Answer explained.'
    with sessions() as db:
        original=db.get(ChatTurn,tid)
        assert original.quiz['questions'][0]['options']==['Một','Hai','Ba','Bốn']


def test_failed_translation_does_not_fail_original_answer_and_can_retry(backend):
    client,sessions,a,*_=backend
    path,tid=saved_turn(backend)
    endpoint=path+'/'+tid+'/translation'
    client.post(endpoint,headers=a,json={'response_language':'en'})
    class Bad:
        def ask(self,prompt,response_language='vi'):return 'invalid JSON','test'
    process_chat_translation(sessions,Bad())
    turn=client.get(path,headers=a).json()[0]
    assert turn['status']=='succeeded' and turn['provenance']['translation_status']=='failed'
    client.post(endpoint,headers=a,json={'response_language':'en'})
    process_chat_translation(sessions,Translator())
    assert client.get(path,headers=a).json()[0]['provenance']['translation_status']=='ready'
