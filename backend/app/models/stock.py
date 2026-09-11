"""Stock and market data models."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    Enum,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base, TimestampMixin


class Stock(Base, TimestampMixin):
    """The symbol master. One row per tradeable instrument."""

    __tablename__ = "stocks"

    id = Column(BigInteger, primary_key=True)
    symbol = Column(String(16), unique=True, nullable=False, index=True)
    name = Column(Text)
    exchange = Column(String(16))
    asset_type = Column(String(32))  # COMMON_STOCK, ETF, ADR
    sector = Column(String(64), index=True)
    industry = Column(String(64))
    market_cap = Column(Numeric(20, 2))
    shares_outstanding = Column(BigInteger)
    is_active = Column(Boolean, default=True, index=True)
    in_universe = Column(Boolean, default=False, index=True)
    is_blocklisted = Column(Boolean, default=False)
    first_trade_date = Column(Date)
    fundamentals = Column(JSON)  # Vendor-shaped; cached 7 days
    fundamentals_updated_at = Column(DateTime)

    __table_args__ = (
        Index("idx_stocks_active_universe", "is_active", "in_universe"),
        Index("idx_stocks_sector", "sector"),
    )


class PriceHistory(Base):
    """Adjusted daily bars. Split- and dividend-adjusted."""

    __tablename__ = "price_history"

    stock_id = Column(BigInteger, primary_key=True)
    trade_date = Column(Date, primary_key=True)
    open = Column(Numeric(18, 4), nullable=False)
    high = Column(Numeric(18, 4), nullable=False)
    low = Column(Numeric(18, 4), nullable=False)
    close = Column(Numeric(18, 4), nullable=False)
    volume = Column(BigInteger, nullable=False)
    adjusted = Column(Boolean, default=True)
    source = Column(String(32))  # Provider name
    ingested_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_price_history_trade_date", "trade_date"),
        UniqueConstraint("stock_id", "trade_date", name="uq_price_history_stock_date"),
    )


class StrategyVersion(Base):
    """Published parameter sets. Append-only."""

    __tablename__ = "strategy_versions"

    version = Column(String(32), primary_key=True)
    weights = Column(JSON, nullable=False)  # Full scoring weight set
    thresholds = Column(JSON, nullable=False)  # Liquidity floors, R:R minimum, etc.
    notes = Column(Text)  # Why this version differs
    activated_at = Column(DateTime, nullable=False)
    deactivated_at = Column(DateTime)
