from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from packages.db.base import Base, new_id, utcnow


class ChatThread(Base):
    __tablename__ = 'chat_threads'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(100), default='Cuộc trò chuyện mới')
    session_id: Mapped[str | None] = mapped_column(ForeignKey('study_sessions.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChatTurn(Base):
    __tablename__ = 'chat_turns'
    __table_args__ = (CheckConstraint("status IN ('queued', 'succeeded', 'failed')", name='chat_turn_status'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    thread_id: Mapped[str] = mapped_column(ForeignKey('chat_threads.id', ondelete='CASCADE'), index=True)
    image_document_id: Mapped[str | None] = mapped_column(ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)
    source_session_id: Mapped[str | None] = mapped_column(ForeignKey('study_sessions.id', ondelete='SET NULL'), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    quiz: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    quiz_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    work_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='queued', index=True)
    provenance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
