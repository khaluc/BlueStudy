"""Full structured exams and per-skill assessment."""
from alembic import op
import sqlalchemy as sa
revision='0008'
down_revision='0007'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('exams',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('owner_id',sa.String(36),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('document_id',sa.String(36),sa.ForeignKey('documents.id',ondelete='CASCADE'),nullable=False),
        sa.Column('title',sa.String(160),nullable=False),sa.Column('status',sa.String(30),nullable=False),
        sa.Column('structure',sa.JSON(),nullable=True),sa.Column('analysis',sa.JSON(),nullable=False),
        sa.Column('error_code',sa.String(80),nullable=True),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('exam_attempts',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('owner_id',sa.String(36),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('exam_id',sa.String(36),sa.ForeignKey('exams.id',ondelete='CASCADE'),nullable=False),
        sa.Column('answers',sa.JSON(),nullable=False),sa.Column('result',sa.JSON(),nullable=False),
        sa.Column('status',sa.String(30),nullable=False),sa.Column('coaching',sa.JSON(),nullable=True),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    for table,fields in [('exams',['owner_id','document_id','status']),('exam_attempts',['owner_id','exam_id','status'])]:
        for field in fields:op.create_index('ix_'+table+'_'+field,table,[field])


def downgrade():
    op.drop_table('exam_attempts');op.drop_table('exams')
