from uuid import UUID, uuid4
from typing import Literal
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import Field, model_validator
from sqlalchemy import select, func
from datetime import timedelta
from apps.api.dependencies import current_user, get_db
from apps.api.schemas.common import Input
from packages.db.base import utcnow
from packages.db.models import SpeakingSession, SpeakingAttempt
from packages.core.speaking import LESSONS, analyse_timing
from packages.core.speaking_bank import PRACTICE_SETS, question_text

router = APIRouter(prefix='/speaking', tags=['speaking'])


def owned(db, session_id, user):
    row = db.scalar(select(SpeakingSession).where(SpeakingSession.id == str(session_id),
                                                SpeakingSession.owner_id == user.id))
    if row is None:
        raise HTTPException(404, 'Speaking session not found')
    return row


@router.get('/config')
def config(request: Request, user=Depends(current_user)):
    return {'configured':bool(request.app.state.settings.assemblyai_api_key.get_secret_value()),
            'provider':'AssemblyAI', 'max_seconds':240, 'lessons':LESSONS}


@router.get('/practice-sets')
def practice_sets(user=Depends(current_user)):
    return PRACTICE_SETS


@router.post('/practice-sets/{set_id}/sessions', status_code=201)
def start_set(set_id: str, user=Depends(current_user), db=Depends(get_db)):
    pack = next((p for p in PRACTICE_SETS if p['id'] == set_id), None)
    if pack is None:
        raise HTTPException(404, 'Practice set not found')
    count = db.scalar(select(func.count()).select_from(SpeakingSession).where(
        SpeakingSession.owner_id == user.id, SpeakingSession.created_at > utcnow() - timedelta(minutes=1)))
    if count >= 9:
        raise HTTPException(429, 'Please wait before opening another practice set.')
    group = str(uuid4())
    rows = [SpeakingSession(owner_id=user.id, lesson='vstep', question=question_text(part),
        status='ready', model='authored-practice',
        activity={**part, 'set_id':pack['id'], 'set_title':pack['title'], 'group_id':group})
        for part in pack['parts']]
    db.add_all(rows); db.commit()
    for row in rows: db.refresh(row)
    return rows


@router.post('/token')
def temporary_token(request: Request, response: Response, user=Depends(current_user)):
    settings = request.app.state.settings
    key = settings.assemblyai_api_key.get_secret_value()
    if not key:
        raise HTTPException(503, 'Set ASSEMBLYAI_API_KEY on the server to enable the microphone.')
    # Per-process throttling complements provider limits; no long-lived key reaches the browser.
    import time
    now = time.monotonic()
    with request.app.state.speaking_token_lock:
        recent = [t for t in request.app.state.speaking_tokens.get(user.id, []) if now - t < 60]
        if len(recent) >= 4:
            raise HTTPException(429, 'Please wait before starting another recording.')
        request.app.state.speaking_tokens[user.id] = recent + [now]
    try:
        with httpx.Client(timeout=15, trust_env=False) as client:
            result = client.get('https://streaming.assemblyai.com/v3/token',
                headers={'Authorization':key},
                params={'expires_in_seconds':60, 'max_session_duration_seconds':300})
            result.raise_for_status()
            token = result.json()['token']
        if not isinstance(token, str) or not token:
            raise ValueError('Invalid token')
    except (httpx.HTTPError, ValueError, KeyError):
        raise HTTPException(502, 'AssemblyAI is unavailable. Check the server key and account balance.') from None
    response.headers['Cache-Control'] = 'no-store'
    return {'token':token, 'speech_model':settings.assemblyai_speech_model}


class SessionInput(Input):
    lesson: Literal['explain', 'opinion', 'compare', 'presentation']


@router.post('/sessions', status_code=202)
def create_session(body: SessionInput, user=Depends(current_user), db=Depends(get_db)):
    count = db.scalar(select(func.count()).select_from(SpeakingSession).where(
        SpeakingSession.owner_id == user.id, SpeakingSession.created_at > utcnow() - timedelta(minutes=1)))
    if count >= 6:
        raise HTTPException(429, 'Please wait before requesting more questions.')
    row = SpeakingSession(owner_id=user.id, lesson=body.lesson)
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get('/sessions')
def history(user=Depends(current_user), db=Depends(get_db)):
    return db.scalars(select(SpeakingSession).where(SpeakingSession.owner_id == user.id)
                      .order_by(SpeakingSession.created_at.desc()).limit(50)).all()


@router.get('/sessions/{session_id}')
def session(session_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    row = owned(db, session_id, user)
    attempts = db.scalars(select(SpeakingAttempt).where(SpeakingAttempt.session_id == row.id,
        SpeakingAttempt.owner_id == user.id).order_by(SpeakingAttempt.created_at, SpeakingAttempt.id)).all()
    return {'session':row, 'attempts':attempts}


class Word(Input):
    text: str = Field(min_length=1, max_length=80)
    start: int = Field(ge=0, le=245000)
    end: int = Field(ge=0, le=245000)
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)


class AttemptInput(Input):
    id: UUID
    words: list[Word] = Field(min_length=1, max_length=850)
    response_language: Literal['en', 'vi'] = 'en'
    practice_mode: Literal['independent', 'model'] = 'independent'
    question_index: int | None = Field(default=None, ge=0, le=5, strict=True)

    @model_validator(mode='after')
    def valid_times(self):
        previous_end = 0
        for word in self.words:
            if word.end <= word.start or word.start < previous_end:
                raise ValueError('Word timestamps must be ordered and non-overlapping')
            previous_end = word.end
        if len(' '.join(w.text for w in self.words)) > 5000:
            raise ValueError('Transcript too long; use a shorter response')
        return self


@router.post('/sessions/{session_id}/attempts', status_code=202)
def submit(session_id: UUID, body: AttemptInput, user=Depends(current_user), db=Depends(get_db)):
    row = owned(db, session_id, user)
    if row.status != 'ready':
        raise HTTPException(409, 'Wait for the speaking question.')
    existing = db.get(SpeakingAttempt, str(body.id))
    if existing:
        if existing.owner_id != user.id or existing.session_id != row.id:
            raise HTTPException(409, 'Attempt ID already used')
        return existing
    count = db.scalar(select(func.count()).select_from(SpeakingAttempt).where(SpeakingAttempt.session_id == row.id))
    if count >= 10:
        raise HTTPException(409, 'Start a new practice session after ten attempts.')
    words = [word.model_dump() for word in body.words]
    activity = row.activity or {}
    segment = None
    if body.question_index is not None:
        segments = activity.get('sample_segments', [])
        if activity.get('part') != 1 or body.question_index >= len(segments):
            raise HTTPException(422, 'Individual questions are available only in Part 1')
        segment = segments[body.question_index]
    duration = (row.activity or {}).get('speaking_seconds', 180)
    if segment:
        duration = 60
    if words[-1]['end'] > (duration + 5) * 1000:
        raise HTTPException(422, 'Recording exceeds the time limit for this part')
    metrics = analyse_timing(words)
    metrics['practice_mode'] = body.practice_mode
    metrics['question_index'] = body.question_index
    if segment:
        metrics['question_label'] = segment['label']
    if body.practice_mode == 'model':
        reference = segment['text'] if segment else activity.get('reference_answer')
        if not reference:
            raise HTTPException(422, 'This session does not have a reference answer')
        import re
        from difflib import SequenceMatcher
        spoken = re.findall(r"[a-z]+(?:'[a-z]+)?", ' '.join(w['text'] for w in words).lower())
        expected = re.findall(r"[a-z]+(?:'[a-z]+)?", reference.lower())
        metrics['reference_similarity_percent'] = round(100 * SequenceMatcher(None, expected, spoken, autojunk=False).ratio())
        metrics['similarity_basis'] = 'word_sequence_not_pronunciation_or_proficiency'
    attempt = SpeakingAttempt(id=str(body.id), owner_id=user.id, session_id=row.id, words=words,
        transcript=' '.join(w['text'] for w in words), metrics=metrics,
        response_language=body.response_language)
    db.add(attempt); db.commit(); db.refresh(attempt)
    return attempt


@router.post('/sessions/{session_id}/attempts/{attempt_id}/retry', status_code=202)
def retry(session_id: UUID, attempt_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    row = owned(db, session_id, user)
    attempt = db.scalar(select(SpeakingAttempt).where(SpeakingAttempt.id == str(attempt_id),
        SpeakingAttempt.session_id == row.id, SpeakingAttempt.owner_id == user.id))
    if not attempt:
        raise HTTPException(404, 'Attempt not found')
    if attempt.status == 'failed':
        attempt.status = 'queued'; db.commit()
    return {'status':attempt.status}


@router.delete('/sessions/{session_id}', status_code=204)
def delete_session(session_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    db.delete(owned(db, session_id, user)); db.commit()
