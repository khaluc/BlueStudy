"""Conservative extraction of numbered A-D exam questions, not question generation."""
import re
from collections import defaultdict
from pydantic import Field, StrictInt, model_validator
from typing import Literal
from packages.core.material import Strict

TOPICS = {'grammar':'Ngữ pháp','vocabulary':'Từ vựng','reading':'Đọc hiểu','cohesion':'Liên kết và sắp xếp văn bản'}
SKILLS = {'word_form':'Từ loại','word_order':'Trật tự từ','verb_form':'Dạng động từ',
    'preposition':'Giới từ','collocation':'Cụm từ','connector':'Từ nối','determiner':'Từ hạn định',
    'vocabulary_context':'Từ vựng trong ngữ cảnh','sentence_structure':'Cấu trúc câu',
    'sentence_order':'Sắp xếp câu','detail':'Thông tin chi tiết','main_idea':'Ý chính',
    'inference':'Suy luận','reference':'Từ quy chiếu','paraphrase':'Diễn đạt tương đương',
    'sentence_insertion':'Chèn câu','other':'Cần phân loại thêm'}


def parse_exam(text, page_count=10):
    # Remove standalone page counters only; preserve numbered blanks, questions and choices.
    lines=[line for line in text.replace('\r','').splitlines()
           if not (line.strip().isdigit() and 1<=int(line.strip())<=page_count)]
    clean='\n'.join(lines)
    # Explicit exam end markers and invigilator notes are not part of option D.
    clean=re.split(r'(?im)^[\s—–-]*(?:HẾT|THE END)[\s—–-]*$',clean,maxsplit=1)[0]
    sections=re.split(r'(?im)(?=^(?:Read the following|Read the passage|Mark the letter)\b)',clean)
    passages=[]; questions=[]; warnings=[]
    for section in sections:
        matches=list(re.finditer(r'(?im)^\s*(?:Question|Câu)\s+(\d+)\s*[.:]',section))
        if not matches:continue
        context=section[:matches[0].start()].strip()
        pid=str(len(passages)+1)
        passages.append({'id':pid,'text':context})
        for index,match in enumerate(matches):
            number=int(match.group(1))
            block=section[match.end():matches[index+1].start() if index+1<len(matches) else len(section)].strip()
            options=list(re.finditer(r'(?<![A-Za-z])([ABCD])\.\s+',block))
            if [m.group(1) for m in options]!=list('ABCD'):
                warnings.append(f'Câu {number}: chưa tách đủ bốn lựa chọn A–D, cần kiểm tra tài liệu.')
                continue
            choices=[block[m.end():options[i+1].start() if i+1<4 else len(block)].strip() for i,m in enumerate(options)]
            if any(not value for value in choices):
                warnings.append(f'Câu {number}: có lựa chọn trống.');continue
            questions.append({'number':number,'stem':block[:options[0].start()].strip(),
                'options':choices,'passage_id':pid,'source_fragment':match.group(0).strip()+' '+block})
    numbers=[q['number'] for q in questions]
    if len(set(numbers))!=len(numbers):raise ValueError('Duplicate question numbers')
    if not questions or len(questions)>100:raise ValueError('No supported exam questions or too many questions')
    expected=re.search(r'(\d+)\s*câu\s*trắc\s*nghiệm',clean,re.I)
    expected_count=int(expected.group(1)) if expected else max(numbers)
    missing=sorted(set(range(1,expected_count+1))-set(numbers))
    if missing:warnings.append('Chưa trích xuất được câu: '+', '.join(map(str,missing)))
    return {'passages':passages,'questions':questions,'warnings':warnings,'expected_count':expected_count}


class QuestionAnalysis(Strict):
    number: StrictInt = Field(ge=1,le=100)
    topic: Literal['grammar','vocabulary','reading','cohesion']
    skill: str
    correct: StrictInt | None = Field(default=None,ge=0,le=3)
    explanation: str = Field(min_length=1,max_length=1000)
    evidence: str = Field(default='',max_length=1200)
    uncertain: bool = False

    @model_validator(mode='after')
    def valid_skill(self):
        if self.skill not in SKILLS:raise ValueError('Unknown skill')
        if self.uncertain:self.correct=None
        return self


class AnalysisBatch(Strict):
    questions: list[QuestionAnalysis] = Field(min_length=1,max_length=5)


def grade_exam(structure, analysis, answers):
    by_number={item['number']:item for item in analysis}
    feedback=[]; groups=defaultdict(lambda:{'correct':0,'total':0,'questions':[]})
    for q,answer in zip(structure['questions'],answers,strict=True):
        item=by_number[q['number']]
        correct=item['correct']
        row={'number':q['number'],'selected':answer,'correct':correct,'is_correct':answer==correct if correct is not None else None,
             'topic':item['topic'],'skill':item['skill'],'explanation':item['explanation'],'evidence':item.get('evidence','')}
        feedback.append(row)
        if correct is not None:
            group=groups[item['skill']];group['total']+=1;group['correct']+=int(answer==correct)
            if answer!=correct:group['questions'].append(q['number'])
    scored=[row for row in feedback if row['correct'] is not None]
    return {'score':sum(row['is_correct'] for row in scored),'graded_total':len(scored),'total':len(feedback),
            'ungraded':len(feedback)-len(scored),'answer_key_status':'ai_unverified','feedback':feedback,
            'skills':[{'skill':skill,'label':SKILLS[skill],**counts} for skill,counts in groups.items()]}
