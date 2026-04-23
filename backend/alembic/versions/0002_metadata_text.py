"""widen metadata_uri to TEXT

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("tokens", "metadata_uri", type_=sa.Text(), existing_type=sa.String(512))


def downgrade() -> None:
    op.alter_column("tokens", "metadata_uri", type_=sa.String(512), existing_type=sa.Text())
