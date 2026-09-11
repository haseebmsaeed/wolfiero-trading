"""Integration tests for market data service (provider + DB)."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.models import Stock, PriceHistory
from app.providers.market_data import YahooProvider
from app.services.market_data import MarketDataService


@pytest.mark.asyncio
class TestMarketDataService:
    """Tests for MarketDataService with real DB and provider."""

    @pytest.fixture
    async def service(self, db_session):
        """Create market data service with real provider."""
        provider = YahooProvider()
        return MarketDataService(provider, db_session)

    @pytest.fixture
    async def stock_spy(self, db_session):
        """Create SPY stock in database."""
        stock = Stock(
            symbol="SPY",
            name="SPDR S&P 500 ETF",
            exchange="ARCA",
            asset_type="ETF",
            is_active=True,
            in_universe=True,
        )
        db_session.add(stock)
        await db_session.commit()
        await db_session.refresh(stock)
        return stock

    @pytest.mark.asyncio
    async def test_ensure_history_fetches_and_persists(self, service, stock_spy, db_session):
        """Test that ensure_history fetches from provider and persists to DB."""
        end = date.today()
        start = end - timedelta(days=30)

        # Ensure history
        results = await service.ensure_history(["SPY"], lookback_days=30)

        assert results["SPY"] is True

        # Verify bars were persisted
        stmt = select(PriceHistory).where(
            PriceHistory.stock_id == stock_spy.id
        ).order_by(PriceHistory.trade_date)
        result = await db_session.execute(stmt)
        bars = result.scalars().all()

        assert len(bars) > 0
        assert all(isinstance(b.close, Decimal) for b in bars)
        assert bars[0].trade_date <= bars[-1].trade_date

    @pytest.mark.asyncio
    async def test_ensure_history_idempotent(self, service, stock_spy, db_session):
        """Test that ensure_history is idempotent (doesn't duplicate rows)."""
        # First call
        await service.ensure_history(["SPY"], lookback_days=30)

        stmt = select(PriceHistory).where(
            PriceHistory.stock_id == stock_spy.id
        )
        result = await db_session.execute(stmt)
        count_first = len(result.scalars().all())

        # Second call
        await service.ensure_history(["SPY"], lookback_days=30)

        result = await db_session.execute(stmt)
        count_second = len(result.scalars().all())

        # Should be the same
        assert count_first == count_second

    @pytest.mark.asyncio
    async def test_ensure_history_nonexistent_symbol(self, service, db_session):
        """Test that nonexistent symbol returns False."""
        results = await service.ensure_history(["NONEXISTENT999"], lookback_days=30)

        assert results["NONEXISTENT999"] is False

    @pytest.mark.asyncio
    async def test_get_bars_returns_dataframe(self, service, stock_spy):
        """Test that get_bars returns a properly formatted pandas DataFrame."""
        # Ensure we have data
        await service.ensure_history(["SPY"], lookback_days=30)

        # Get bars
        df = await service.get_bars("SPY", days=30)

        assert len(df) > 0
        assert "Open" in df.columns
        assert "High" in df.columns
        assert "Low" in df.columns
        assert "Close" in df.columns
        assert "Volume" in df.columns
        assert df.index.name == "Date"

        # Check that dates are ascending
        assert (df.index[:-1] <= df.index[1:]).all()

    @pytest.mark.asyncio
    async def test_get_bars_nonexistent_symbol(self, service):
        """Test that get_bars raises error for nonexistent symbol."""
        from app.providers.market_data import SymbolNotFoundError

        with pytest.raises(SymbolNotFoundError):
            await service.get_bars("NONEXISTENT999")

    @pytest.mark.asyncio
    async def test_ensure_history_batch(self, service, db_session):
        """Test ensuring history for multiple symbols."""
        # Create stocks
        for symbol in ["SPY", "QQQ", "IWM"]:
            stock = Stock(
                symbol=symbol,
                is_active=True,
                in_universe=True,
            )
            db_session.add(stock)

        await db_session.commit()

        # Ensure history for all
        results = await service.ensure_history(["SPY", "QQQ", "IWM"], lookback_days=30)

        assert all(results.values())
        assert len(results) == 3

        # Verify all have bars
        for symbol in ["SPY", "QQQ", "IWM"]:
            df = await service.get_bars(symbol, days=30)
            assert len(df) > 0
