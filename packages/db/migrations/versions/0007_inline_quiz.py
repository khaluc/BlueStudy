"""Structured chat quizzes, private answers and durable pipeline context."""
from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    for name in ('quiz', 'quiz_result', 'work_context'):
        op.add_column('chat_turns', sa.Column(name, sa.JSON(), nullable=True))


def downgrade():
    for name in ('work_context', 'quiz_result', 'quiz'):
        op.drop_column('chat_turns', name)
