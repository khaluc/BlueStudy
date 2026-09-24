"""Verify two consumers in an isolated, temporary PostgreSQL schema."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.schema import CreateSchema, DropSchema
from sqlalchemy.orm import sessionmaker
from apps.api.config import Settings
from apps.api.services.auth import provision_user
from apps.chat.agents.orchestrator import Orchestrator
from apps.worker.main import process_one
from packages.db.base import Base
from packages.db.database import build_database
from packages.db.models import Document, StudySession, Job


def main():
    engine, _ = build_database(Settings().database_url)
    if engine.dialect.name != 'postgresql':
        raise SystemExit('This check requires PostgreSQL.')
    schema = 'queue_check_' + uuid4().hex
    with engine.begin() as db:
        db.execute(CreateSchema(schema))
    isolated = engine.execution_options(schema_translate_map={None: schema})
    sessions = sessionmaker(isolated, expire_on_commit=False)
    try:
        Base.metadata.create_all(isolated)
        with sessions.begin() as db:
            user, _ = provision_user(db, 'Queue check')
            document = Document(owner_id=user.id, title='Test', text='Test source',
                                source_key=str(uuid4()) + '.txt', sha256='0' * 64)
            db.add(document)
            db.flush()
            session = StudySession(owner_id=user.id, document_id=document.id, source_text=document.text)
            db.add(session)
            db.flush()
            db.add_all([Job(owner_id=user.id, session_id=session.id, kind='classify'),
                        Job(owner_id=user.id, session_id=session.id, kind='classify')])
        entered, release = Event(), Event()
        class BlockingModel:
            def ask(self, prompt):
                entered.set()
                if not release.wait(15):
                    raise RuntimeError('First worker timed out')
                return '{"category":"notes"}', 'queue-test'
        class QuickModel:
            def ask(self, prompt):
                return '{"category":"summary"}', 'queue-test'
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(process_one, sessions, Orchestrator(BlockingModel()))
            try:
                assert entered.wait(5), 'First worker never claimed a job'
                second = pool.submit(process_one, sessions, Orchestrator(QuickModel()))
                assert second.result(timeout=5), 'Second worker could not skip the locked job'
            finally:
                release.set()
            assert first.result(timeout=5)
        with sessions() as db:
            jobs = db.scalars(select(Job)).all()
            assert len(jobs) == 2 and all(job.status == 'succeeded' for job in jobs)
            assert {job.result['content']['category'] for job in jobs} == {'notes', 'summary'}
        print('PASS: two PostgreSQL consumers processed distinct jobs; locked row was skipped.')
    finally:
        with engine.begin() as db:
            db.execute(DropSchema(schema, cascade=True))
        engine.dispose()


if __name__ == '__main__':
    main()
