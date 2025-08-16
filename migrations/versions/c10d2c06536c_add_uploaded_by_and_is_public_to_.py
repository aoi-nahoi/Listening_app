"""Add uploaded_by and is_public to Question

Revision ID: c10d2c06536c
Revises: 69fd92cec8e7
Create Date: 2025-01-10 18:13:29.249038

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c10d2c06536c'
down_revision = '69fd92cec8e7'
branch_labels = None
depends_on = None


def upgrade():
    # ### Adjusted commands ###

    # Add new columns to the 'question' table
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uploaded_by', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('is_public', sa.Boolean(), nullable=True))
        batch_op.create_foreign_key('fk_question_user', 'user', ['uploaded_by'], ['id'])

    # ### End of commands ###


def downgrade():
    # ### Adjusted commands ###

    # Remove the added columns and constraints from the 'question' table
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.drop_constraint('fk_question_user', type_='foreignkey')
        batch_op.drop_column('is_public')
        batch_op.drop_column('uploaded_by')

    # ### End of commands ###
