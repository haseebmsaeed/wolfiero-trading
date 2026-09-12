"""Stock and market data document shapes for Firestore."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel


class Stock(BaseModel):
    """Firestore document: stocks/{symbol}. One per tradeable instrument."""

    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    asset_type: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[Decimal] = None
    shares_outstanding: Optional[int] = None
    is_active: bool = True
    in_universe: bool = False
    is_blocklisted: bool = False
    first_trade_date: Optional[date] = None
    fundamentals: Optional[dict[str, Any]] = None
    fundamentals_updated_at: Optional[datetime] = None


class PriceHistory(BaseModel):
    """Firestore subcollection: stocks/{symbol}/price_history/{trade_date}. Adjusted daily OHLCV."""

    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    adjusted: bool = True
    source: Optional[str] = None
    ingested_at: datetime


class StrategyVersion(BaseModel):
    """Firestore document: strategy_versions/{version}. Published parameter set (append-only)."""

    version: str
    weights: dict[str, Any]
    thresholds: dict[str, Any]
    notes: Optional[str] = None
    activated_at: datetime
    deactivated_at: Optional[datetime] = None
