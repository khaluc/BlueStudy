import hashlib
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from urllib.parse import quote
from apps.api.dependencies import current_user, get_db
from apps.api.schemas.document import DocumentCreate, DocumentOut, TextReview, RevisionRequest
from packages.ocr.extraction import normalize
from packages.db.base import new_id
from packages.db.models import Document

router = APIRouter(prefix='/documents', tags=['documents'])


def owned_document(db, document_id, owner_id, lock=False):
    query = select(Document).where(Document.id == str(document_id), Document.owner_id == owner_id)
    if lock:
        query = query.with_for_update()
    document = db.scalar(query)
    if document is None:
        raise HTTPException(404, 'Không tìm thấy tài liệu.')
    return document


@router.post('', response_model=DocumentOut, status_code=201)
def create(body: DocumentCreate, request: Request, user=Depends(current_user), db=Depends(get_db)):
    document_id = new_id()
    content = body.text.encode('utf-8')
    key = document_id + '.txt'
    storage = request.app.state.storage
    storage.put(key, content)
    document = Document(id=document_id, owner_id=user.id, title=body.title, text=body.text,
                        source_key=key, sha256=hashlib.sha256(content).hexdigest(), source_size=len(content))
    try:
        db.add(document)
        db.commit()
    except Exception:
        db.rollback()
        storage.delete(key)
        raise
    return document


@router.get('', response_model=list[DocumentOut])
def listing(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
            q: str = Query('', max_length=100),
            user=Depends(current_user), db=Depends(get_db)):
    return db.scalars(select(Document).where(Document.owner_id == user.id,
                      Document.title.contains(q, autoescape=True) | Document.text.contains(q, autoescape=True))
                      .order_by(Document.created_at.desc(), Document.id).limit(limit).offset(offset)).all()


@router.get('/{document_id}', response_model=DocumentOut)
def get(document_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    return owned_document(db, document_id, user.id)


@router.get('/{document_id}/source')
def source(document_id: UUID, request: Request, user=Depends(current_user), db=Depends(get_db)):
    document = owned_document(db, document_id, user.id)
    try:
        content = request.app.state.storage.read(document.source_key)
    except FileNotFoundError:
        raise HTTPException(503, 'Nguồn tạm thời không khả dụng.')
    return Response(content, media_type=document.media_type,
                    headers={'Content-Disposition': "attachment; filename*=UTF-8''" + quote(document.source_name, safe=''),
                             'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'private, no-store'})


def require_revision(document, expected):
    if document.revision != expected:
        raise HTTPException(409, 'Văn bản đã thay đổi. Tải lại tài liệu trước khi sửa/xác nhận.')
    if document.status == 'queued':
        raise HTTPException(409, 'Tài liệu đang chờ xử lý.')


@router.patch('/{document_id}/text', response_model=DocumentOut)
def review_text(document_id: UUID, body: TextReview, user=Depends(current_user), db=Depends(get_db)):
    document = owned_document(db, document_id, user.id, lock=True)
    require_revision(document, body.expected_revision)
    text = normalize(body.text)
    if not text:
        raise HTTPException(422, 'Văn bản không được rỗng.')
    document.text = text
    document.revision += 1
    document.status = 'review_required'
    document.extraction_error = None
    db.commit()
    return document


@router.post('/{document_id}/confirm', response_model=DocumentOut)
def confirm(document_id: UUID, body: RevisionRequest, user=Depends(current_user), db=Depends(get_db)):
    document = owned_document(db, document_id, user.id, lock=True)
    require_revision(document, body.expected_revision)
    if document.status not in {'review_required', 'confirmed'} or not document.text.strip():
        raise HTTPException(409, 'Cần văn bản không rỗng đã kiểm tra để xác nhận.')
    document.status = 'confirmed'
    db.commit()
    return document


@router.post('/{document_id}/retry', response_model=DocumentOut, status_code=202)
def retry(document_id: UUID, body: RevisionRequest, user=Depends(current_user), db=Depends(get_db)):
    document = owned_document(db, document_id, user.id, lock=True)
    if document.revision != body.expected_revision or document.status != 'failed' or document.media_type == 'text/plain':
        raise HTTPException(409, 'Chỉ chạy lại tài liệu trích xuất thất bại ở phiên bản hiện tại.')
    document.status, document.extraction_error = 'queued', None
    document.revision += 1
    db.commit()
    return document


@router.delete('/{document_id}', status_code=204)
def delete(document_id: UUID, request: Request, user=Depends(current_user), db=Depends(get_db)):
    document = owned_document(db, document_id, user.id, lock=True)
    # Keep the DB record when physical deletion fails, allowing the caller to retry.
    request.app.state.storage.delete(document.source_key)
    db.delete(document)
    db.commit()
    return Response(status_code=204)
