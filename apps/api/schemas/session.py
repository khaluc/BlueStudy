from datetime import datetime
from uuid import UUID
from typing import Literal
from pydantic import Field, model_validator
from apps.api.schemas.common import Input, Output


class SessionCreate(Input):
    document_id: UUID
    start_offset: int = Field(default=0, ge=0)
    end_offset: int | None = Field(default=None, ge=1)


class SessionOut(Output):
    id: str
    document_id: str
    source_text: str
    document_revision: int
    topic_id: str | None
    created_at: datetime


class JobCreate(Input):
    kind: Literal['classify', 'teach', 'generate_bundle']
    question: str = Field(default='', max_length=500)

    @model_validator(mode='after')
    def require_question(self):
        if self.kind == 'teach' and not self.question:
            raise ValueError('Tác vụ giảng dạy cần câu hỏi.')
        if self.kind == 'classify' and self.question:
            raise ValueError('Tác vụ phân loại không nhận câu hỏi.')
        return self


class JobOut(Output):
    id: str
    session_id: str
    kind: str
    status: str
    result: dict | None
    error_code: str | None
    created_at: datetime
    finished_at: datetime | None
