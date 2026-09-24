"""Explicit learner preference and learner-confirmed topic selection."""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('learning_preference', sa.String(20), server_default='notes', nullable=False))
    op.add_column('study_sessions', sa.Column('topic_id', sa.String(30), nullable=True))


def downgrade():
    with op.batch_alter_table('study_sessions') as batch:
        batch.drop_column('topic_id')
    with op.batch_alter_table('users') as batch:
        batch.drop_column('learning_preference')
