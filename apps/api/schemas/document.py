from datetime import datetime
from pydantic import Field
from apps.api.schemas.common import Input, Output


class DocumentCreate(Input):
    title: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=1, max_length=2400)


class DocumentOut(Output):
    id: str
    title: str
    text: str
    sha256: str
    source_name: str
    media_type: str
    source_size: int
    page_count: int
    status: str
    pages: list[dict]
    extraction_error: str | None
    revision: int
    created_at: datetime


class TextReview(Input):
    text: str = Field(min_length=1, max_length=100000)
    expected_revision: int = Field(ge=1)


class RevisionRequest(Input):
    expected_revision: int = Field(ge=1)
