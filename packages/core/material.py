import re
import unicodedata
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Card(Strict):
    front: str = Field(min_length=1, max_length=300)
    back: str = Field(min_length=1, max_length=500)
    quote: str = Field(min_length=1, max_length=500)


class Question(Strict):
    question: str = Field(min_length=1, max_length=500)
    options: list[str] = Field(min_length=4, max_length=4)
    correct: StrictInt = Field(ge=0, le=3)
    explanation: str = Field(min_length=1, max_length=600)
    quote: str = Field(min_length=1, max_length=500)

    @model_validator(mode='after')
    def distinct_options(self):
        if any(not x.strip() or len(x) > 300 for x in self.options) or len({x.strip().casefold() for x in self.options}) != 4:
            raise ValueError('Four distinct nonempty options required')
        return self


class Bundle(Strict):
    summary: str = Field(min_length=1, max_length=2000)
    notes: list[str] = Field(min_length=1, max_length=8)
    cards: list[Card] = Field(min_length=5, max_length=5)
    quiz: list[Question] = Field(min_length=5, max_length=5)

    @model_validator(mode='after')
    def distinct_questions(self):
        if len({q.question.casefold() for q in self.quiz}) != 5 or len({c.front.casefold() for c in self.cards}) != 5:
            raise ValueError('Questions and card fronts must be distinct')
        return self

    def check_source(self, source):
        normalize = lambda value: re.sub(r'\s+', ' ', unicodedata.normalize('NFC', value)).strip()
        source = normalize(source)
        for item in [*self.cards, *self.quiz]:
            if normalize(item.quote) not in source:
                raise ValueError('Quote not found in source')
        if any(not line.strip() or len(line) > 1000 for line in self.notes):
            raise ValueError('Invalid note')
        return self
