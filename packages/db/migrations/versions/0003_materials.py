"""Study bundles and persistent deterministic quiz assessment."""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('jobs') as batch:
        batch.drop_constraint('job_kind', type_='check')
        batch.create_check_constraint('job_kind', "kind IN ('classify', 'teach', 'generate_bundle')")
    op.create_table('materials',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('study_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('provenance', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_materials_owner_id', 'materials', ['owner_id'])
    op.create_index('ix_materials_session_id', 'materials', ['session_id'])
    op.create_table('quiz_attempts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_id', sa.String(36), sa.ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('answers', sa.JSON(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_quiz_attempts_owner_id', 'quiz_attempts', ['owner_id'])
    op.create_index('ix_quiz_attempts_material_id', 'quiz_attempts', ['material_id'])


def downgrade():
    op.drop_table('quiz_attempts')
    op.drop_table('materials')
    op.execute("DELETE FROM jobs WHERE kind = 'generate_bundle'")
    with op.batch_alter_table('jobs') as batch:
        batch.drop_constraint('job_kind', type_='check')
        batch.create_check_constraint('job_kind', "kind IN ('classify', 'teach')")
