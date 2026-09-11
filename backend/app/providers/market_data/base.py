"""Abstract base class for market data providers."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Sequence

from app.schemas.market_data import (
    EarningsEvent,
    Fundamentals,
    OHLCVFrame,
    ProviderHealth,
    Quote,
)


class Interval:
    """Supported intervals."""

    DAY = "1d"
    HOUR = "1h"
    MINUTE_15 = "15m"
    MINUTE_5 = "5m"
    MINUTE_1 = "1m"


class MarketDataProvider(ABC):
    """Abstract base class for market data providers.

    All implementations MUST:
    1. Normalise at the boundary (vendor quirks die inside the adapter)
    2. Validate returned data (bad data raises, not returned)
    3. Handle rate limits and retries internally
    4. Return split- and dividend-adjusted bars consistently
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g. 'yahoo', 'alpaca', 'polygon')."""
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote:
        """Get current quote for a symbol.

        Args:
            symbol: e.g. 'NVDA'

        Returns:
            Quote with current price and change

        Raises:
            SymbolNotFoundError: Symbol not found
            ProviderError: API error or rate limit
        """
        pass

    @abstractmethod
    async def get_history(
        self,
        symbol: str,
        *,
        start: date,
        end: date,
        interval: str = Interval.DAY,
    ) -> OHLCVFrame:
        """Get historical OHLCV data for a symbol.

        Args:
            symbol: e.g. 'NVDA'
            start: Start date (inclusive)
            end: End date (inclusive)
            interval: Bar interval (default: '1d')

        Returns:
            OHLCVFrame with bars in ascending date order, no duplicates or gaps except weekends/holidays

        Raises:
            SymbolNotFoundError: Symbol not found
            InsufficientHistoryError: Not enough bars available
            DataQualityError: Bad bars (NaN, inverted high/low, etc.)
            ProviderError: API error or rate limit
        """
        pass

    @abstractmethod
    async def get_history_batch(
        self,
        symbols: Sequence[str],
        *,
        start: date,
        end: date,
        interval: str = Interval.DAY,
    ) -> dict[str, OHLCVFrame]:
        """Get historical data for multiple symbols efficiently.

        IMPORTANT: Implement with bounded concurrency (e.g. Semaphore(10))
        to respect provider rate limits and avoid overwhelming the network.

        Args:
            symbols: List of symbols
            start: Start date
            end: End date
            interval: Bar interval

        Returns:
            Dict of {symbol: OHLCVFrame}. Missing symbols are absent from dict.

        Raises:
            ProviderError: Fatal error (credentials, network, etc.)
        """
        pass

    @abstractmethod
    async def get_fundamentals(self, symbol: str) -> Fundamentals:
        """Get fundamental data for a symbol.

        Args:
            symbol: e.g. 'NVDA'

        Returns:
            Fundamentals (some fields may be None if not available)

        Raises:
            SymbolNotFoundError: Symbol not found
            ProviderError: API error
        """
        pass

    @abstractmethod
    async def get_earnings_calendar(
        self,
        symbols: Sequence[str],
        *,
        through: date,
    ) -> list[EarningsEvent]:
        """Get earnings dates for symbols.

        Args:
            symbols: List of symbols
            through: Include dates through this date

        Returns:
            List of EarningsEvent (may be empty)
        """
        pass

    @abstractmethod
    async def health(self) -> ProviderHealth:
        """Check provider health.

        Returns:
            ProviderHealth status
        """
        pass


# Exceptions
class ProviderError(Exception):
    """Base exception for provider errors."""

    pass


class SymbolNotFoundError(ProviderError):
    """Symbol not found."""

    pass


class InsufficientHistoryError(ProviderError):
    """Not enough historical data."""

    pass


class DataQualityError(ProviderError):
    """Data quality validation failed."""

    pass


class RateLimitError(ProviderError):
    """Rate limit hit."""

    pass
