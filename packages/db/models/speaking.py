from datetime import datetime
from sqlalchemy import String, ForeignKey, JSON, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from packages.db.base import Base, new_id, utcnow


class SpeakingSession(Base):
    __tablename__ = 'speaking_sessions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    lesson: Mapped[str] = mapped_column(String(40))
    question: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(20), default='queued', index=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    activity: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SpeakingAttempt(Base):
    __tablename__ = 'speaking_attempts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey('speaking_sessions.id', ondelete='CASCADE'), index=True)
    words: Mapped[list] = mapped_column(JSON)
    transcript: Mapped[str] = mapped_column(Text)
    metrics: Mapped[dict] = mapped_column(JSON)
    response_language: Mapped[str] = mapped_column(String(2), default='en')
    status: Mapped[str] = mapped_column(String(20), default='queued', index=True)
    coaching: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
