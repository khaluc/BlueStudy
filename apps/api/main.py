from contextlib import asynccontextmanager
from pathlib import Path
import json
from fastapi import Request, Response, Depends
from apps.api.dependencies import get_db, check_local_origin
from apps.api.services.auth import authenticate
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from apps.api.config import Settings
from apps.api.routers import documents, sessions, users, uploads
from apps.api.routers import materials
from apps.api.routers import chat
from apps.api.routers import exams
from apps.api.services.body_limit import UploadBodyLimit
from packages.db.database import build_database
from packages.storage.local import LocalStorage


def create_app(settings: Settings | None = None):
    settings = settings or Settings()
    engine, session_factory = build_database(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        app.state.storage = LocalStorage(settings.storage_root)
        app.state.sessions = session_factory
        yield
        engine.dispose()

    app = FastAPI(title='BlueStudy API — Phase 4', lifespan=lifespan)
    app.state.local_access_file = settings.local_access_file

    @app.post('/local-session')
    def local_session(request: Request, response: Response, db=Depends(get_db)):
        if not settings.local_access_file:
            raise HTTPException(404, 'Local access disabled')
        check_local_origin(request)
        try:
            token = json.loads(settings.local_access_file.read_text(encoding='utf-8'))['token']
            user = authenticate(db, token)
        except (OSError, ValueError, KeyError, TypeError):
            user = None
        if user is None:
            raise HTTPException(503, 'Không mở được góc học tập trên máy. Kiểm tra cấu hình tài khoản mặc định.')
        response.headers['Cache-Control'] = 'no-store'
        response.set_cookie('padayon-local', token, httponly=True, samesite='strict',
                            secure=request.url.scheme == 'https', max_age=2592000)
        return {'mode': 'local'}
    app.add_middleware(UploadBodyLimit)
    app.include_router(uploads.router)
    app.include_router(users.router)
    app.include_router(documents.router)
    app.include_router(sessions.router)
    app.include_router(materials.router)
    app.include_router(chat.router)
    app.include_router(exams.router)
    app.mount('/app', StaticFiles(directory=Path(__file__).resolve().parents[1] / 'web', html=True), name='web')

    @app.get('/health/live')
    def live():
        return {'status': 'alive'}

    @app.get('/health/ready')
    def ready():
        try:
            with engine.connect() as connection:
                revision = connection.execute(text('SELECT version_num FROM alembic_version')).scalar()
            if revision != '0008':
                raise HTTPException(503, 'Cần cập nhật schema.')
        except SQLAlchemyError as exc:
            raise HTTPException(503, 'Cơ sở dữ liệu chưa sẵn sàng.') from exc
        return {'status': 'ready', 'schema': revision}

    return app


app = create_app()
