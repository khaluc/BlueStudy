from datetime import datetime
from sqlalchemy import String, ForeignKey, JSON, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from packages.db.base import Base, new_id, utcnow


class Material(Base):
    __tablename__ = 'materials'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey('study_sessions.id', ondelete='CASCADE'), index=True)
    content: Mapped[dict] = mapped_column(JSON)
    provenance: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class QuizAttempt(Base):
    __tablename__ = 'quiz_attempts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    material_id: Mapped[str] = mapped_column(ForeignKey('materials.id', ondelete='CASCADE'), index=True)
    answers: Mapped[list] = mapped_column(JSON)
    score: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
