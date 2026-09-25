from uuid import uuid4
from packages.core.speaking_bank import PRACTICE_SETS
from tests.integration.test_speaking import words, Model
from apps.worker.tasks.speaking_task import process_speaking
from apps.worker.tasks.speaking_task import coach


def test_bank_has_three_complete_parts_and_requested_example():
    assert len(PRACTICE_SETS)==16
    for pack in PRACTICE_SETS:
        a,b,c=pack['parts']
        assert len(a['topics'])==2 and all(len(t['questions'])==3 for t in a['topics'])
        assert len(a['sample_segments'])==6
        assert len(b['options'])==3 and len(c['points'])==3
        assert [p['preparation_seconds'] for p in pack['parts']]==[0,60,60]
        assert [p['speaking_seconds'] for p in pack['parts']]==[180,180,240]
        assert all(p['reference_answer'] and p['source']=='authored_practice' for p in pack['parts'])
    assert PRACTICE_SETS[0]['parts'][0]['topics'][0]['title']=='Morning Routines'
    assert PRACTICE_SETS[0]['parts'][1]['options']==['My living room','A local cinema','A garden']
    assert PRACTICE_SETS[0]['parts'][2]['topic']=='Causes of Stress in the Modern Workplace'


def test_set_ownership_modes_and_four_minute_limit(backend):
    client,sessions,a,b,*_=backend
    assert client.get('/speaking/practice-sets').status_code==401
    assert len(client.get('/speaking/practice-sets',headers=a).json())==16
    result=client.post('/speaking/practice-sets/vstep-01/sessions',headers=a)
    assert result.status_code==201
    rows=result.json()
    assert len(rows)==3 and all(r['status']=='ready' for r in rows)
    assert len({r['activity']['group_id'] for r in rows})==1
    assert client.get('/speaking/sessions/'+rows[0]['id'],headers=b).status_code==404
    body={'id':str(uuid4()),'words':[{'text':'hello','start':230000,'end':230200}],'practice_mode':'model'}
    assert client.post('/speaking/sessions/'+rows[0]['id']+'/attempts',headers=a,json=body).status_code==422
    answer=client.post('/speaking/sessions/'+rows[2]['id']+'/attempts',headers=a,json=body)
    assert answer.status_code==202 and answer.json()['metrics']['practice_mode']=='model'
    assert 'reference_similarity_percent' in answer.json()['metrics']
    class CheckingModel(Model):
        def ask_material(self,prompt,**kwargs):
            assert '"part": 3' in prompt
            assert '"practice_mode": "model"' in prompt
            return super().ask_material(prompt,**kwargs)
    assert process_speaking(sessions,CheckingModel())
    saved=client.get('/speaking/sessions/'+rows[2]['id'],headers=a).json()['attempts'][0]
    assert saved['coaching']['practice_mode']=='model' and saved['coaching']['overall'] is None
    body={'id':str(uuid4()),'words':words(),'practice_mode':'independent'}
    independent=client.post('/speaking/sessions/'+rows[2]['id']+'/attempts',headers=a,json=body).json()
    assert 'reference_similarity_percent' not in independent['metrics']
    assert client.post('/speaking/practice-sets/not-real/sessions',headers=a).status_code==404


def test_long_response_fits_coaching_context():
    from types import SimpleNamespace
    from packages.core.speaking import analyse_timing
    from packages.core.speaking_bank import question_text
    w=words('study '*800)
    attempt=SimpleNamespace(words=w,transcript='study '*800,metrics=analyse_timing(w))
    part=PRACTICE_SETS[0]['parts'][0]
    session=SimpleNamespace(question=question_text(part),activity=part)
    class CheckLength(Model):
        def ask_material(self,prompt,**kwargs):
            assert len(prompt)<7900
            assert attempt.transcript in prompt
            return super().ask_material(prompt,**kwargs)
    assert coach(attempt,session,CheckLength())['overall']==3


def test_individual_question_uses_only_its_reference_and_prompt(backend):
    client,sessions,a,*_=backend
    rows=client.post('/speaking/practice-sets/vstep-02/sessions',headers=a).json()
    segment=rows[0]['activity']['sample_segments'][1]
    body={'id':str(uuid4()),'words':words(segment['text']),'practice_mode':'model','question_index':1}
    path='/speaking/sessions/'+rows[0]['id']
    result=client.post(path+'/attempts',headers=a,json=body)
    assert result.status_code==202
    assert result.json()['metrics']['reference_similarity_percent']==100
    assert result.json()['metrics']['question_label']==segment['label']
    class ScopedModel(Model):
        def ask_material(self,prompt,**kwargs):
            assert '"scope": "single_question"' in prompt
            assert segment['label'] in prompt
            assert rows[0]['activity']['sample_segments'][0]['label'] not in prompt
            return super().ask_material(prompt,**kwargs)
    assert process_speaking(sessions,ScopedModel())
    body['id']=str(uuid4())
    assert client.post('/speaking/sessions/'+rows[1]['id']+'/attempts',headers=a,json=body).status_code==422
    body['words']=[{'text':'late','start':70000,'end':70100}]
    assert client.post(path+'/attempts',headers=a,json=body).status_code==422
