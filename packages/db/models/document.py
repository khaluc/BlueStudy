from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from packages.db.base import Base, new_id, utcnow


class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(160))
    text: Mapped[str] = mapped_column(Text)
    source_key: Mapped[str] = mapped_column(String(80), unique=True)
    sha256: Mapped[str] = mapped_column(String(64))
    source_name: Mapped[str] = mapped_column(String(200), default='source.txt', server_default='source.txt')
    media_type: Mapped[str] = mapped_column(String(80), default='text/plain', server_default='text/plain')
    source_size: Mapped[int] = mapped_column(Integer, default=0, server_default='0')
    page_count: Mapped[int] = mapped_column(Integer, default=1, server_default='1')
    status: Mapped[str] = mapped_column(String(24), default='confirmed', server_default='confirmed', index=True)
    pages: Mapped[list] = mapped_column(JSON, default=list, server_default='[]')
    extraction_error: Mapped[str | None] = mapped_column(String(40), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default='1')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
