"""Owner-scoped retrieval from saved assessment, never inferred personality."""
from sqlalchemy import select
from packages.db.models import QuizAttempt, Material


def recent_mistakes(db, owner_id):
    rows = db.execute(select(QuizAttempt, Material).join(Material, QuizAttempt.material_id == Material.id)
                      .where(QuizAttempt.owner_id == owner_id, Material.owner_id == owner_id)
                      .order_by(QuizAttempt.created_at.desc()).limit(5)).all()
    mistakes, seen = [], set()
    for attempt, material in rows:
        for index, (answer, question) in enumerate(zip(attempt.answers, material.content['quiz'])):
            if (material.id, index) in seen:
                continue
            seen.add((material.id, index))
            if answer != question['correct'] and question['question'][:140] not in mistakes:
                mistakes.append(question['question'][:140])
            if len(mistakes) == 3:
                return mistakes
    return mistakes
