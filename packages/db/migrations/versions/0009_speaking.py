"""Speaking sessions and timestamped practice attempts."""
from alembic import op
import sqlalchemy as sa

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('speaking_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson', sa.String(40), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('model', sa.String(120), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('speaking_attempts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('speaking_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('words', sa.JSON(), nullable=False), sa.Column('transcript', sa.Text(), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False), sa.Column('response_language', sa.String(2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False), sa.Column('coaching', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    for table, fields in [('speaking_sessions', ['owner_id', 'status']),
                          ('speaking_attempts', ['owner_id', 'session_id', 'status'])]:
        for field in fields:
            op.create_index('ix_' + table + '_' + field, table, [field])


def downgrade():
    op.drop_table('speaking_attempts')
    op.drop_table('speaking_sessions')
