import httpx
from sqlalchemy import select
from packages.db.models import Exam, ExamAttempt, Document
from packages.core.exam import parse_exam
from apps.chat.agents.exam_agent import analyze_batch,build_analysis_prompt,coach_result,translate_coaching


def process_exam(sessions,model):
    with sessions.begin() as db:
        exam=db.scalar(select(Exam).where(Exam.status.in_(['queued','analyzing']))
            .order_by(Exam.created_at).with_for_update(skip_locked=True).limit(1))
        if exam is None:return False
        doc=db.get(Document,exam.document_id)
        if not doc or doc.owner_id!=exam.owner_id:
            exam.status='failed';exam.error_code='invalid_ownership';return True
        if doc.status=='queued':return False
        if doc.status=='failed':exam.status='failed';exam.error_code='document_extraction_failed';return True
        try:
            if exam.structure is None:
                exam.structure=parse_exam(doc.text,doc.page_count)
                if exam.structure['warnings']:
                    exam.status='needs_review';exam.error_code='incomplete_structure'
                else:exam.status='analyzing'
                return True
            done={q['number'] for q in exam.analysis}
            todo=[q for q in exam.structure['questions'] if q['number'] not in done]
            if not todo:exam.status='ready';return True
            pid=todo[0]['passage_id']
            passage=next(p['text'] for p in exam.structure['passages'] if p['id']==pid)
            group=[q for q in todo if q['passage_id']==pid][:5]
            while len(group)>1 and len(build_analysis_prompt(group,passage))>7900:group.pop()
            exam.analysis=[*exam.analysis,*analyze_batch(group,passage,model)]
            if len(exam.analysis)==len(exam.structure['questions']):exam.status='ready'
        except httpx.HTTPError:exam.status='failed';exam.error_code='model_unavailable'
        except (ValueError,KeyError,TypeError):exam.status='failed';exam.error_code='invalid_exam_analysis'
    return True


def process_exam_feedback(sessions,model):
    with sessions.begin() as db:
        attempt=db.scalar(select(ExamAttempt).where(ExamAttempt.status=='queued')
            .order_by(ExamAttempt.created_at).with_for_update(skip_locked=True).limit(1))
        if attempt is None:return False
        try:
            language=attempt.result.get('response_language','vi')
            if attempt.result.get('coaching_mode')=='translate' and attempt.coaching:
                attempt.coaching=translate_coaching(attempt.coaching,language,model)
            else:
                attempt.coaching=coach_result(attempt.result,model)
            attempt.result={**attempt.result,'coaching_translations':{
                **attempt.result.get('coaching_translations',{}),language:attempt.coaching}}
            attempt.status='ready'
        except (httpx.HTTPError,ValueError,KeyError,TypeError) as error:
            attempt.status='failed'
            attempt.result={**attempt.result,'coaching_error':
                'model_unavailable' if isinstance(error,httpx.HTTPError) else 'invalid_coaching_output'}
    return True
