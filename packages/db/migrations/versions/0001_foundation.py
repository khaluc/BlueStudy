"""User, source document, study session and durable job queue."""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('display_name', sa.String(80), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('language_level', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(160), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('source_key', sa.String(80), nullable=False, unique=True),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_documents_owner_id', 'documents', ['owner_id'])
    op.create_table('study_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_study_sessions_owner_id', 'study_sessions', ['owner_id'])
    op.create_index('ix_study_sessions_document_id', 'study_sessions', ['document_id'])
    op.create_table('jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('study_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_code', sa.String(40), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('queued', 'succeeded', 'failed')", name='job_status'),
        sa.CheckConstraint("kind IN ('classify', 'teach')", name='job_kind'))
    op.create_index('ix_jobs_owner_id', 'jobs', ['owner_id'])
    op.create_index('ix_jobs_session_id', 'jobs', ['session_id'])
    op.create_index('ix_jobs_queue', 'jobs', ['status', 'created_at'])


def downgrade():
    op.drop_table('jobs')
    op.drop_table('study_sessions')
    op.drop_table('documents')
    op.drop_table('users')
