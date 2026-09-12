"""Pydantic schemas for market data (vendor-agnostic)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


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

        json_encoders = {Decimal: float}  # noqa: RUF012


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
        json_encoders = {Decimal: float}  # noqa: RUF012


class OHLCVFrame(BaseModel):
    """A series of OHLCV bars."""

    symbol: str
    bars: list[OHLCVBar]
    interval: str = "1d"  # 1d, 1h, 15m, etc.

    class Config:
        json_encoders = {Decimal: float}  # noqa: RUF012


class Fundamentals(BaseModel):
    """Stock fundamentals."""

    symbol: str
    market_cap: Decimal | None = None
    shares_outstanding: int | None = None
    pe_ratio: Decimal | None = None
    dividend_yield: Decimal | None = None
    eps: Decimal | None = None

    class Config:
        json_encoders = {Decimal: float}  # noqa: RUF012


class EarningsEvent(BaseModel):
    """An earnings date."""

    symbol: str
    earnings_date: date
    time_of_day: str = "UNKNOWN"  # BMO, AMC, UNKNOWN
    is_confirmed: bool = False
    fiscal_period: str | None = None
    eps_estimate: Decimal | None = None
    eps_actual: Decimal | None = None
    surprise_pct: Decimal | None = None

    class Config:
        json_encoders = {Decimal: float}  # noqa: RUF012


class ProviderHealth(BaseModel):
    """Health status of a provider."""

    provider_name: str
    is_healthy: bool
    error: str | None = None
    last_error_at: datetime | None = None
    request_count: int = 0
    error_count: int = 0
    rate_limit_remaining: int | None = None
