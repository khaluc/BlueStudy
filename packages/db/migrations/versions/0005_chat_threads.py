"""Independent multi-turn chat, optionally grounded in a confirmed study excerpt."""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('chat_threads',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('owner_id',sa.String(36),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('title',sa.String(100),nullable=False),
        sa.Column('session_id',sa.String(36),sa.ForeignKey('study_sessions.id',ondelete='SET NULL'),nullable=True),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_chat_threads_owner_id','chat_threads',['owner_id'])
    op.create_table('chat_turns',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('thread_id',sa.String(36),sa.ForeignKey('chat_threads.id',ondelete='CASCADE'),nullable=False),
        sa.Column('source_session_id',sa.String(36),sa.ForeignKey('study_sessions.id',ondelete='SET NULL'),nullable=True),
        sa.Column('message',sa.Text(),nullable=False),
        sa.Column('answer',sa.Text(),nullable=True),
        sa.Column('status',sa.String(20),nullable=False),
        sa.Column('provenance',sa.JSON(),nullable=True),
        sa.Column('error_code',sa.String(40),nullable=True),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('finished_at',sa.DateTime(timezone=True),nullable=True),
        sa.CheckConstraint("status IN ('queued', 'succeeded', 'failed')",name='chat_turn_status'))
    op.create_index('ix_chat_turns_thread_id','chat_turns',['thread_id'])
    op.create_index('ix_chat_turns_status','chat_turns',['status'])


def downgrade():
    op.drop_table('chat_turns')
    op.drop_table('chat_threads')
