import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from apps.api.config import Settings
from apps.api.main import create_app
from apps.api.services.auth import provision_user
from packages.db.database import build_database


@pytest.fixture
def backend(tmp_path, monkeypatch):
    url = 'sqlite:///' + (tmp_path / 'test.db').as_posix()
    monkeypatch.setenv('DATABASE_URL', url)
    command.upgrade(Config('alembic.ini'), 'head')
    command.upgrade(Config('alembic.ini'), 'head')
    engine, sessions = build_database(url)
    with sessions.begin() as db:
        first, token_a = provision_user(db, 'Learner A')
        second, token_b = provision_user(db, 'Learner B')
        ids = first.id, second.id
    settings = Settings(_env_file=None, database_url=url, storage_root=tmp_path / 'sources')
    with TestClient(create_app(settings)) as client:
        yield client, sessions, {'Authorization': 'Bearer ' + token_a}, {
            'Authorization': 'Bearer ' + token_b}, settings, ids
    engine.dispose()
