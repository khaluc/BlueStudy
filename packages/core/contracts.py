from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class AgentContext(BaseModel):
    model_config = ConfigDict(extra='forbid')
    document_id: str
    text: str = Field(min_length=1, max_length=2400)
    question: str = Field(default='', max_length=500)
    language_level: Literal['support', 'basic', 'confident']
    learning_preference: Literal['notes', 'flashcards', 'quiz'] = 'notes'
    recent_mistakes: list[str] = Field(default_factory=list, max_length=3)


class Classification(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: Literal['notes', 'exercise', 'summary', 'unknown']


class AgentResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['classify', 'teach', 'generate_bundle']
    source_document_id: str
    content: dict
    model: str
    provider: str | None = None
    fallback_reason: str | None = None
    review_status: Literal['unreviewed'] = 'unreviewed'
