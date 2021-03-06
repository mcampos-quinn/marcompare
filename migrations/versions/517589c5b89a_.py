"""empty message

Revision ID: 517589c5b89a
Revises: b5e2c0a04e27
Create Date: 2021-03-29 21:24:17.262933

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '517589c5b89a'
down_revision = 'b5e2c0a04e27'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('records', sa.Column('added_author_field_count', sa.Integer(), nullable=True))
    op.add_column('records', sa.Column('author_field_count', sa.Integer(), nullable=True))
    op.add_column('records', sa.Column('link_field_count', sa.Integer(), nullable=True))
    op.add_column('records', sa.Column('note_field_count', sa.Integer(), nullable=True))
    op.add_column('records', sa.Column('physical_field_count', sa.Integer(), nullable=True))
    op.add_column('records', sa.Column('subject_field_count', sa.Integer(), nullable=True))
    op.add_column('records', sa.Column('title_field_count', sa.Integer(), nullable=True))
    op.add_column('sessions', sa.Column('added_author_batch_comparison_dict', sa.Text(), nullable=True))
    op.add_column('sessions', sa.Column('author_batch_comparison_dict', sa.Text(), nullable=True))
    op.add_column('sessions', sa.Column('note_batch_comparison_dict', sa.Text(), nullable=True))
    op.add_column('sessions', sa.Column('physical_batch_comparison_dict', sa.Text(), nullable=True))
    op.add_column('sessions', sa.Column('subject_batch_comparison_dict', sa.Text(), nullable=True))
    op.add_column('sessions', sa.Column('title_batch_comparison_dict', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sessions', 'title_batch_comparison_dict')
    op.drop_column('sessions', 'subject_batch_comparison_dict')
    op.drop_column('sessions', 'physical_batch_comparison_dict')
    op.drop_column('sessions', 'note_batch_comparison_dict')
    op.drop_column('sessions', 'author_batch_comparison_dict')
    op.drop_column('sessions', 'added_author_batch_comparison_dict')
    op.drop_column('records', 'title_field_count')
    op.drop_column('records', 'subject_field_count')
    op.drop_column('records', 'physical_field_count')
    op.drop_column('records', 'note_field_count')
    op.drop_column('records', 'link_field_count')
    op.drop_column('records', 'author_field_count')
    op.drop_column('records', 'added_author_field_count')
    # ### end Alembic commands ###
