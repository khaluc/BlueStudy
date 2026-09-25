import json
from sqlalchemy import select
from packages.db.models import Exam,ExamAttempt
from apps.worker.tasks.exam_task import process_exam,process_exam_feedback

SOURCE='''Read the following passage and answer questions 1 to 2.
Libraries lend books. Parks provide shade.
Question 1. What do libraries lend?
A. Books B. Cars C. Houses D. Planes
Question 2. What provides shade?
A. Oceans B. Parks C. Computers D. Roads'''


class Model:
    last_metadata={'provider':'test'}
    def ask_material(self,prompt):
        if 'learning coach' in prompt:
            return json.dumps({'summary':'Complete the unanswered question before drawing conclusions.',
                'roadmap':[{'day':1,'skill':'detail','minutes':15,'goal':'Read for details',
                    'activities':['Revisit the sentence about parks.','Answer question 2.'],
                    'question_numbers':[2],'success_criteria':'Locate and explain the supporting sentence.'}]}),'test'
        assert 'Libraries lend books' in prompt
        return json.dumps({'questions':[
            {'number':1,'topic':'reading','skill':'detail','correct':0,'explanation':'Libraries lend books.',
             'evidence':'Libraries lend books.','uncertain':False},
            {'number':2,'topic':'reading','skill':'detail','correct':1,'explanation':'Parks provide shade.',
             'evidence':'Parks provide shade.','uncertain':False}]}),'test'
    def ask(self,prompt):return json.dumps({'summary':'Review details.','practice':['Read the sentence about parks.']}),'test'


def create_exam(backend):
    client,_,a,*_=backend
    doc=client.post('/documents',headers=a,json={'title':'Exam','text':SOURCE}).json()
    response=client.post('/exams',headers=a,json={'document_id':doc['id']})
    assert response.status_code==202
    return doc,response.json()


def test_full_exam_private_key_scoring_coaching_and_cascade(backend):
    client,sessions,a,b,*_=backend
    doc,exam=create_exam(backend);path='/exams/'+exam['id']
    assert client.get('/exams').status_code==401
    assert client.get(path,headers=b).status_code==404
    assert client.post('/exams',headers=b,json={'document_id':doc['id']}).status_code==404
    assert client.post('/exams',headers=a,json={'document_id':doc['id']}).json()['id']==exam['id']
    assert client.post(path+'/attempts',headers=a,json={'answers':[0,1]}).status_code==409
    assert process_exam(sessions,Model())
    assert process_exam(sessions,Model())
    response=client.get(path,headers=a)
    assert response.json()['status']=='ready'
    assert response.json()['classified_count']==2
    assert '"correct"' not in response.text and '"explanation"' not in response.text
    assert client.post(path+'/attempts',headers=b,json={'answers':[0,1]}).status_code==404
    assert client.post(path+'/attempts',headers=a,json={'answers':[True,1]}).status_code==422
    assert client.post(path+'/attempts',headers=a,json={'answers':[0]}).status_code==422
    attempt=client.post(path+'/attempts',headers=a,json={'answers':[0,None]}).json()
    assert attempt['result']['score']==1 and attempt['result']['graded_total']==2
    assert attempt['result']['skills'][0]['questions']==[2]
    assert attempt['result']['answer_key_status']=='ai_unverified'
    assert process_exam_feedback(sessions,Model())
    assert client.get(path+'/attempts',headers=a).json()[0]['coaching']['practice']
    coaching_path=path+'/attempts/'+attempt['id']+'/coaching'
    assert client.post(coaching_path,headers=b,json={}).status_code==404
    retried=client.post(coaching_path,headers=a,json={'response_language':'en'})
    assert retried.status_code==202
    assert retried.json()['result']['response_language']=='en'
    assert retried.json()['result']['score']==1
    assert retried.json()['answers']==[0,None]
    assert retried.json()['status']=='queued'
    assert client.post(coaching_path,headers=a,json={}).json()['result']['response_language']=='en'
    assert client.get(path+'/attempts',headers=b).status_code==404
    client.delete('/documents/'+doc['id'],headers=a)
    with sessions() as db:
        assert db.scalar(select(Exam)) is None and db.scalar(select(ExamAttempt)) is None


def test_missing_question_blocks_grading(backend):
    client,sessions,a,*_=backend
    doc=client.post('/documents',headers=a,json={'title':'Broken','text':SOURCE.replace('Question 2.','Question 3.')}).json()
    exam=client.post('/exams',headers=a,json={'document_id':doc['id']}).json()
    process_exam(sessions,Model())
    result=client.get('/exams/'+exam['id'],headers=a).json()
    assert result['status']=='needs_review' and result['structure']['warnings']


def test_unsupported_evidence_not_graded(backend):
    client,sessions,a,*_=backend
    _,exam=create_exam(backend)
    class BadEvidence(Model):
        def ask_material(self,prompt):
            raw,name=super().ask_material(prompt)
            data=json.loads(raw);data['questions'][0]['evidence']='Invented source'
            return json.dumps(data),name
    process_exam(sessions,BadEvidence());process_exam(sessions,BadEvidence())
    attempt=client.post('/exams/'+exam['id']+'/attempts',headers=a,json={'answers':[0,1]}).json()
    assert attempt['result']['ungraded']==1 and attempt['result']['graded_total']==1


def test_failed_coaching_can_retry_without_resubmitting_or_changing_score(backend):
    client,sessions,a,*_=backend
    _,exam=create_exam(backend)
    process_exam(sessions,Model());process_exam(sessions,Model())
    path='/exams/'+exam['id']+'/attempts'
    submitted=client.post(path,headers=a,json={'answers':[0,None]}).json()
    class Broken(Model):
        def ask_material(self,prompt):return '{"summary":', 'test'
    process_exam_feedback(sessions,Broken())
    failed=client.get(path,headers=a).json()[0]
    assert failed['status']=='failed'
    assert failed['result']['coaching_error']=='invalid_coaching_output'
    assert failed['result']['score']==1
    assert client.post(path+'/'+submitted['id']+'/coaching',headers=a,json={}).status_code==202
    process_exam_feedback(sessions,Model())
    rows=client.get(path,headers=a).json()
    assert len(rows)==1 and rows[0]['status']=='ready'
    assert rows[0]['coaching']['roadmap'][0]['question_numbers']==[2]
    assert 'coaching_error' not in rows[0]['result']


def test_existing_vietnamese_assessment_translates_and_switches_from_cache(backend):
    client,sessions,a,b,*_=backend
    _,exam=create_exam(backend)
    process_exam(sessions,Model());process_exam(sessions,Model())
    path='/exams/'+exam['id']+'/attempts'
    original=client.post(path,headers=a,json={'answers':[0,None]}).json()
    legacy={'summary':'Bạn cần ôn đọc hiểu.','practice':['Đọc lại câu 2.']}
    with sessions.begin() as db:
        row=db.get(ExamAttempt,original['id']);row.status='ready';row.coaching=legacy
    endpoint=path+'/'+original['id']+'/coaching'
    body={'response_language':'en','translate_existing':True}
    assert client.post(endpoint,headers=b,json=body).status_code==404
    queued=client.post(endpoint,headers=a,json=body).json()
    assert queued['coaching']['summary']==legacy['summary']
    assert queued['status']=='queued'
    class Translation:
        def ask(self,prompt,response_language='vi'):
            assert response_language=='en'
            assert 'Do not reassess' in prompt
            return json.dumps({'summary':'Review reading comprehension.',
                'practice':['Read question 2 again.'],'roadmap':[]}),'translator'
    process_exam_feedback(sessions,Translation())
    translated=client.get(path,headers=a).json()[0]
    assert translated['coaching']['summary']=='Review reading comprehension.'
    assert translated['result']['feedback']==original['result']['feedback']
    assert translated['result']['score']==original['result']['score']
    for language,summary in [('vi',legacy['summary']),('en','Review reading comprehension.')]:
        response=client.post(endpoint,headers=a,json={**body,'response_language':language}).json()
        assert response['status']=='ready'
        assert response['coaching']['summary']==summary
        assert response['answers']==original['answers']
        assert not process_exam_feedback(sessions,Translation())
