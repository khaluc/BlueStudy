from datetime import datetime
from sqlalchemy import String, ForeignKey, JSON, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from packages.db.base import Base, new_id, utcnow


class Exam(Base):
    __tablename__='exams'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=new_id)
    owner_id:Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True)
    document_id:Mapped[str]=mapped_column(ForeignKey('documents.id',ondelete='CASCADE'),index=True)
    title:Mapped[str]=mapped_column(String(160))
    status:Mapped[str]=mapped_column(String(30),default='queued',index=True)
    structure:Mapped[dict|None]=mapped_column(JSON,nullable=True)
    analysis:Mapped[list]=mapped_column(JSON,default=list)
    error_code:Mapped[str|None]=mapped_column(String(80),nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)


class ExamAttempt(Base):
    __tablename__='exam_attempts'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=new_id)
    owner_id:Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True)
    exam_id:Mapped[str]=mapped_column(ForeignKey('exams.id',ondelete='CASCADE'),index=True)
    answers:Mapped[list]=mapped_column(JSON)
    result:Mapped[dict]=mapped_column(JSON)
    status:Mapped[str]=mapped_column(String(30),default='queued',index=True)
    coaching:Mapped[dict|None]=mapped_column(JSON,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
