from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from packages.db.base import Base, new_id, utcnow


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    display_name: Mapped[str] = mapped_column(String(80))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    language_level: Mapped[str] = mapped_column(String(20), default='basic')
    learning_preference: Mapped[str] = mapped_column(String(20), default='notes', server_default='notes')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
