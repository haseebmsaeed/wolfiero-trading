"""Firestore seeding — load initial universe and strategy version."""

import asyncio
from datetime import date, datetime, timedelta
import pandas as pd

from app.config import get_settings
from app.db.firestore import get_firestore_client
from app.db import now_utc
from app.providers.market_data import get_provider_factory
from app.providers.market_data.base import Interval
from app.repositories import (
    StockRepository,
    StrategyVersionRepository,
    PriceHistoryRepository,
)


async def seed_database() -> None:
    """Seed Firestore with initial data."""
    settings = get_settings()
    client = get_firestore_client()

    strategy_repo = StrategyVersionRepository(client)
    stock_repo = StockRepository(client)
    price_repo = PriceHistoryRepository(client)

    # Seed strategy version v1.0.0
    existing = await strategy_repo.get("v1.0.0")
    if not existing:
        await strategy_repo.create(
            "v1.0.0",
            {
                "weights": {
                    "technical_score": 0.25,
                    "momentum_score": 0.15,
                    "relative_strength": 0.15,
                    "volume_score": 0.10,
                    "regime_fit_score": 0.10,
                    "catalyst_score": 0.10,
                    "reward_risk_score": 0.15,
                },
                "thresholds": {
                    "universe_min_dollar_volume": settings.universe_min_dollar_volume,
                    "universe_min_price": settings.universe_min_price,
                    "scan_max_candidates": settings.scan_max_candidates,
                    "min_reward_risk": settings.min_reward_risk,
                    "min_setup_quality": settings.min_setup_quality,
                    "account_equity_usd": settings.account_equity_usd,
                    "risk_per_trade_pct": settings.risk_per_trade_pct,
                    "max_portfolio_heat_pct": settings.max_portfolio_heat_pct,
                    "max_positions": settings.max_positions,
                    "max_sector_exposure_pct": settings.max_sector_exposure_pct,
                    "hold_window_days": settings.hold_window_days,
                    "earnings_policy": settings.earnings_policy,
                },
                "notes": "Initial strategy version v1.0.0 with baseline weights",
                "activated_at": now_utc(),
            },
        )
        print("✓ Seeded StrategyVersion v1.0.0")
    else:
        print("✓ StrategyVersion v1.0.0 already exists")

    # Seed sample stocks with price history from Yahoo Finance
    symbols = ["NVDA", "AAPL", "TSLA", "QQQ", "SPY"]
    print(f"\nFetching price history for {symbols}...")

    try:
        provider_factory = get_provider_factory("yahoo")
        provider = provider_factory.providers["yahoo"]

        end_date = date.today()
        start_date = end_date - timedelta(days=400)

        # Fetch data for all symbols
        history_data = await provider.get_history_batch(
            symbols,
            start=start_date,
            end=end_date,
            interval=Interval.DAY,
        )

        for symbol, frame in history_data.items():
            # Create or update stock record
            stock_data = {
                "symbol": symbol,
                "sector": "Technology",
                "is_active": True,
                "in_universe": True,
            }
            await stock_repo.upsert(symbol, stock_data)

            # Add price history
            bars_list = []
            for bar in frame.bars:
                trade_date = (
                    bar.trade_date.date()
                    if hasattr(bar.trade_date, "date")
                    else bar.trade_date
                )
                bars_list.append({
                    "trade_date": trade_date,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "adjusted": bar.adjusted,
                    "source": "yahoo",
                    "ingested_at": now_utc(),
                })

            if bars_list:
                bars_df = pd.DataFrame(bars_list)
                bars_df.set_index("trade_date", inplace=True)
                await price_repo.upsert_batch(symbol, bars_df)
                print(f"✓ Seeded {symbol} with {len(bars_list)} days of history")

    except Exception as e:
        print(f"⚠ Could not fetch price history: {e}")
        print("  API will work once stocks and price history are in the database.")


if __name__ == "__main__":
    asyncio.run(seed_database())
