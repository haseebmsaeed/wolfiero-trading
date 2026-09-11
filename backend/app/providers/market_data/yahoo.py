"""Yahoo Finance market data provider."""

import asyncio
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Sequence

import httpx
import yfinance as yf

from app.logging import get_logger
from app.providers.market_data.base import (
    DataQualityError,
    Interval,
    MarketDataProvider,
    OHLCVFrame,
    OHLCVBar,
    ProviderError,
    ProviderHealth,
    Quote,
    SymbolNotFoundError,
    EarningsEvent,
    Fundamentals,
)

logger = get_logger(__name__)


class YahooProvider(MarketDataProvider):
    """Yahoo Finance provider.

    Uses yfinance library with httpx for async support.
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """Initialize Yahoo provider.

        Args:
            timeout: Request timeout in seconds
            max_retries: Number of retries on failure
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self._error_count = 0
        self._request_count = 0

    @property
    def name(self) -> str:
        """Provider name."""
        return "yahoo"

    async def get_quote(self, symbol: str) -> Quote:
        """Get current quote."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.info

            if "currentPrice" not in data:
                raise SymbolNotFoundError(f"Symbol {symbol} not found or has no price")

            price = Decimal(str(data["currentPrice"]))
            change = Decimal(str(data.get("regularMarketChange", 0)))
            change_pct = Decimal(str(data.get("regularMarketChangePercent", 0)))
            open_price = Decimal(str(data.get("open", price)))
            high = Decimal(str(data.get("dayHigh", price)))
            low = Decimal(str(data.get("dayLow", price)))
            volume = int(data.get("volume", 0))

            self._request_count += 1

            return Quote(
                symbol=symbol,
                price=price,
                change=change,
                change_pct=change_pct,
                open=open_price,
                high=high,
                low=low,
                volume=volume,
                as_of=datetime.utcnow(),
                is_realtime=True,
            )

        except SymbolNotFoundError:
            raise
        except Exception as e:
            self._error_count += 1
            raise ProviderError(f"Failed to get quote for {symbol}: {e}") from e

    async def get_history(
        self,
        symbol: str,
        *,
        start: date,
        end: date,
        interval: str = Interval.DAY,
    ) -> OHLCVFrame:
        """Get historical OHLCV data."""
        try:
            ticker = yf.Ticker(symbol, session=yf.utils.get_clean_session())
            df = ticker.history(start=start, end=end, interval=interval, auto_adjust=True)

            if df.empty:
                raise SymbolNotFoundError(f"No data found for {symbol}")

            # Validate data
            self._validate_ohlcv(df, symbol)

            # Convert to OHLCVBar list
            bars = []
            for trade_date, row in df.iterrows():
                bar = OHLCVBar(
                    trade_date=trade_date.date(),
                    open=Decimal(str(row["Open"])),
                    high=Decimal(str(row["High"])),
                    low=Decimal(str(row["Low"])),
                    close=Decimal(str(row["Close"])),
                    volume=int(row["Volume"]),
                    adjusted=True,
                )
                bars.append(bar)

            self._request_count += 1

            return OHLCVFrame(symbol=symbol, bars=bars, interval=interval)

        except SymbolNotFoundError:
            raise
        except Exception as e:
            self._error_count += 1
            raise ProviderError(f"Failed to get history for {symbol}: {e}") from e

    async def get_history_batch(
        self,
        symbols: Sequence[str],
        *,
        start: date,
        end: date,
        interval: str = Interval.DAY,
    ) -> dict[str, OHLCVFrame]:
        """Get history for multiple symbols with bounded concurrency."""
        # Bounded concurrency to respect rate limits
        semaphore = asyncio.Semaphore(10)

        async def fetch_one(symbol: str) -> tuple[str, OHLCVFrame | None]:
            async with semaphore:
                try:
                    frame = await self.get_history(symbol, start=start, end=end, interval=interval)
                    return symbol, frame
                except Exception as e:
                    logger.warning(f"Failed to fetch {symbol}: {e}")
                    return symbol, None

        # Gather all tasks
        tasks = [fetch_one(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Build result dict
        return {symbol: frame for symbol, frame in results if frame is not None}

    async def get_fundamentals(self, symbol: str) -> Fundamentals:
        """Get fundamentals."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            market_cap = info.get("marketCap")
            shares_outstanding = info.get("sharesOutstanding")
            pe_ratio = info.get("trailingPE")
            dividend_yield = info.get("dividendYield")
            eps = info.get("trailingEps")

            self._request_count += 1

            return Fundamentals(
                symbol=symbol,
                market_cap=Decimal(str(market_cap)) if market_cap else None,
                shares_outstanding=shares_outstanding,
                pe_ratio=Decimal(str(pe_ratio)) if pe_ratio else None,
                dividend_yield=Decimal(str(dividend_yield)) if dividend_yield else None,
                eps=Decimal(str(eps)) if eps else None,
            )

        except Exception as e:
            self._error_count += 1
            raise ProviderError(f"Failed to get fundamentals for {symbol}: {e}") from e

    async def get_earnings_calendar(
        self,
        symbols: Sequence[str],
        *,
        through: date,
    ) -> list[EarningsEvent]:
        """Get earnings dates."""
        events = []

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                earnings_date = info.get("earningsDate")

                if earnings_date:
                    events.append(
                        EarningsEvent(
                            symbol=symbol,
                            earnings_date=earnings_date,
                            time_of_day="UNKNOWN",
                            is_confirmed=False,
                        )
                    )
                self._request_count += 1

            except Exception as e:
                logger.warning(f"Failed to get earnings for {symbol}: {e}")
                self._error_count += 1

        return events

    async def health(self) -> ProviderHealth:
        """Check health."""
        try:
            # Quick test: fetch one symbol
            quote = await self.get_quote("AAPL")
            return ProviderHealth(
                provider_name=self.name,
                is_healthy=True,
                request_count=self._request_count,
                error_count=self._error_count,
            )
        except Exception as e:
            return ProviderHealth(
                provider_name=self.name,
                is_healthy=False,
                error=str(e),
                last_error_at=datetime.utcnow(),
                request_count=self._request_count,
                error_count=self._error_count,
            )

    @staticmethod
    def _validate_ohlcv(df: Any, symbol: str) -> None:
        """Validate OHLCV data quality.

        Args:
            df: pandas DataFrame with OHLCV data
            symbol: Symbol being validated

        Raises:
            DataQualityError: If validation fails
        """
        if df.empty:
            return

        # Check for NaN in OHLC
        for col in ["Open", "High", "Low", "Close"]:
            if df[col].isna().any():
                raise DataQualityError(f"{symbol}: NaN values in {col}")

        # Check for inverted high/low
        if (df["High"] < df["Low"]).any():
            raise DataQualityError(f"{symbol}: High < Low detected")

        # Check for high < max(open, close)
        if (df["High"] < df[["Open", "Close"]].max(axis=1)).any():
            raise DataQualityError(f"{symbol}: High < max(Open, Close)")

        # Check for low > min(open, close)
        if (df["Low"] > df[["Open", "Close"]].min(axis=1)).any():
            raise DataQualityError(f"{symbol}: Low > min(Open, Close)")

        # Check for negative volume
        if (df["Volume"] < 0).any():
            raise DataQualityError(f"{symbol}: Negative volume detected")
