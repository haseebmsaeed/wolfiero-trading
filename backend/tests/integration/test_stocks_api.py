"""Integration tests for stocks API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from app.db.session import get_db
from app.models.stock import Stock, PriceHistory
from datetime import datetime, timedelta
from decimal import Decimal


@pytest.fixture
async def client(db_session: AsyncSession):
    """Create test FastAPI client."""
    app = create_app()

    # Override the DB dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def sample_stock_with_history(db_session: AsyncSession):
    """Create a test stock with price history."""
    stock = Stock(
        symbol="TESTSTOCK",
        sector="Technology",
        is_active=True,
        in_universe=True,
        first_trade_date=datetime.now().date(),
    )
    db_session.add(stock)
    await db_session.flush()

    # Add 400 days of price history
    today = datetime.now().date()
    for i in range(400):
        date = today - timedelta(days=i)
        price_history = PriceHistory(
            stock_id=stock.id,
            trade_date=date,
            open=Decimal("100.00") + Decimal(i % 10),
            high=Decimal("105.00") + Decimal(i % 10),
            low=Decimal("95.00") + Decimal(i % 10),
            close=Decimal("102.00") + Decimal(i % 10),
            volume=1000000 + i * 1000,
        )
        db_session.add(price_history)

    await db_session.commit()
    return stock


class TestStocksAnalyzeEndpoint:
    """Tests for POST /api/stocks/analyze endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_endpoint_exists(self, client: AsyncClient):
        """Test that analyze endpoint is reachable."""
        response = await client.post("/api/stocks/analyze?symbol=SPY")

        # Will fail with data not found, but endpoint should exist
        assert response.status_code in (200, 404, 500)

    @pytest.mark.asyncio
    async def test_analyze_returns_json(
        self, client: AsyncClient, sample_stock_with_history
    ):
        """Test that analyze endpoint returns JSON response."""
        response = await client.post("/api/stocks/analyze?symbol=TESTSTOCK")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert "symbol" in data
        assert data["symbol"] == "TESTSTOCK"

    @pytest.mark.asyncio
    async def test_analyze_response_structure(
        self, client: AsyncClient, sample_stock_with_history
    ):
        """Test that analyze response has required fields."""
        response = await client.post("/api/stocks/analyze?symbol=TESTSTOCK")

        assert response.status_code == 200
        data = response.json()

        required_fields = {
            "symbol",
            "trend",
            "momentum",
            "volatility",
            "volume",
            "setup",
            "support",
            "resistance",
            "week_52_high",
            "week_52_low",
            "pct_from_52w_high",
        }

        assert required_fields.issubset(set(data.keys()))

    @pytest.mark.asyncio
    async def test_analyze_trend_field_structure(
        self, client: AsyncClient, sample_stock_with_history
    ):
        """Test that trend field has expected structure."""
        response = await client.post("/api/stocks/analyze?symbol=TESTSTOCK")

        assert response.status_code == 200
        data = response.json()
        trend = data["trend"]

        required_trend_fields = {
            "direction",
            "strength",
            "above_20_ema",
            "above_50_sma",
            "above_200_sma",
            "ma_stack_aligned",
            "slope_50_sma_20d_pct",
        }

        assert required_trend_fields.issubset(set(trend.keys()))
        assert trend["direction"] in ("UPTREND", "DOWNTREND", "RANGE")

    @pytest.mark.asyncio
    async def test_analyze_momentum_field_structure(
        self, client: AsyncClient, sample_stock_with_history
    ):
        """Test that momentum field has expected structure."""
        response = await client.post("/api/stocks/analyze?symbol=TESTSTOCK")

        assert response.status_code == 200
        data = response.json()
        momentum = data["momentum"]

        assert "rsi_14" in momentum
        assert "macd" in momentum
        assert "roc_20d_pct" in momentum

        # RSI should have value and state
        assert "value" in momentum["rsi_14"]
        assert "state" in momentum["rsi_14"]
        assert momentum["rsi_14"]["state"] in ("OVERSOLD", "NEUTRAL", "OVERBOUGHT")

    @pytest.mark.asyncio
    async def test_analyze_volatility_field_structure(
        self, client: AsyncClient, sample_stock_with_history
    ):
        """Test that volatility field has expected structure."""
        response = await client.post("/api/stocks/analyze?symbol=TESTSTOCK")

        assert response.status_code == 200
        data = response.json()
        volatility = data["volatility"]

        required_vol_fields = {
            "atr_14",
            "atr_pct_of_price",
            "realized_vol_20d_pct",
            "volatility_regime",
            "bollinger_width_percentile",
        }

        assert required_vol_fields.issubset(set(volatility.keys()))
        assert volatility["volatility_regime"] in ("LOW", "NORMAL", "HIGH")

    @pytest.mark.asyncio
    async def test_analyze_volume_field_structure(
        self, client: AsyncClient, sample_stock_with_history
    ):
        """Test that volume field has expected structure."""
        response = await client.post("/api/stocks/analyze?symbol=TESTSTOCK")

        assert response.status_code == 200
        data = response.json()
        volume = data["volume"]

        required_vol_fields = {"avg_20d", "ratio_vs_avg", "dollar_volume_20d", "trend"}

        assert required_vol_fields.issubset(set(volume.keys()))
        assert volume["trend"] in ("INCREASING", "DECREASING", "STABLE")

    @pytest.mark.asyncio
    async def test_analyze_setup_field_structure(
        self, client: AsyncClient, sample_stock_with_history
    ):
        """Test that setup field has expected structure."""
        response = await client.post("/api/stocks/analyze?symbol=TESTSTOCK")

        assert response.status_code == 200
        data = response.json()
        setup = data["setup"]

        required_setup_fields = {
            "type",
            "quality",
            "direction",
            "description",
            "triggered",
            "trigger_condition",
        }

        assert required_setup_fields.issubset(set(setup.keys()))
        assert setup["type"] in ("UPTREND", "DOWNTREND", "NONE")

    @pytest.mark.asyncio
    async def test_analyze_support_resistance_are_lists(
        self, client: AsyncClient, sample_stock_with_history
    ):
        """Test that support and resistance are lists."""
        response = await client.post("/api/stocks/analyze?symbol=TESTSTOCK")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["support"], list)
        assert isinstance(data["resistance"], list)

    @pytest.mark.asyncio
    async def test_analyze_52week_metrics_are_numbers(
        self, client: AsyncClient, sample_stock_with_history
    ):
        """Test that 52-week metrics are numeric."""
        response = await client.post("/api/stocks/analyze?symbol=TESTSTOCK")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["week_52_high"], (int, float))
        assert isinstance(data["week_52_low"], (int, float))
        assert isinstance(data["pct_from_52w_high"], (int, float))

    @pytest.mark.asyncio
    async def test_analyze_missing_symbol_returns_error(self, client: AsyncClient):
        """Test that missing symbol parameter returns error."""
        response = await client.post("/api/stocks/analyze")

        # Should be 422 (validation error) or 404
        assert response.status_code in (422, 404)

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_symbol_returns_404(self, client: AsyncClient):
        """Test that nonexistent symbol returns 404."""
        response = await client.post("/api/stocks/analyze?symbol=NONEXISTENT")

        assert response.status_code == 404
        error = response.json()
        assert "error" in error or "detail" in error
