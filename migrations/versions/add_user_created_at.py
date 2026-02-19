"""Add created_at to user table

Revision ID: add_user_created_at
Revises: add_review_fields_fixed
Create Date: 2025-02-19

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_user_created_at'
down_revision = 'add_review_fields_fixed'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('user', sa.Column('created_at', sa.DateTime(), nullable=True))
    # 既存ユーザーに登録日を設定（SQLite/PostgreSQL両方で動く書き方）
    try:
        op.execute("UPDATE user SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    except Exception:
        pass

def downgrade():
    op.drop_column('user', 'created_at')
