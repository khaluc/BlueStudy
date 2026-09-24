from sqlalchemy import select
from packages.db.models import Document
from packages.ocr.errors import ExtractionError
from packages.ocr.process import run_parser


def process_upload(sessions, storage, parser=run_parser):
    with sessions.begin() as db:
        document = db.scalar(select(Document).where(Document.status == 'queued')
                             .order_by(Document.created_at, Document.id)
                             .with_for_update(skip_locked=True).limit(1))
        if document is None:
            return False
        try:
            result = parser(storage.read(document.source_key), 'extract')
            document.text = result['text']
            document.pages = result['pages']
            document.page_count = result['page_count']
            document.status = 'review_required' if document.text.strip() else 'failed'
            document.extraction_error = None if document.text.strip() else 'empty_text'
            document.revision += 1
        except FileNotFoundError:
            document.status, document.extraction_error = 'failed', 'source_missing'
        except ExtractionError as exc:
            document.status, document.extraction_error = 'failed', exc.code
    return True
