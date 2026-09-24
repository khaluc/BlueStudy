from alembic import context
from apps.api.config import Settings
from packages.db.base import Base
from packages.db.database import build_database
from packages.db import models


def run():
    url = Settings().database_url
    if context.is_offline_mode():
        context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
    else:
        engine, _ = build_database(url)
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=Base.metadata)
            with context.begin_transaction():
                context.run_migrations()
        engine.dispose()


run()
