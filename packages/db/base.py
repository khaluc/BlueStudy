from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def new_id():
    return str(uuid4())


def utcnow():
    return datetime.now(timezone.utc)
