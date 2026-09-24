from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from packages.db.base import Base, new_id, utcnow


class StudySession(Base):
    __tablename__ = 'study_sessions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE'), index=True)
    source_text: Mapped[str] = mapped_column(Text, default='', server_default='')
    document_revision: Mapped[int] = mapped_column(Integer, default=1, server_default='1')
    topic_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
