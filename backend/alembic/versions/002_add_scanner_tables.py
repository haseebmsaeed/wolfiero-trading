"""Add scanner tables: universe_membership, scan_runs, candidates.

Revision ID: 002
Revises: 001
Create Date: 2026-09-11 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create scanner tables."""
    # universe_membership table
    op.create_table(
        "universe_membership",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("stock_id", sa.BigInteger(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("refresh_date", sa.Date(), nullable=False),
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
    )
    op.create_index("idx_universe_membership_stock_id", "universe_membership", ["stock_id"])
    op.create_index("idx_universe_membership_symbol", "universe_membership", ["symbol"])
    op.create_index("idx_universe_membership_refresh_date", "universe_membership", ["refresh_date"])
    op.create_index("idx_universe_membership_symbol_date", "universe_membership", ["symbol", "refresh_date"])

    # scan_runs table
    op.create_table(
        "scan_runs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("strategy_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="RUNNING"),
        sa.Column("funnel", sa.JSON(), nullable=False),
        sa.Column("data_coverage_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("stage_timings", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("run_id", name="uq_scan_runs_run_id"),
    )
    op.create_index("idx_scan_runs_run_id", "scan_runs", ["run_id"])
    op.create_index("idx_scan_runs_trade_date", "scan_runs", ["trade_date"])
    op.create_index("idx_scan_runs_trade_date_version", "scan_runs", ["trade_date", "strategy_version"])

    # candidates table
    op.create_table(
        "candidates",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("stock_id", sa.BigInteger(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("score_breakdown", sa.JSON(), nullable=False),
        sa.Column("setup_type", sa.String(length=32), nullable=False),
        sa.Column("setup_quality", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("technical_snapshot", sa.JSON(), nullable=False),
        sa.Column("is_vetoed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("veto_reasons", sa.JSON(), nullable=True),
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
        sa.UniqueConstraint("run_id", "stock_id", name="uq_candidates_run_stock"),
    )
    op.create_index("idx_candidates_run_id", "candidates", ["run_id"])
    op.create_index("idx_candidates_symbol", "candidates", ["symbol"])
    op.create_index("idx_candidates_trade_date", "candidates", ["trade_date"])
    op.create_index("idx_candidates_symbol_date", "candidates", ["symbol", "trade_date"])


def downgrade() -> None:
    """Drop scanner tables."""
    op.drop_index("idx_candidates_symbol_date", table_name="candidates")
    op.drop_index("idx_candidates_trade_date", table_name="candidates")
    op.drop_index("idx_candidates_symbol", table_name="candidates")
    op.drop_index("idx_candidates_run_id", table_name="candidates")
    op.drop_table("candidates")

    op.drop_index("idx_scan_runs_trade_date_version", table_name="scan_runs")
    op.drop_index("idx_scan_runs_trade_date", table_name="scan_runs")
    op.drop_index("idx_scan_runs_run_id", table_name="scan_runs")
    op.drop_table("scan_runs")

    op.drop_index("idx_universe_membership_symbol_date", table_name="universe_membership")
    op.drop_index("idx_universe_membership_refresh_date", table_name="universe_membership")
    op.drop_index("idx_universe_membership_symbol", table_name="universe_membership")
    op.drop_index("idx_universe_membership_stock_id", table_name="universe_membership")
    op.drop_table("universe_membership")
