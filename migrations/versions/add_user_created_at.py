"""Add created_at to user table

Revision ID: add_user_created_at
Revises: add_review_fields_fixed
Create Date: 2025-02-19

"""
from alembic import op
from sqlalchemy import text

revision = 'add_user_created_at'
down_revision = 'add_review_fields_fixed'
branch_labels = None
depends_on = None

def upgrade():
    import sqlalchemy as sa
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    # PostgreSQL では "user" が予約語のため引用符で囲む
    if dialect_name == 'postgresql':
        op.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP'))
        op.execute(text('UPDATE "user" SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL'))
    else:
        op.add_column('user', sa.Column('created_at', sa.DateTime(), nullable=True))
        try:
            op.execute(text("UPDATE user SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
        except Exception:
            pass

def downgrade():
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute(text('ALTER TABLE "user" DROP COLUMN IF EXISTS created_at'))
    else:
        import sqlalchemy as sa
        op.drop_column('user', 'created_at')
