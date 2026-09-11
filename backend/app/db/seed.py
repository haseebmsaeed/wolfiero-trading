"""Database seeding — load initial universe and strategy version."""

import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import StrategyVersion


async def seed_database() -> None:
    """Seed the database with initial data."""
    settings = get_settings()

    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=None, expire_on_commit=False)

    async with async_session() as session:
        # Seed strategy version v1.0.0
        strategy = StrategyVersion(
            version="v1.0.0",
            weights={
                "technical_score": 0.25,
                "momentum_score": 0.15,
                "relative_strength": 0.15,
                "volume_score": 0.10,
                "regime_fit_score": 0.10,
                "catalyst_score": 0.10,
                "reward_risk_score": 0.15,
            },
            thresholds={
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
            notes="Initial strategy version v1.0.0 with baseline weights",
            activated_at=datetime.utcnow(),
        )
        session.add(strategy)
        await session.commit()

        print("✓ Seeded StrategyVersion v1.0.0")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
