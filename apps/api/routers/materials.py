from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field, StrictInt
from sqlalchemy import select
from apps.api.dependencies import current_user, get_db
from apps.api.routers.sessions import owned_session
from apps.api.schemas.common import Input
from packages.curriculum.grade9_topics import TOPICS, suggest
from packages.db.models import Material, QuizAttempt, StudySession

router = APIRouter(tags=['study materials'])


def owned_material(db, material_id, owner_id):
    material = db.scalar(select(Material).where(Material.id == str(material_id), Material.owner_id == owner_id))
    if material is None:
        raise HTTPException(404, 'Không tìm thấy bộ học.')
    return material


def public_material(material):
    # Quiz rationales/quotes can disclose the correct choice: release only after submission.
    content = {key: value for key, value in material.content.items() if key != 'quiz'}
    content['quiz'] = [{key: q[key] for key in ('question', 'options')} for q in material.content['quiz']]
    return dict(id=material.id, session_id=material.session_id, content=content,
                provenance=material.provenance, created_at=material.created_at)


@router.get('/curriculum')
def curriculum(user=Depends(current_user)):
    return TOPICS


@router.get('/sessions/{session_id}/curriculum')
def mapping(session_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    session = owned_session(db, session_id, user.id)
    matches = suggest(session.source_text)
    return {'status': 'learner_selected' if session.topic_id else ('suggested' if matches else 'unmatched'),
            'selected_topic_id': session.topic_id, 'matches': matches}


class TopicSelection(Input):
    topic_id: str | None = Field(default=None, max_length=30)


@router.patch('/sessions/{session_id}/curriculum')
def select_topic(session_id: UUID, body: TopicSelection, user=Depends(current_user), db=Depends(get_db)):
    session = owned_session(db, session_id, user.id)
    if body.topic_id is not None and body.topic_id not in {t['id'] for t in TOPICS}:
        raise HTTPException(422, 'Chủ đề không hợp lệ.')
    session.topic_id = body.topic_id
    db.commit()
    return {'topic_id': session.topic_id, 'status': 'learner_selected' if session.topic_id else 'unmatched'}


@router.get('/sessions/{session_id}/materials')
def materials(session_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    owned_session(db, session_id, user.id)
    rows = db.scalars(select(Material).where(Material.owner_id == user.id, Material.session_id == str(session_id))
                      .order_by(Material.created_at.desc()).limit(50)).all()
    return [public_material(row) for row in rows]


@router.get('/materials/{material_id}')
def material(material_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    return public_material(owned_material(db, material_id, user.id))


class Submission(Input):
    answers: list[Annotated[StrictInt, Field(ge=0, le=3)]] = Field(min_length=5, max_length=5)


@router.post('/materials/{material_id}/attempts', status_code=201)
def submit(material_id: UUID, body: Submission, user=Depends(current_user), db=Depends(get_db)):
    material = owned_material(db, material_id, user.id)
    quiz = material.content['quiz']
    score = sum(answer == question['correct'] for answer, question in zip(body.answers, quiz, strict=True))
    attempt = QuizAttempt(owner_id=user.id, material_id=material.id, answers=body.answers, score=score)
    db.add(attempt)
    db.commit()
    return {'id': attempt.id, 'score': score, 'total': len(quiz), 'feedback': quiz}


@router.get('/users/me/progress')
def progress(user=Depends(current_user), db=Depends(get_db)):
    rows = db.scalars(select(QuizAttempt).where(QuizAttempt.owner_id == user.id)
                      .order_by(QuizAttempt.created_at.desc()).limit(100)).all()
    topic_scores = {}
    associations = db.execute(select(Material.id, StudySession.topic_id)
        .join(StudySession, Material.session_id == StudySession.id)
        .where(Material.owner_id == user.id, StudySession.owner_id == user.id,
               Material.id.in_([r.material_id for r in rows]))).all() if rows else []
    material_topics = dict(associations)
    for row in rows:
        topic = material_topics.get(row.material_id)
        if topic:
            topic_scores.setdefault(topic, []).append(row.score)
    topics = []
    for topic in TOPICS:
        scores = topic_scores.get(topic['id'], [])
        average = round(sum(scores) / len(scores) * 20) if scores else None
        topics.append(dict(topic_id=topic['id'], title=topic['title'], attempts=len(scores),
                           average_percent=average, status='insufficient_data' if len(scores)<3 else
                           ('needs_practice' if average<60 else 'stronger' if average>=80 else 'practising')))
    return {'attempt_count': len(rows), 'window': 'latest_100', 'topics': topics,
            'average_percent': round(sum(row.score for row in rows) / (len(rows) * 5) * 100) if rows else None,
            'attempts': [dict(id=r.id, material_id=r.material_id, score=r.score, total=5,
                              created_at=r.created_at) for r in rows]}


@router.get('/users/me/review')
def review(user=Depends(current_user), db=Depends(get_db)):
    rows = db.execute(select(QuizAttempt, Material).join(Material, QuizAttempt.material_id == Material.id)
                      .where(QuizAttempt.owner_id == user.id, Material.owner_id == user.id)
                      .order_by(QuizAttempt.created_at.desc()).limit(20)).all()
    items, seen = [], set()
    for attempt, material in rows:
        for index, (answer, question) in enumerate(zip(attempt.answers, material.content['quiz'])):
            key = (material.id, index)
            if key in seen:
                continue
            seen.add(key)
            if answer != question['correct']:
                items.append(dict(material_id=material.id, session_id=material.session_id,
                                  question_index=index, selected=answer, **question))
    return items


@router.delete('/users/me/progress', status_code=204)
def clear_progress(user=Depends(current_user), db=Depends(get_db)):
    from sqlalchemy import delete
    db.execute(delete(QuizAttempt).where(QuizAttempt.owner_id == user.id))
    db.commit()


@router.get('/sessions')
def history(limit: int = Query(30, ge=1, le=100), user=Depends(current_user), db=Depends(get_db)):
    return db.scalars(select(StudySession).where(StudySession.owner_id == user.id)
                      .order_by(StudySession.created_at.desc()).limit(limit)).all()
