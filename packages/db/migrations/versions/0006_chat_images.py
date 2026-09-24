"""Direct image questions in chat."""
from alembic import op
import sqlalchemy as sa

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('chat_turns') as batch:
        batch.add_column(sa.Column('image_document_id', sa.String(36), nullable=True))
        batch.create_foreign_key('fk_chat_image', 'documents', ['image_document_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('chat_turns') as batch:
        batch.drop_constraint('fk_chat_image', type_='foreignkey')
        batch.drop_column('image_document_id')
