"""Market data service — fetch, validate, and cache OHLCV data."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pandas as pd

from app.db import now_utc
from app.logging import get_logger
from app.providers.market_data import (
    Interval,
    MarketDataProvider,
    SymbolNotFoundError,
)
from app.repositories.protocols import PriceHistoryRepository, StockRepository
from app.schemas.market_data import OHLCVFrame

logger = get_logger(__name__)


class ValidationResult:
    """Result of OHLCV validation."""

    def __init__(self, is_valid: bool = True, errors: list[str] | None = None):
        """Initialize validation result.

        Args:
            is_valid: Whether validation passed
            errors: List of error messages if validation failed
        """
        self.is_valid = is_valid
        self.errors = errors or []

    def __bool__(self) -> bool:
        """Allow using result as boolean."""
        return self.is_valid


def validate_ohlcv(
    df: pd.DataFrame,
    symbol: str,
    max_daily_move_pct: float = 50.0,
) -> ValidationResult:
    """Validate OHLCV data quality.

    Args:
        df: pandas DataFrame with OHLCV data (indexed by date)
        symbol: Symbol being validated
        max_daily_move_pct: Maximum allowed single-day move (%)

    Returns:
        ValidationResult with errors if validation failed
    """
    errors = []

    if df.empty:
        return ValidationResult(is_valid=True)

    for col in ["Open", "High", "Low", "Close"]:
        if df[col].isna().any():
            bad_dates = df[df[col].isna()].index.tolist()
            errors.append(f"NaN values in {col} on dates: {bad_dates}")

    if (df["High"] < df["Low"]).any():
        bad_dates = df[df["High"] < df["Low"]].index.tolist()
        errors.append(f"High < Low on dates: {bad_dates}")

    if (df["High"] < df[["Open", "Close"]].max(axis=1)).any():
        bad_dates = df[df["High"] < df[["Open", "Close"]].max(axis=1)].index.tolist()
        errors.append(f"High < max(Open, Close) on dates: {bad_dates}")

    if (df["Low"] > df[["Open", "Close"]].min(axis=1)).any():
        bad_dates = df[df["Low"] > df[["Open", "Close"]].min(axis=1)].index.tolist()
        errors.append(f"Low > min(Open, Close) on dates: {bad_dates}")

    if (df["Volume"] < 0).any():
        bad_dates = df[df["Volume"] < 0].index.tolist()
        errors.append(f"Negative volume on dates: {bad_dates}")

    if (df["Volume"] == 0).any():
        logger.warning(f"{symbol}: Zero volume detected on some dates")

    pct_change = (df["Close"] / df["Open"] - 1) * 100
    extreme_moves = pct_change.abs() > max_daily_move_pct
    if extreme_moves.any():
        bad_dates = df[extreme_moves].index.tolist()
        errors.append(
            f"Extreme moves (>{max_daily_move_pct}%) on dates: {bad_dates} — "
            f"may indicate corporate action or bad data"
        )

    if df["Close"].isna().any():
        bad_dates = df[df["Close"].isna()].index.tolist()
        errors.append(f"NaN close price on dates: {bad_dates}")

    if errors:
        return ValidationResult(is_valid=False, errors=errors)

    return ValidationResult(is_valid=True)


class MarketDataService:
    """Service for fetching, validating, and caching market data."""

    def __init__(
        self,
        provider: MarketDataProvider,
        stock_repository: StockRepository,
        price_history_repository: PriceHistoryRepository,
        max_daily_move_pct: float = 50.0,
    ):
        """Initialize market data service.

        Args:
            provider: Market data provider
            stock_repository: Stock repository
            price_history_repository: PriceHistory repository
            max_daily_move_pct: Maximum allowed single-day move (%)
        """
        self.provider = provider
        self.stock_repo = stock_repository
        self.price_repo = price_history_repository
        self.max_daily_move_pct = max_daily_move_pct

    async def ensure_history(
        self,
        symbols: list[str],
        lookback_days: int = 400,
    ) -> dict[str, bool]:
        """Fetch and persist missing bars for symbols.

        Only fetches the tail — closed bars are immutable.

        Args:
            symbols: List of symbols
            lookback_days: How far back to fetch (trading days)

        Returns:
            Dict of {symbol: successfully_fetched}
        """
        results = {}
        end = date.today()
        start = end - timedelta(days=lookback_days)

        for symbol in symbols:
            try:
                # Verify symbol exists
                stock = await self.stock_repo.get_by_symbol(symbol)
                if not stock:
                    raise SymbolNotFoundError(f"Symbol {symbol} not in database")

                # Get existing bars
                existing_bars = await self.price_repo.get_bars(symbol, start_date=start, end_date=end)
                existing_dates = set(existing_bars.index) if not existing_bars.empty else set()

                # Fetch from provider
                frame = await self.provider.get_history(
                    symbol, start=start, end=end, interval=Interval.DAY
                )

                # Validate
                df = self._frame_to_dataframe(frame)
                validation = validate_ohlcv(df, symbol, self.max_daily_move_pct)

                if not validation:
                    logger.error(
                        "data_quality_error",
                        symbol=symbol,
                        errors=validation.errors,
                    )
                    results[symbol] = False
                    continue

                # Persist new bars
                new_bars = []
                for bar in frame.bars:
                    if bar.trade_date not in existing_dates:
                        new_bars.append({
                            "trade_date": bar.trade_date,
                            "open": bar.open,
                            "high": bar.high,
                            "low": bar.low,
                            "close": bar.close,
                            "volume": bar.volume,
                            "adjusted": bar.adjusted,
                            "source": self.provider.name,
                            "ingested_at": now_utc(),
                        })

                if new_bars:
                    new_df = pd.DataFrame(new_bars)
                    new_df.set_index("trade_date", inplace=True)
                    await self.price_repo.upsert_batch(symbol, new_df)

                results[symbol] = True
                logger.info("history_ensured", symbol=symbol, bar_count=len(frame.bars))

            except SymbolNotFoundError:
                logger.warning("symbol_not_found", symbol=symbol)
                results[symbol] = False
            except Exception as e:
                logger.error("history_fetch_failed", symbol=symbol, error=str(e))
                results[symbol] = False

        return results

    async def get_bars(
        self,
        symbol: str,
        days: int = 400,
    ) -> pd.DataFrame:
        """Get bars from the database as a pandas DataFrame.

        Returns:
            DataFrame with DatetimeIndex (market time, ascending, no duplicates)

        Raises:
            SymbolNotFoundError: Symbol not in database
        """
        df = await self.price_repo.get_bars(symbol)

        if df.empty:
            raise SymbolNotFoundError(f"No bars found for {symbol}")

        # Convert Decimal prices to float for compatibility with rest of system
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                df[col] = df[col].astype(float)

        # Rename columns to match expected format
        df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }, inplace=True)

        # Ensure index is DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.DatetimeIndex(df.index)
        df.index.name = "Date"

        return df.tail(days)

    @staticmethod
    def _frame_to_dataframe(frame: OHLCVFrame) -> pd.DataFrame:
        """Convert OHLCVFrame to pandas DataFrame."""
        return pd.DataFrame(
            {
                "Open": [float(b.open) for b in frame.bars],
                "High": [float(b.high) for b in frame.bars],
                "Low": [float(b.low) for b in frame.bars],
                "Close": [float(b.close) for b in frame.bars],
                "Volume": [b.volume for b in frame.bars],
            },
            index=pd.DatetimeIndex([b.trade_date for b in frame.bars]),
        )
