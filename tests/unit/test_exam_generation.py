import json
from types import SimpleNamespace
import pytest
from apps.chat.agents.material_agent import generate
from apps.chat.agents.inline_quiz_agent import generate_quiz

SOURCE = ('Mã đề: 1144\nThời gian làm bài: 50 phút\n'
          'Read the following and choose the option that best fits each of the numbered blanks.\n'
          'The harder we try, (1)_____ our future will be!\n'
          'Question 1. A. greener B. greenest C. the greener D. the greenest')
QUOTE = 'The harder we try, (1)_____ our future will be!'


def items(bad=False):
    return [{'question':('Đề thi này năm bao nhiêu?' if bad and i==0 else f'Câu {i+1}: Cấu trúc so sánh kép trong câu này là gì?'),
             'options':['the + comparative','as ... as','superlative','less than'],
             'correct':0,'explanation':'Dùng cấu trúc so sánh kép.','quote':QUOTE} for i in range(5)]


class Model:
    def __init__(self,payload):self.payload=payload
    def ask(self,prompt):
        assert '1144' not in prompt and '50 phút' not in prompt
        assert QUOTE in prompt
        assert 'NOT trivia' in prompt
        return json.dumps(self.payload,ensure_ascii=False),'test-model'


@pytest.mark.parametrize('bad',[False,True])
def test_bundle_uses_filtered_learning_source_and_checks_relevance(bad):
    questions=items(bad)
    payload={'summary':'Ôn cấu trúc so sánh kép.','notes':['The + comparative, the + comparative.'],
             'cards':[{'front':q['question'],'back':q['explanation'],'quote':q['quote']} for q in questions],
             'quiz':questions}
    context=SimpleNamespace(text=SOURCE,document_id='example',language_level='basic')
    if bad:
        with pytest.raises(ValueError):generate(context,Model(payload))
    else:
        assert len(generate(context,Model(payload)).content['quiz'])==5


@pytest.mark.parametrize('bad',[False,True])
def test_inline_quiz_uses_same_relevance_checks(bad):
    model=Model({'title':'So sánh kép','questions':items(bad)})
    if bad:
        with pytest.raises(ValueError):generate_quiz({'source':SOURCE},'Tạo quiz','basic',model)
    else:
        assert len(generate_quiz({'source':SOURCE},'Tạo quiz','basic',model)[0]['questions'])==5
