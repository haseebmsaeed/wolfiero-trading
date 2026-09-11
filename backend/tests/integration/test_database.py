"""Integration tests for database schema and operations."""

import pytest
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select

from app.models import Stock, PriceHistory, StrategyVersion


@pytest.mark.asyncio
async def test_stocks_table_creation(db_session):
    """Test that stocks table is created with correct schema."""
    # Insert a stock
    stock = Stock(
        symbol="NVDA",
        name="NVIDIA Corporation",
        exchange="NASDAQ",
        asset_type="COMMON_STOCK",
        sector="Technology",
        industry="Semiconductors",
        market_cap=Decimal("3000000000000"),
        shares_outstanding=2400000000,
        is_active=True,
        in_universe=True,
        first_trade_date=date(1999, 1, 22),
    )
    db_session.add(stock)
    await db_session.commit()

    # Query back
    result = await db_session.execute(select(Stock).where(Stock.symbol == "NVDA"))
    retrieved = result.scalar_one()

    assert retrieved.symbol == "NVDA"
    assert retrieved.name == "NVIDIA Corporation"
    assert retrieved.is_active is True
    assert retrieved.created_at is not None


@pytest.mark.asyncio
async def test_price_history_table_creation(db_session):
    """Test that price_history table is created with correct schema."""
    # First insert a stock
    stock = Stock(
        symbol="SPY",
        name="SPDR S&P 500 ETF",
        exchange="ARCA",
        asset_type="ETF",
        is_active=True,
        in_universe=True,
    )
    db_session.add(stock)
    await db_session.flush()

    # Insert a price history record
    bar = PriceHistory(
        stock_id=stock.id,
        trade_date=date(2026, 9, 10),
        open=Decimal("550.00"),
        high=Decimal("552.50"),
        low=Decimal("549.75"),
        close=Decimal("551.25"),
        volume=50000000,
        adjusted=True,
        source="yahoo",
        ingested_at=datetime.utcnow(),
    )
    db_session.add(bar)
    await db_session.commit()

    # Query back
    result = await db_session.execute(
        select(PriceHistory).where(PriceHistory.stock_id == stock.id)
    )
    retrieved = result.scalar_one()

    assert retrieved.close == Decimal("551.25")
    assert retrieved.volume == 50000000
    assert retrieved.adjusted is True


@pytest.mark.asyncio
async def test_strategy_version_table_creation(db_session):
    """Test that strategy_versions table is created with correct schema."""
    version = StrategyVersion(
        version="v1.0.0",
        weights={
            "technical_score": 0.25,
            "momentum_score": 0.15,
        },
        thresholds={
            "min_reward_risk": 2.0,
        },
        notes="Initial version",
        activated_at=datetime.utcnow(),
    )
    db_session.add(version)
    await db_session.commit()

    # Query back
    result = await db_session.execute(
        select(StrategyVersion).where(StrategyVersion.version == "v1.0.0")
    )
    retrieved = result.scalar_one()

    assert retrieved.version == "v1.0.0"
    assert retrieved.weights["technical_score"] == 0.25
    assert retrieved.thresholds["min_reward_risk"] == 2.0


@pytest.mark.asyncio
async def test_stock_timestamps(db_session):
    """Test that created_at and updated_at are set automatically."""
    stock = Stock(
        symbol="AAPL",
        is_active=True,
        in_universe=False,
    )
    db_session.add(stock)
    await db_session.commit()

    result = await db_session.execute(select(Stock).where(Stock.symbol == "AAPL"))
    retrieved = result.scalar_one()

    assert retrieved.created_at is not None
    assert retrieved.updated_at is not None
    assert isinstance(retrieved.created_at, datetime)
