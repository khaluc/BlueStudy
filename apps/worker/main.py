import logging
import signal
import threading
import httpx
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from apps.api.config import Settings
from apps.chat.agents.orchestrator import Orchestrator
from apps.chat.tools.model_tool import ModelTool
from apps.chat.tools.memory_tool import recent_mistakes
from packages.core.contracts import AgentContext
from packages.db.base import utcnow
from packages.db.database import build_database
from packages.db.models import Document, Job, StudySession, User, Material
from packages.storage.local import LocalStorage
from apps.worker.tasks.ocr_task import process_upload
from apps.worker.tasks.chat_task import process_chat
from apps.worker.tasks.exam_task import process_exam,process_exam_feedback

logger = logging.getLogger('padayon.worker')


def process_one(sessions, orchestrator):
    # Hold the row lock through inference. A killed worker rolls back, leaving
    # the job queued. Multiple PostgreSQL workers skip locked jobs.
    with sessions.begin() as db:
        job = db.scalar(select(Job).where(Job.status == 'queued').order_by(Job.created_at, Job.id)
                        .with_for_update(skip_locked=True).limit(1))
        if job is None:
            return False
        session = db.get(StudySession, job.session_id)
        document = db.get(Document, session.document_id) if session else None
        user = db.get(User, job.owner_id)
        if not session or not document or not user or session.owner_id != job.owner_id or document.owner_id != job.owner_id:
            job.status, job.error_code = 'failed', 'invalid_ownership'
        else:
            try:
                context = AgentContext(document_id=document.id, text=session.source_text,
                                       question=job.question, language_level=user.language_level,
                                       learning_preference=user.learning_preference,
                                       recent_mistakes=recent_mistakes(db, user.id))
                result = orchestrator.run(job.kind, context)
                job.result = result.model_dump()
                if job.kind == 'generate_bundle':
                    material = Material(owner_id=user.id, session_id=session.id, content=result.content,
                                        provenance=result.model_dump(exclude={'content'}))
                    db.add(material)
                    db.flush()
                    # Never expose private quiz answers through the job endpoint.
                    job.result = {'material_id': material.id, **material.provenance}
                job.status = 'succeeded'
            except httpx.TimeoutException:
                job.status, job.error_code = 'failed', 'model_timeout'
            except httpx.HTTPError:
                job.status, job.error_code = 'failed', 'model_unavailable'
            except (ValueError, KeyError, TypeError):
                job.status, job.error_code = 'failed', 'invalid_model_output'
        job.finished_at = utcnow()
    return True


def main():
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    engine, sessions = build_database(settings.database_url)
    if engine.dialect.name != 'postgresql':
        raise SystemExit('Worker triển khai yêu cầu PostgreSQL; SQLite chỉ dùng test một worker.')
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    orchestrator = Orchestrator(ModelTool(settings.chat_base_url))
    storage = LocalStorage(settings.storage_root)
    try:
        while not stop.is_set():
            try:
                uploaded = process_upload(sessions, storage)
                studied = process_one(sessions, orchestrator)
                chatted = process_chat(sessions, orchestrator.model, storage)
                examined = process_exam(sessions, orchestrator.model)
                coached = process_exam_feedback(sessions, orchestrator.model)
                if uploaded or studied or chatted or examined or coached:
                    continue
            except SQLAlchemyError:
                logger.error('Database error; transaction rolled back. Retrying after poll interval.')
            stop.wait(settings.worker_poll_seconds)
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
