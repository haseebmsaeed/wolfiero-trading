"""Stock and market data document shapes for Firestore."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class Stock(BaseModel):
    """Firestore document: stocks/{symbol}. One per tradeable instrument."""

    symbol: str
    name: str | None = None
    exchange: str | None = None
    asset_type: str | None = None
    sector: str | None = None
    industry: str | None = None
    market_cap: Decimal | None = None
    shares_outstanding: int | None = None
    is_active: bool = True
    in_universe: bool = False
    is_blocklisted: bool = False
    first_trade_date: date | None = None
    fundamentals: dict[str, Any] | None = None
    fundamentals_updated_at: datetime | None = None


class PriceHistory(BaseModel):
    """Firestore subcollection: stocks/{symbol}/price_history/{trade_date}. Adjusted daily OHLCV."""

    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    adjusted: bool = True
    source: str | None = None
    ingested_at: datetime


class StrategyVersion(BaseModel):
    """Firestore document: strategy_versions/{version}. Published parameter set (append-only)."""

    version: str
    weights: dict[str, Any]
    thresholds: dict[str, Any]
    notes: str | None = None
    activated_at: datetime
    deactivated_at: datetime | None = None
