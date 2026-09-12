"""Scanner and universe models."""

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from app.db import Base, TimestampMixin


class UniverseMembership(Base, TimestampMixin):
    """Track universe membership changes — when stocks enter/exit and why."""

    __tablename__ = "universe_membership"

    id = Column(BigInteger, primary_key=True)
    stock_id = Column(BigInteger, nullable=False, index=True)
    symbol = Column(String(16), nullable=False, index=True)
    action = Column(String(16), nullable=False)  # ENTERED, EXITED
    reason = Column(Text, nullable=False)
    refresh_date = Column(Date, nullable=False, index=True)

    __table_args__ = (
        Index("idx_universe_membership_symbol_date", "symbol", "refresh_date"),
    )


class ScanRun(Base, TimestampMixin):
    """Scan execution record with funnel metrics."""

    __tablename__ = "scan_runs"

    id = Column(BigInteger, primary_key=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    strategy_version = Column(String(32), nullable=False)
    status = Column(String(32), default="RUNNING")  # RUNNING, COMPLETED, FAILED
    funnel = Column(JSON, nullable=False)  # Per-stage counts and reasons
    data_coverage_pct = Column(Numeric(5, 2))
    stage_timings = Column(JSON)  # Seconds per stage
    error_message = Column(Text)

    __table_args__ = (
        Index("idx_scan_runs_trade_date_version", "trade_date", "strategy_version"),
    )


class Candidate(Base, TimestampMixin):
    """Immutable point-in-time scan result. Never UPDATE."""

    __tablename__ = "candidates"

    id = Column(BigInteger, primary_key=True)
    run_id = Column(String(64), nullable=False, index=True)
    stock_id = Column(BigInteger, nullable=False, index=True)
    symbol = Column(String(16), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    rank = Column(Integer)  # Final rank, 1–N
    score = Column(Numeric(5, 2), nullable=False)
    score_breakdown = Column(JSON, nullable=False)  # Component breakdown
    setup_type = Column(String(32), nullable=False)
    setup_quality = Column(Numeric(3, 2), nullable=False)
    technical_snapshot = Column(JSON, nullable=False)  # Full TechnicalSnapshot
    is_vetoed = Column(Boolean, default=False)
    veto_reasons = Column(JSON)  # List of reasons if vetoed

    __table_args__ = (
        Index("idx_candidates_run_id", "run_id"),
        Index("idx_candidates_symbol_date", "symbol", "trade_date"),
        UniqueConstraint("run_id", "stock_id", name="uq_candidates_run_stock"),
    )
