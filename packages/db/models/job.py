from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from packages.db.base import Base, new_id, utcnow


class Job(Base):
    __tablename__ = 'jobs'
    __table_args__ = (
        CheckConstraint("status IN ('queued', 'succeeded', 'failed')", name='job_status'),
        CheckConstraint("kind IN ('classify', 'teach', 'generate_bundle')", name='job_kind'),
        Index('ix_jobs_queue', 'status', 'created_at'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey('study_sessions.id', ondelete='CASCADE'), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    question: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(20), default='queued')
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
