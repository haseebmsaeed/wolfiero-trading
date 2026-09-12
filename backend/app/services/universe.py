"""Universe construction and refresh service."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pandas_market_calendars as mcal

from app.logging import get_logger
from app.repositories.protocols import (
    PriceHistoryRepository,
    StockRepository,
    UniverseMembershipRepository,
)

logger = get_logger(__name__)


class UniverseService:
    """Construct and maintain the tradeable universe."""

    MIN_DOLLAR_VOLUME = Decimal("20000000")
    MIN_PRICE = Decimal("5.00")
    MIN_BARS = 250
    MAX_DATA_STALENESS_DAYS = 3
    MIN_IPO_AGE_DAYS = 60
    DATA_LOOKBACK_DAYS = 20

    LEVERAGED_PATTERNS = ["3X", "2X", "-2X", "-3X", "INVERSE", "SHORT", "BEAR"]
    BLOCKLISTED_ETFS = {"TQQQ", "SQQQ", "UVXY", "VIXY", "SVXY"}

    def __init__(
        self,
        stock_repository: StockRepository,
        price_history_repository: PriceHistoryRepository,
        universe_membership_repository: UniverseMembershipRepository,
    ):
        """Initialize with repositories."""
        self.stock_repo = stock_repository
        self.price_repo = price_history_repository
        self.membership_repo = universe_membership_repository
        self.calendar = mcal.get_calendar("NYSE")

    async def refresh_universe(self, trade_date: date | None = None) -> dict:
        """Refresh the universe for a given date.

        Args:
            trade_date: Date to refresh for (defaults to today)

        Returns:
            dict with entered/exited counts and details

        Raises:
            ValueError: If result is empty
        """
        if trade_date is None:
            trade_date = date.today()

        logger.info("universe_refresh_start", trade_date=str(trade_date))

        all_symbols = await self._get_all_symbols()
        logger.info("all_symbols_fetched", count=len(all_symbols))

        survivors = await self._apply_liquidity_screen(all_symbols, trade_date)
        logger.info("liquidity_screen_complete", survivors=len(survivors))

        survivors = await self._apply_exclusions(survivors)
        logger.info("exclusions_applied", survivors=len(survivors))

        if len(survivors) == 0:
            raise ValueError(
                "Universe is empty; check data source and liquidity screens"
            )

        if len(survivors) < 2000 or len(survivors) > 4000:
            logger.warning(
                "universe_size_outside_band",
                size=len(survivors),
                trade_date=str(trade_date),
            )

        result = await self._update_universe(survivors, trade_date)

        logger.info(
            "universe_refresh_complete",
            new_count=len(survivors),
            entered=result["entered_count"],
            exited=result["exited_count"],
        )

        return result

    async def get_universe_stats(self) -> dict:
        """Get current universe statistics."""
        stocks = await self.stock_repo.list_universe()
        total = len(stocks)

        sector_counts: dict[str, int] = {}
        for stock in stocks:
            sector = stock.get("sector")
            if sector:
                sector_counts[sector] = sector_counts.get(sector, 0) + 1

        return {
            "total_symbols": total,
            "distinct_sectors": len(sector_counts),
            "sector_breakdown": sector_counts,
        }

    async def _get_all_symbols(self) -> set[str]:
        """Get all active tradeable symbols from database."""
        stocks = await self.stock_repo.list_active()
        return {stock["symbol"] for stock in stocks}

    async def _apply_liquidity_screen(
        self, symbols: set[str], trade_date: date
    ) -> set[str]:
        """Apply liquidity and data quality filters."""
        survivors = set()
        lookback_start = trade_date - timedelta(days=self.DATA_LOOKBACK_DAYS + 10)

        for symbol in symbols:
            try:
                bars_df = await self.price_repo.get_bars(
                    symbol, start_date=lookback_start, end_date=trade_date
                )

                if bars_df.empty:
                    continue

                # Check: last bar freshness
                last_date = bars_df.index[-1]
                if hasattr(last_date, "date"):
                    last_date = last_date.date()
                trading_days = self.calendar.valid_days(
                    start_date=last_date, end_date=trade_date
                )
                days_stale = len(trading_days) - 1

                if days_stale > self.MAX_DATA_STALENESS_DAYS:
                    continue

                # Check: minimum bars in history
                total_bars = await self.price_repo.count(symbol)
                if total_bars < self.MIN_BARS:
                    continue

                # Check: price threshold (use last close)
                last_close_val = bars_df["close"].iloc[-1]
                if isinstance(last_close_val, Decimal):
                    last_close = last_close_val
                else:
                    last_close = Decimal(str(last_close_val))

                if last_close < self.MIN_PRICE:
                    continue

                # Check: dollar volume (20-day average)
                if len(bars_df) >= self.DATA_LOOKBACK_DAYS:
                    lookback_bars = bars_df.tail(self.DATA_LOOKBACK_DAYS)
                    closes = lookback_bars["close"]
                    volumes = lookback_bars["volume"]

                    if isinstance(closes.iloc[0], Decimal):
                        avg_dollar_vol = (closes * volumes).sum() / len(closes)
                    else:
                        avg_dollar_vol = Decimal(str((closes * volumes).sum() / len(closes)))

                    if avg_dollar_vol < self.MIN_DOLLAR_VOLUME:
                        continue

                survivors.add(symbol)

            except Exception as e:
                logger.warning("liquidity_screen_error", symbol=symbol, error=str(e))
                continue

        return survivors

    async def _apply_exclusions(self, symbols: set[str]) -> set[str]:
        """Apply exclusion rules: leveraged ETFs, recent IPOs, blocklisted."""
        survivors = set()

        for symbol in symbols:
            try:
                stock = await self.stock_repo.get_by_symbol(symbol)

                if not stock:
                    continue

                if stock.get("is_blocklisted"):
                    continue

                if stock.get("asset_type") == "ETF":
                    if symbol in self.BLOCKLISTED_ETFS:
                        continue
                    if any(pattern in symbol.upper() for pattern in self.LEVERAGED_PATTERNS):
                        continue

                first_trade = stock.get("first_trade_date")
                if first_trade:
                    age_days = (date.today() - first_trade).days
                    if age_days < self.MIN_IPO_AGE_DAYS:
                        continue

                survivors.add(symbol)

            except Exception as e:
                logger.warning("exclusion_check_error", symbol=symbol, error=str(e))
                continue

        return survivors

    async def _update_universe(
        self, new_universe: set[str], trade_date: date
    ) -> dict:
        """Update stocks.in_universe and log membership changes."""
        current_stocks = await self.stock_repo.list_universe()
        current_universe = {stock["symbol"]: stock for stock in current_stocks}

        entered = new_universe - set(current_universe.keys())
        exited = set(current_universe.keys()) - new_universe

        # Batch update in_universe flags
        await self.stock_repo.update_in_universe_batch(entered, exited)

        # Log membership changes
        for symbol in entered:
            await self.membership_repo.create({
                "symbol": symbol,
                "action": "ENTERED",
                "reason": "Passed liquidity and exclusion screening",
                "refresh_date": trade_date,
            })

        for symbol in exited:
            await self.membership_repo.create({
                "symbol": symbol,
                "action": "EXITED",
                "reason": "Failed screening or removed from source",
                "refresh_date": trade_date,
            })

        return {
            "entered_count": len(entered),
            "exited_count": len(exited),
            "new_total": len(new_universe),
            "entered_symbols": sorted(entered),
            "exited_symbols": sorted(exited),
        }
