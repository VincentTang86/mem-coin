"""init

Revision ID: 0001
Revises:
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tokens",
        sa.Column("mint", sa.String(64), primary_key=True),
        sa.Column("symbol", sa.String(32)),
        sa.Column("name", sa.String(128)),
        sa.Column("decimals", sa.Integer),
        sa.Column("launched_at", sa.DateTime(timezone=True), index=True),
        sa.Column("creator", sa.String(64)),
        sa.Column("source", sa.String(32), nullable=False, index=True),
        sa.Column("metadata_uri", sa.String(512)),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tokens_launched_at_desc", "tokens", [sa.text("launched_at DESC")])

    op.create_table(
        "pools",
        sa.Column("pool_address", sa.String(64), primary_key=True),
        sa.Column("token_mint", sa.String(64), sa.ForeignKey("tokens.mint", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("dex", sa.String(32), nullable=False, index=True),
        sa.Column("quote_mint", sa.String(64)),
        sa.Column("liquidity_usd", sa.Numeric(24, 6), index=True),
        sa.Column("price_usd", sa.Numeric(32, 12)),
        sa.Column("price_sol", sa.Numeric(32, 12)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("pool_address", sa.String(64), sa.ForeignKey("pools.pool_address", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("price_usd", sa.Numeric(32, 12)),
        sa.Column("liquidity_usd", sa.Numeric(24, 6)),
        sa.Column("volume_5m", sa.Numeric(24, 6)),
    )
    op.create_index("ix_snap_pool_ts", "price_snapshots", ["pool_address", "ts"])

    op.create_table(
        "saved_filters",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.String(64), index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("saved_filters")
    op.drop_table("price_snapshots")
    op.drop_table("pools")
    op.drop_table("tokens")
