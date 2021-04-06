"""empty message

Revision ID: 221a1deb36b5
Revises: c1197f8a206e
Create Date: 2021-04-06 12:31:05.681287

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '221a1deb36b5'
down_revision = 'c1197f8a206e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sessions', sa.Column('notes2', sa.String(length=200), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sessions', 'notes2')
    # ### end Alembic commands ###
