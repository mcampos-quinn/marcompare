"""empty message

Revision ID: 1c07823ddf30
Revises: a01810528faf
Create Date: 2021-03-25 18:49:24.426278

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c07823ddf30'
down_revision = 'a01810528faf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=60), nullable=True),
    sa.Column('username', sa.String(length=60), nullable=True),
    sa.Column('affiliation', sa.String(length=100), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('started_timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('batches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('source', sa.String(length=200), nullable=True),
    sa.Column('filepath', sa.String(length=200), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.Column('oclc_number', sa.String(length=200), nullable=True),
    sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('fields',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('record_id', sa.Integer(), nullable=False),
    sa.Column('tag', sa.String(length=100), nullable=True),
    sa.Column('indicator_1', sa.String(length=10), nullable=True),
    sa.Column('indicator_2', sa.String(length=10), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['record_id'], ['records.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('fields')
    op.drop_table('records')
    op.drop_table('batches')
    op.drop_table('sessions')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
