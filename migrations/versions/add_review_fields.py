"""Add review fields to models

Revision ID: add_review_fields
Revises: c10d2c06536c
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_review_fields_fixed'
down_revision = 'c10d2c06536c'
branch_labels = None
depends_on = None

def upgrade():
    # LearningLogテーブルに新しいフィールドを追加
    op.add_column('learning_log', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('learning_log', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('learning_log', sa.Column('review_count', sa.Integer(), nullable=True))
    op.add_column('learning_log', sa.Column('is_review', sa.Boolean(), nullable=True))
    
    # Questionテーブルに新しいフィールドを追加
    op.add_column('question', sa.Column('option_a', sa.String(length=255), nullable=True))
    op.add_column('question', sa.Column('option_b', sa.String(length=255), nullable=True))
    op.add_column('question', sa.Column('option_c', sa.String(length=255), nullable=True))
    op.add_column('question', sa.Column('option_d', sa.String(length=255), nullable=True))
    op.add_column('question', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('question', sa.Column('difficulty_level', sa.Integer(), nullable=True))
    
    # デフォルト値を設定
    op.execute("UPDATE learning_log SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    op.execute("UPDATE learning_log SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
    op.execute("UPDATE learning_log SET review_count = 0 WHERE review_count IS NULL")
    op.execute("UPDATE learning_log SET is_review = 0 WHERE is_review IS NULL")
    op.execute("UPDATE question SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    op.execute("UPDATE question SET difficulty_level = 1 WHERE difficulty_level IS NULL")

def downgrade():
    # LearningLogテーブルからフィールドを削除
    op.drop_column('learning_log', 'is_review')
    op.drop_column('learning_log', 'review_count')
    op.drop_column('learning_log', 'updated_at')
    op.drop_column('learning_log', 'created_at')
    
    # Questionテーブルからフィールドを削除
    op.drop_column('question', 'difficulty_level')
    op.drop_column('question', 'created_at')
    op.drop_column('question', 'option_d')
    op.drop_column('question', 'option_c')
    op.drop_column('question', 'option_b')
    op.drop_column('question', 'option_a')
