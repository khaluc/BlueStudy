from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from apps.api.dependencies import current_user, get_db
from apps.api.routers.documents import owned_document
from apps.api.schemas.session import SessionCreate, SessionOut, JobCreate, JobOut
from packages.db.models import StudySession, Job

router = APIRouter(tags=['study sessions'])


def owned_session(db, session_id, owner_id):
    session = db.scalar(select(StudySession).where(StudySession.id == str(session_id),
                                                  StudySession.owner_id == owner_id))
    if session is None:
        raise HTTPException(404, 'Không tìm thấy phiên học.')
    return session


@router.post('/sessions', response_model=SessionOut, status_code=201)
def create_session(body: SessionCreate, user=Depends(current_user), db=Depends(get_db)):
    document = owned_document(db, body.document_id, user.id, lock=True)
    if document.status != 'confirmed':
        raise HTTPException(409, 'Hãy kiểm tra và xác nhận văn bản trước khi học.')
    end = body.end_offset if body.end_offset is not None else len(document.text)
    if not 0 <= body.start_offset < end <= len(document.text):
        raise HTTPException(422, 'Khoảng văn bản không hợp lệ.')
    source_text = document.text[body.start_offset:end]
    if not source_text.strip() or len(source_text) > 2400:
        raise HTTPException(422, 'Chọn đoạn học không rỗng, tối đa 2400 ký tự bằng start_offset/end_offset.')
    session = StudySession(owner_id=user.id, document_id=document.id,
                           source_text=source_text, document_revision=document.revision)
    db.add(session)
    db.commit()
    return session


@router.get('/sessions/{session_id}', response_model=SessionOut)
def get_session(session_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    return owned_session(db, session_id, user.id)


@router.post('/sessions/{session_id}/jobs', response_model=JobOut, status_code=202)
def enqueue(session_id: UUID, body: JobCreate, user=Depends(current_user), db=Depends(get_db)):
    session = owned_session(db, session_id, user.id)
    owned_document(db, session.document_id, user.id, lock=True)
    job = Job(owner_id=user.id, session_id=session.id, kind=body.kind, question=body.question)
    db.add(job)
    db.commit()
    return job


@router.get('/sessions/{session_id}/jobs', response_model=list[JobOut])
def list_jobs(session_id: UUID, limit: int = Query(20, ge=1, le=100),
              user=Depends(current_user), db=Depends(get_db)):
    owned_session(db, session_id, user.id)
    return db.scalars(select(Job).where(Job.session_id == str(session_id), Job.owner_id == user.id)
                      .order_by(Job.created_at.desc(), Job.id).limit(limit)).all()


@router.get('/jobs/{job_id}', response_model=JobOut)
def get_job(job_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == str(job_id), Job.owner_id == user.id))
    if job is None:
        raise HTTPException(404, 'Không tìm thấy tác vụ.')
    return job
