import hashlib
from typing import Literal
from pathlib import PurePosixPath
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from apps.api.dependencies import current_user, get_db
from apps.api.schemas.document import DocumentOut
from packages.db.base import new_id
from packages.db.models import Document
from packages.ocr.validation import MAX_BYTES
from packages.ocr.process import run_parser
from packages.ocr.errors import ExtractionError

router = APIRouter(prefix='/uploads', tags=['uploads'])


@router.post('', response_model=DocumentOut, status_code=202)
def upload(request: Request, file: UploadFile = File(...), title: str = Form(default='', max_length=160),
           purpose: Literal['study', 'chat_image'] = Form(default='study'),
           user=Depends(current_user), db=Depends(get_db)):
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, 'File vượt quá 10 MiB.')
    name = PurePosixPath((file.filename or 'upload').replace('\\', '/')).name
    name = ''.join(c for c in name if c.isprintable())[:200]
    suffix = PurePosixPath(name).suffix.lower()
    if suffix not in {'.png', '.jpg', '.jpeg', '.pdf'}:
        raise HTTPException(415, 'Chỉ nhận JPEG, PNG hoặc PDF.')
    try:
        metadata = run_parser(data, 'inspect')
    except ExtractionError as exc:
        raise HTTPException(422, {'code': exc.code, 'message': exc.detail}) from exc
    expected_suffix = '.jpg' if suffix == '.jpeg' else suffix
    if metadata['extension'] != expected_suffix:
        raise HTTPException(415, 'Định dạng nội dung không khớp đuôi file.')
    if purpose == 'chat_image' and metadata['media_type'] not in ('image/png', 'image/jpeg'):
        raise HTTPException(415, 'Chat ảnh chỉ nhận PNG hoặc JPEG.')
    if file.content_type not in (metadata['media_type'], 'application/octet-stream', None):
        raise HTTPException(415, 'MIME không khớp nội dung file.')
    doc_id = new_id()
    key = doc_id + metadata['extension']
    storage = request.app.state.storage
    storage.put(key, data)
    document = Document(id=doc_id, owner_id=user.id, title=title.strip() or name[:160], text='',
                        source_key=key, sha256=hashlib.sha256(data).hexdigest(),
                        source_name=name, source_size=len(data), media_type=metadata['media_type'],
                        page_count=metadata['page_count'], status='review_required' if purpose == 'chat_image' else 'queued')
    try:
        db.add(document)
        db.commit()
    except Exception:
        db.rollback()
        storage.delete(key)
        raise
    return document
