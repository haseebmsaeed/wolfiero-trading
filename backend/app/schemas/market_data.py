"""Pydantic schemas for market data (vendor-agnostic)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class Quote(BaseModel):
    """Current quote for a symbol."""

    symbol: str
    price: Decimal
    change: Decimal
    change_pct: Decimal
    open: Decimal
    high: Decimal
    low: Decimal
    volume: int
    as_of: datetime
    is_realtime: bool = False

    class Config:
        """Allow decimal representation."""

        json_encoders = {Decimal: float}


class OHLCVBar(BaseModel):
    """A single OHLCV bar."""

    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    adjusted: bool = True

    class Config:
        json_encoders = {Decimal: float}


class OHLCVFrame(BaseModel):
    """A series of OHLCV bars."""

    symbol: str
    bars: list[OHLCVBar]
    interval: str = "1d"  # 1d, 1h, 15m, etc.

    class Config:
        json_encoders = {Decimal: float}


class Fundamentals(BaseModel):
    """Stock fundamentals."""

    symbol: str
    market_cap: Optional[Decimal] = None
    shares_outstanding: Optional[int] = None
    pe_ratio: Optional[Decimal] = None
    dividend_yield: Optional[Decimal] = None
    eps: Optional[Decimal] = None

    class Config:
        json_encoders = {Decimal: float}


class EarningsEvent(BaseModel):
    """An earnings date."""

    symbol: str
    earnings_date: date
    time_of_day: str = "UNKNOWN"  # BMO, AMC, UNKNOWN
    is_confirmed: bool = False
    fiscal_period: Optional[str] = None
    eps_estimate: Optional[Decimal] = None
    eps_actual: Optional[Decimal] = None
    surprise_pct: Optional[Decimal] = None

    class Config:
        json_encoders = {Decimal: float}


class ProviderHealth(BaseModel):
    """Health status of a provider."""

    provider_name: str
    is_healthy: bool
    error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    request_count: int = 0
    error_count: int = 0
    rate_limit_remaining: Optional[int] = None
