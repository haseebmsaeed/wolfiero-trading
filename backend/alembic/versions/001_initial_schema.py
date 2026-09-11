"""Initial schema with stocks, price_history, and strategy_versions.

Revision ID: 001
Revises:
Create Date: 2026-09-10 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    # stocks table
    op.create_table(
        "stocks",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("exchange", sa.String(length=16), nullable=True),
        sa.Column("asset_type", sa.String(length=32), nullable=True),
        sa.Column("sector", sa.String(length=64), nullable=True),
        sa.Column("industry", sa.String(length=64), nullable=True),
        sa.Column("market_cap", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("shares_outstanding", sa.BigInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("in_universe", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_blocklisted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("first_trade_date", sa.Date(), nullable=True),
        sa.Column("fundamentals", sa.JSON(), nullable=True),
        sa.Column("fundamentals_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index("idx_stocks_active_universe", "stocks", ["is_active", "in_universe"])
    op.create_index("idx_stocks_sector", "stocks", ["sector"])
    op.create_index("ix_stocks_symbol", "stocks", ["symbol"])
    op.create_index("ix_stocks_is_active", "stocks", ["is_active"])
    op.create_index("ix_stocks_in_universe", "stocks", ["in_universe"])

    # price_history table
    op.create_table(
        "price_history",
        sa.Column("stock_id", sa.BigInteger(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("high", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("low", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("close", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("adjusted", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("stock_id", "trade_date"),
    )
    op.create_index("idx_price_history_trade_date", "price_history", ["trade_date"])
    op.create_unique_constraint(
        "uq_price_history_stock_date", "price_history", ["stock_id", "trade_date"]
    )

    # strategy_versions table
    op.create_table(
        "strategy_versions",
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("thresholds", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("version"),
    )


def downgrade() -> None:
    """Drop all tables created in upgrade."""
    op.drop_table("strategy_versions")
    op.drop_table("price_history")
    op.drop_table("stocks")
