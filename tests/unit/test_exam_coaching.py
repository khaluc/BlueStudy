import json
import pytest
from apps.chat.agents.exam_agent import coach_result,translate_coaching
from packages.core.exam_review import review_metrics


def result():
    return {'score':1,'graded_total':3,'total':4,'ungraded':1,'response_language':'en',
        'feedback':[
            {'number':1,'skill':'detail','selected':0,'correct':0,'is_correct':True},
            {'number':2,'skill':'detail','selected':1,'correct':0,'is_correct':False},
            {'number':3,'skill':'verb_form','selected':None,'correct':0,'is_correct':False},
            {'number':4,'skill':'verb_form','selected':1,'correct':None,'is_correct':None}]}


class Model:
    def ask(self, prompt):
        raise AssertionError('Use structured generation, not short chat output')

    def ask_material(self, prompt, response_language='vi'):
        assert response_language=='en'
        assert 'An unanswered question is NOT evidence' in prompt
        self.stats=json.loads(prompt.split('\n',1)[1])
        return json.dumps({'summary':'Review the detail question you missed; complete the skipped question.',
            'roadmap':[{'day':1,'skill':'detail','minutes':20,'goal':'Find supporting details',
                'activities':['Find the supporting sentence.','Explain each option.'],
                'question_numbers':[2],'success_criteria':'Explain why one answer matches the evidence.'}]}),'test'


def test_metrics_distinguish_skips_mistakes_and_unknown_keys():
    metrics=review_metrics(result())
    assert metrics['answered']==3 and metrics['unanswered']==1 and metrics['incorrect_answered']==1
    assert metrics['skills'][0]['wrong_questions']==[2]
    assert metrics['skills'][1]['wrong_questions']==[]
    assert metrics['skills'][1]['unanswered_questions']==[3]
    assert metrics['skills'][1]['ungraded_questions']==[4]


def test_coach_uses_structured_generation_and_saves_language():
    model=Model()
    plan=coach_result(result(),model)
    assert plan['roadmap'][0]['question_numbers']==[2]
    assert plan['response_language']=='en' and plan['version']==2
    assert model.stats['incorrect_answered']==1


@pytest.mark.parametrize('change', ['unknown_question','wrong_skill','duplicate_day'])
def test_plan_cannot_invent_question_references(change):
    class Invalid(Model):
        def ask_material(self,prompt,response_language='vi'):
            answer,name=super().ask_material(prompt,response_language)
            data=json.loads(answer)
            if change=='unknown_question':data['roadmap'][0]['question_numbers']=[99]
            if change=='wrong_skill':data['roadmap'][0]['skill']='verb_form'
            if change=='duplicate_day':data['roadmap'].append(data['roadmap'][0])
            return json.dumps(data),name
    with pytest.raises(ValueError):coach_result(result(),Invalid())


def test_translation_preserves_plan_structure_and_references():
    source=coach_result(result(),Model())
    class Translator:
        def ask(self,prompt):raise AssertionError('Use structured generation')
        def ask_material(self,prompt,response_language='vi'):
            return json.dumps({'summary':'Nhận xét đã dịch.','practice':['Mục tiêu đã dịch.'],
                'roadmap':[{'goal':'Mục tiêu đã dịch.','activities':['Đọc lại câu.','Giải thích đáp án.'],
                            'success_criteria':'Tìm được bằng chứng.'}]}),'translator'
    translated=translate_coaching(source,'vi',Translator())
    for key in ['day','skill','minutes','question_numbers']:
        assert translated['roadmap'][0][key]==source['roadmap'][0][key]
    assert translated['response_language']=='vi'
    assert source['response_language']=='en'


def test_translation_rejects_removed_activities():
    source=coach_result(result(),Model())
    class Bad:
        def ask(self,prompt,response_language='vi'):
            return json.dumps({'summary':'Changed','practice':['One'],
                'roadmap':[{'goal':'Goal','activities':['Only one'], 'success_criteria':'Check'}]}),'test'
    with pytest.raises(ValueError):translate_coaching(source,'en',Bad())
