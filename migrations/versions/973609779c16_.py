"""empty message

Revision ID: 973609779c16
Revises: 221a1deb36b5
Create Date: 2021-04-06 12:36:23.271087

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '973609779c16'
down_revision = '221a1deb36b5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sessions', 'notes2')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sessions', sa.Column('notes2', sa.VARCHAR(length=200), nullable=True))
    # ### end Alembic commands ###
