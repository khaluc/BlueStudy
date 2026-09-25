"""Evidence-based attempt metrics, also compatible with previously saved results."""
from packages.core.exam import SKILLS


def review_metrics(result):
    rows = result['feedback']
    skills = []
    for skill in dict.fromkeys(row['skill'] for row in rows):
        items = [row for row in rows if row['skill'] == skill]
        answered = [row for row in items if row['selected'] is not None and row['correct'] is not None]
        skills.append({
            'skill': skill, 'label': SKILLS[skill],
            'correct': sum(row['is_correct'] is True for row in answered),
            'answered_graded': len(answered),
            'wrong_questions': [row['number'] for row in answered if not row['is_correct']],
            'unanswered_questions': [row['number'] for row in items if row['selected'] is None],
            'ungraded_questions': [row['number'] for row in items if row['correct'] is None],
        })
    return {
        'answered': sum(row['selected'] is not None for row in rows),
        'unanswered': sum(row['selected'] is None for row in rows),
        'incorrect_answered': sum(row['selected'] is not None and row['is_correct'] is False for row in rows),
        'skills': skills,
    }
