"""empty message

Revision ID: 6fe5f5354dac
Revises: 517589c5b89a
Create Date: 2021-03-29 22:42:20.909520

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6fe5f5354dac'
down_revision = '517589c5b89a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('batches', sa.Column('records_w_more_fields', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('batches', 'records_w_more_fields')
    # ### end Alembic commands ###
