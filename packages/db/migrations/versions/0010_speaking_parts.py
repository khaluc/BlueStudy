"""Structured three-part speaking practice; existing sessions remain unchanged."""
from alembic import op
import sqlalchemy as sa
revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('speaking_sessions', sa.Column('activity', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('speaking_sessions', 'activity')
