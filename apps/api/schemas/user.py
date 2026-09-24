from typing import Literal
from pydantic import Field
from apps.api.schemas.common import Input, Output


class UserOut(Output):
    id: str
    display_name: str
    language_level: str
    learning_preference: str


class UserUpdate(Input):
    display_name: str = Field(min_length=1, max_length=80)
    language_level: Literal['support', 'basic', 'confident']
    learning_preference: Literal['notes', 'flashcards', 'quiz'] = 'notes'
