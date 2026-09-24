from pathlib import Path
import pytest
from packages.core.exam import parse_exam


def test_vinh_pdf_all_40_questions_and_cross_page_choices():
    text=Path('data/samples/vinh-exam-2026.txt').read_text(encoding='utf-8')
    exam=parse_exam(text,8)
    assert [q['number'] for q in exam['questions']]==list(range(1,41))
    assert len(exam['passages'])==6 and not exam['warnings']
    assert exam['questions'][28]['options']==['Paragraph 2','Paragraph 4','Paragraph 3','Paragraph 1']
    assert exam['questions'][21]['options'][3]=='making city life healthier and more sustainable'
    assert 'e – a' in exam['questions'][13]['options'][3]
    assert 'JOINING THE WORKFORCE' in exam['passages'][-1]['text']
    assert 'career choice' in exam['questions'][37]['stem']


def test_ambiguous_or_missing_options_not_invented():
    with pytest.raises(ValueError):parse_exam('Question 1. A. one B. two C. three')
    with pytest.raises(ValueError):parse_exam('Question 1. A. one B. two C. three D. four\nQuestion 1. A. one B. two C. three D. four')


def test_hanoi_11_pages_complete_and_end_notes_excluded():
    text=Path('data/samples/hanoi-exam-2026.txt').read_text(encoding='utf-8')
    exam=parse_exam(text,11)
    assert [q['number'] for q in exam['questions']]==list(range(1,41))
    assert len(exam['passages'])==6 and not exam['warnings']
    assert exam['questions'][-1]['options'][-1]=='but also some people are beneficial from giving a speech without notes'
    assert 'Giám thị' not in exam['questions'][-1]['source_fragment']
