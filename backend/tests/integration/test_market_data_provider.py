"""Integration tests for market data providers."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.providers.market_data import YahooProvider, get_provider_factory
from app.providers.market_data.base import SymbolNotFoundError, DataQualityError


@pytest.mark.asyncio
class TestYahooProvider:
    """Tests for Yahoo Finance provider."""

    @pytest.fixture
    def provider(self):
        """Create a Yahoo provider instance."""
        return YahooProvider()

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Yahoo API may not return currentPrice in test environment")
    async def test_get_quote(self, provider):
        """Test getting a current quote."""
        # Use a well-known ticker
        quote = await provider.get_quote("SPY")

        assert quote.symbol == "SPY"
        assert quote.price > 0
        assert isinstance(quote.price, Decimal)
        assert quote.volume > 0
        assert quote.is_realtime is True

    @pytest.mark.asyncio
    async def test_get_quote_nonexistent_symbol(self, provider):
        """Test that nonexistent symbol raises error."""
        with pytest.raises(SymbolNotFoundError):
            await provider.get_quote("NONEXISTENT999")

    @pytest.mark.asyncio
    async def test_get_history(self, provider):
        """Test getting historical data."""
        end = date.today()
        start = end - timedelta(days=30)

        frame = await provider.get_history("SPY", start=start, end=end)

        assert frame.symbol == "SPY"
        assert len(frame.bars) > 0
        assert frame.bars[0].trade_date <= frame.bars[-1].trade_date

        # Check bar validity
        for bar in frame.bars:
            assert bar.high >= bar.low
            assert bar.high >= max(bar.open, bar.close)
            assert bar.low <= min(bar.open, bar.close)
            assert bar.volume >= 0

    @pytest.mark.asyncio
    async def test_get_history_nonexistent_symbol(self, provider):
        """Test that nonexistent symbol raises error."""
        end = date.today()
        start = end - timedelta(days=30)

        with pytest.raises(SymbolNotFoundError):
            await provider.get_history("NONEXISTENT999", start=start, end=end)

    @pytest.mark.asyncio
    async def test_get_history_batch(self, provider):
        """Test getting history for multiple symbols."""
        end = date.today()
        start = end - timedelta(days=30)
        symbols = ["SPY", "QQQ", "IWM"]

        results = await provider.get_history_batch(
            symbols, start=start, end=end
        )

        # All symbols should be present
        assert len(results) == len(symbols)
        for symbol in symbols:
            assert symbol in results
            assert len(results[symbol].bars) > 0

    @pytest.mark.asyncio
    async def test_get_fundamentals(self, provider):
        """Test getting fundamentals."""
        fundamentals = await provider.get_fundamentals("SPY")

        assert fundamentals.symbol == "SPY"
        # ETF may not have all fields, but should have something
        assert fundamentals.market_cap or fundamentals.shares_outstanding

    @pytest.mark.asyncio
    async def test_health(self, provider):
        """Test provider health check."""
        health = await provider.health()

        assert health.provider_name == "yahoo"
        assert health.is_healthy is True
        assert health.request_count > 0


@pytest.mark.asyncio
class TestProviderFactory:
    """Tests for ProviderFactory."""

    @pytest.fixture
    def factory(self):
        """Create a provider factory."""
        return get_provider_factory("yahoo")

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Yahoo API may not return currentPrice in test environment")
    async def test_factory_get_quote_fallback(self, factory):
        """Test that factory successfully gets quote."""
        quote = await factory.get_quote("SPY")

        assert quote["symbol"] == "SPY"
        assert quote["price"] > 0

    @pytest.mark.asyncio
    async def test_factory_get_history_fallback(self, factory):
        """Test that factory successfully gets history."""
        end = date.today()
        start = end - timedelta(days=30)

        frame = await factory.get_history("SPY", start=start, end=end)

        assert frame["symbol"] == "SPY"
        assert len(frame["bars"]) > 0

    @pytest.mark.asyncio
    async def test_factory_health(self, factory):
        """Test factory health check."""
        health = await factory.health()

        assert "yahoo" in health
        assert health["yahoo"]["healthy"] is True
        assert health["yahoo"]["circuit"] in ("CLOSED", "HALF_OPEN")
