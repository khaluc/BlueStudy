"""Source metadata, extraction review and immutable study text."""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    for column in [
        sa.Column('source_name', sa.String(200), nullable=False, server_default='source.txt'),
        sa.Column('media_type', sa.String(80), nullable=False, server_default='text/plain'),
        sa.Column('source_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('page_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(24), nullable=False, server_default='confirmed'),
        sa.Column('pages', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('extraction_error', sa.String(40), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
    ]:
        op.add_column('documents', column)
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.add_column('study_sessions', sa.Column('source_text', sa.Text(), nullable=False, server_default=''))
    op.add_column('study_sessions', sa.Column('document_revision', sa.Integer(), nullable=False, server_default='1'))
    op.execute("UPDATE study_sessions SET source_text = (SELECT text FROM documents WHERE documents.id = study_sessions.document_id)")
    # Preserve old documents and their sessions; migration is non-destructive.


def downgrade():
    op.drop_column('study_sessions', 'document_revision')
    op.drop_column('study_sessions', 'source_text')
    op.drop_index('ix_documents_status', 'documents')
    for name in ['revision', 'extraction_error', 'pages', 'status', 'page_count',
                 'source_size', 'media_type', 'source_name']:
        op.drop_column('documents', name)
