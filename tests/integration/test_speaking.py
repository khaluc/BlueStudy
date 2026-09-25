import json
import pytest
from uuid import uuid4
from unittest.mock import patch
from pydantic import SecretStr
from packages.core.speaking import analyse_timing
from apps.worker.tasks.speaking_task import process_speaking


def words(text='Um I I think research helps people understand the world because evidence gives us a reliable way to compare different ideas and make informed decisions.'):
    return [{'text':word,'start':i*450,'end':i*450+300,'confidence':.99}
            for i,word in enumerate(text.split())]


class Model:
    def ask_material(self,prompt,response_language='en'):
        if 'Create one English' in prompt:
            return json.dumps({'question':'Why is evidence important when people make decisions?'}),'test'
        bilingual={'en':'Support your opinion with an example.','vi':'Hãy thêm ví dụ cho quan điểm.'}
        data={'summary':bilingual,'corrections':[],
              'sample_answer':'Evidence helps us compare ideas and make better decisions.',
              'next_steps':[bilingual]}
        for key in ('fluency','grammar','vocabulary','coherence','relevance'):
            data[key]={'score':3,'feedback':bilingual}
        return json.dumps(data),'test'


def session(backend):
    client,sessions,a,*_=backend
    row=client.post('/speaking/sessions',headers=a,json={'lesson':'opinion'}).json()
    assert process_speaking(sessions,Model())
    return '/speaking/sessions/'+row['id']


@pytest.mark.parametrize('nested', [False, True])
def test_speaking_history_coaching_retry_and_isolation(backend, nested):
    client,sessions,a,b,*_=backend
    path=session(backend)
    assert client.get(path,headers=b).status_code==404
    assert client.get(path,headers=a).json()['session']['status']=='ready'
    body={'id':str(uuid4()),'words':words(),'response_language':'en'}
    response=client.post(path+'/attempts',headers=a,json=body)
    assert response.status_code==202
    assert client.post(path+'/attempts',headers=b,json=body).status_code==404
    assert client.post(path+'/attempts',headers=a,json=body).json()['id']==body['id']
    class NestedModel(Model):
        def ask_material(self, *args, **kwargs):
            answer, name = super().ask_material(*args, **kwargs)
            result = json.loads(answer)
            if nested:
                result['dimensions'] = {k:result.pop(k) for k in ('fluency','grammar','vocabulary','coherence','relevance')}
            return json.dumps(result), name
    assert process_speaking(sessions,NestedModel())
    row=client.get(path,headers=a).json()['attempts'][0]
    assert row['coaching']['overall']==3
    assert row['coaching']['pronunciation']['score'] is None
    assert row['metrics']['pronunciation_score'] is None
    assert {'filler','repetition'} <= {e['kind'] for e in row['metrics']['events']}
    body['id']=str(uuid4());body['words']=words('I think so')
    assert client.post(path+'/attempts',headers=a,json=body).status_code==202
    assert process_speaking(sessions,Model())
    rows=client.get(path,headers=a).json()['attempts']
    assert len(rows)==2 and rows[1]['coaching']['overall'] is None
    assert rows[1]['coaching']['grammar']['score'] is None
    assert client.delete(path,headers=b).status_code==404
    assert client.delete(path,headers=a).status_code==204
    assert client.get(path,headers=a).status_code==404


def test_invalid_timestamps_and_model_failure(backend):
    client,sessions,a,*_=backend
    path=session(backend)
    invalid=words('hello world');invalid[1]['start']=0
    assert client.post(path+'/attempts',headers=a,json={'id':str(uuid4()),'words':invalid}).status_code==422
    response=client.post(path+'/attempts',headers=a,json={'id':str(uuid4()),'words':words()})
    attempt=response.json()['id']
    class Broken:
        def ask_material(self,*args,**kwargs):return '{}','broken'
    assert process_speaking(sessions,Broken())
    row=client.get(path,headers=a).json()['attempts'][0]
    assert row['status']=='failed' and row['coaching'] is None
    assert client.post(path+'/attempts/'+attempt+'/retry',headers=a).status_code==202
    assert process_speaking(sessions,Model())
    assert client.get(path,headers=a).json()['attempts'][0]['status']=='ready'


def test_token_auth_configuration_and_secret_boundary(backend):
    client,_,a,*_=backend
    client.app.state.settings.assemblyai_api_key=SecretStr('')
    assert client.post('/speaking/token').status_code==401
    assert client.post('/speaking/token',headers=a).status_code==503
    client.app.state.settings.assemblyai_api_key=SecretStr('server-secret')
    with patch('apps.api.routers.speaking.httpx.Client') as mock:
        response=mock.return_value.__enter__.return_value.get.return_value
        response.json.return_value={'token':'short-lived-token'}
        result=client.post('/speaking/token',headers=a)
        assert result.status_code==200
        assert 'server-secret' not in result.text
        assert result.headers['cache-control']=='no-store'
        call=mock.return_value.__enter__.return_value.get.call_args
        assert call.kwargs['headers']['Authorization']=='server-secret'
        assert call.kwargs['params']['expires_in_seconds']==60


def test_timing_flags_are_observations_not_pronunciation_scores():
    result=analyse_timing([{'text':'um','start':0,'end':200},
        {'text':'research','start':1800,'end':3200}])
    assert {e['kind'] for e in result['events']}=={'filler','pause','long_word'}
    assert result['pronunciation_score'] is None
