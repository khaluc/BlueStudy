"""Private learning evidence; no source documents or recordings are returned."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from apps.api.dependencies import current_user, get_db
from packages.db.models import SpeakingAttempt, ExamAttempt
from packages.core.exam_review import review_metrics

router = APIRouter(tags=['learning'])


@router.get('/learning-map')
def learning_map(response: Response, user=Depends(current_user), db=Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    speaking = db.scalars(select(SpeakingAttempt).where(SpeakingAttempt.owner_id == user.id)
        .order_by(SpeakingAttempt.created_at.desc()).limit(50)).all()
    exams = db.scalars(select(ExamAttempt).where(ExamAttempt.owner_id == user.id)
        .order_by(ExamAttempt.created_at.desc()).limit(50)).all()
    return {
        'speaking': [{'id': a.id, 'session_id': a.session_id, 'date': a.created_at,
            'mode': (a.metrics or {}).get('practice_mode', 'independent'),
            'question': (a.metrics or {}).get('question_label'),
            'status': a.status, 'coaching': a.coaching} for a in speaking],
        'exams': [{'id': a.id, 'exam_id': a.exam_id, 'date': a.created_at,
            'total': a.result.get('total', 0), 'metrics': review_metrics(a.result),
            'coaching': a.coaching, 'translations': a.result.get('coaching_translations', {})}
            for a in exams],
        'limit_per_activity': 50,
    }
