"""Separate exam administration from learning evidence without altering stored OCR."""
import re
import unicodedata
from dataclasses import dataclass


def folded(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.lower()) if not unicodedata.combining(c)).replace('đ','d')


ADMIN = re.compile(
    r'bo giao duc|so giao duc|de thi chinh thuc|ky thi.{0,70}(trung hoc|tot nghiep)|'
    r'thoi gian lam bai|thoi gian phat de|ho.{0,8}ten thi sinh|so bao danh|ma de|'
    r'^\s*trang\s*\d+\s*[/|]|de thi co\s*\d+\s*trang|mon thi\s*[:：]|'
    r'exam (code|duration|date)|candidate (name|number)|time allowed|^\s*page\s*\d+\s*(of|/)',re.I)
ADMIN_QUESTION = re.compile(
    r'ma de|so bao danh|ten thi sinh|bo giao duc|de thi.{0,45}(nam nao|nam bao nhieu|bao nhieu trang|may trang|bao nhieu phut)|'
    r'thoi gian lam bai|(?:nam|ngay)\s+(?:to chuc\s+)?(?:ky thi|thi\b)|'
    r'(exam|test).{0,35}(year|date|code|duration|pages)|time allowed',re.I)
LANGUAGE_TASK = re.compile(
    r'ngu phap|tu vung|cum tu|cau truc|tu loai|dong tu|danh tu|tinh tu|trang tu|lien tu|gioi tu|'
    r'dien|cho trong|o trong|cho cham|nghia|ket hop|so sanh|thi hien tai|thi qua khu|'
    r'collocation|grammar|vocabulary|meaning|mean\b|blank|complete|word|phrase|verb|noun|adjective|adverb|preposition|tense|'
    r'_{2,}|\(\d+\)',re.I)


@dataclass(frozen=True)
class StudySource:
    text: str
    exam: bool
    cloze: bool

    @property
    def instruction(self):
        general = ('Use learning content only. Never make study questions or summary bullets about exam administration: '
                   'year/date of the exam, issuing authority, exam code, candidate details, page count or time allowed. ')
        if not self.exam:
            return general
        return general + (
            'This is an exam/exercise excerpt, possibly incomplete and not necessarily grade 9. Match the actual source level; '
            'do not relabel it as a grade 9 exam. Teach the tested English vocabulary, collocations, grammar and solving strategies. '
            'For gap-fill exercises, each card/question MUST test a language skill or completing an actual gap, '
            'NOT trivia about campaign names, dates, deadlines or activities in the passage. '
            'For reading-comprehension sections, test comprehension only where the passage supplies enough evidence. '
            'Preserve the passage context, numbered blanks and A-D choices. Include the relevant sentence in the question '
            'so the learner can answer without seeing the original image. '
            'Do not fabricate missing pages, choices, answer keys or unreadable text. Do not claim an official answer key. '
            'If a gap lacks its sentence or choices, use a clear visible vocabulary/grammar example instead. '
            'Language knowledge may explain the examples, but do not add unrelated factual content. '
            'Summary/notes must describe skills and rules to practise, not summarize the exam cover or passage events. '
            'Quote the exact source sentence/phrase supporting each learning item. ')

    def validate_items(self, questions, extra_text=()):
        for value in extra_text:
            if ADMIN_QUESTION.search(folded(value)):
                raise ValueError('Exam administration is not a learning objective')
        for value in questions:
            text = folded(value)
            if ADMIN_QUESTION.search(text):
                raise ValueError('Exam administration question rejected')
            if self.cloze and not LANGUAGE_TASK.search(text):
                raise ValueError('Gap-fill review must test English language skills, not passage trivia')


def prepare_study_source(raw):
    text = folded(raw)
    exam = bool(ADMIN.search(text) or re.search(r'question\s*\d+\s*[.:]|numbered blanks|mark the letter|cau\s*\d+\s*[.:]',text))
    cloze = exam and bool(re.search(r'numbered blanks|best fits|\(\d+\)\s*[_.…]{2,}|dien.{0,20}(trong|cho)',text))
    if not exam:
        return StudySource(raw,False,False)
    # Keep original line contents so verbatim source citation checks still work.
    separated = re.sub(r'(?i)(?=Read the following|Read the passage|Question\s+\d+\s*[.:])', '\n', raw)
    lines = [line for line in separated.splitlines() if not ADMIN.search(folded(line))]
    cleaned = '\n'.join(lines).strip()
    if not cleaned:
        raise ValueError('No learning content after exam header removal')
    return StudySource(cleaned,True,cloze)
