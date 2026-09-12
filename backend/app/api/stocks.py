"""Stock analysis endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_market_data_service
from app.logging import get_logger
from app.services.market_data import MarketDataService
from app.services.setups import detect_best_setup
from app.services.technical_analysis import TechnicalAnalysisService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.post("/analyze")
async def analyze_stock(
    symbol: str,
    market_data: MarketDataService = Depends(get_market_data_service),
) -> dict:
    """Analyze a single stock completely.

    Args:
        symbol: Stock symbol (e.g. "NVDA")
        market_data: MarketDataService dependency

    Returns:
        Complete technical analysis with indicators, trend, setup
    """
    try:
        # Load bars from DB (or fetch if needed)
        try:
            bars = await market_data.get_bars(symbol, days=400)
        except Exception as e:
            logger.error("bars_fetch_failed", symbol=symbol, error=str(e))
            raise HTTPException(status_code=404, detail=f"No data for symbol {symbol}") from e

        # Technical analysis
        analysis_service = TechnicalAnalysisService(symbol, bars)
        snapshot = await analysis_service.analyze()

        # Setup detection
        setup = detect_best_setup(snapshot)

        return {
            "symbol": symbol,
            "trend": snapshot.trend.model_dump(),
            "momentum": snapshot.momentum.model_dump(),
            "volatility": snapshot.volatility.model_dump(),
            "volume": snapshot.volume.model_dump(),
            "setup": setup.to_dict(),
            "support": [s.model_dump() for s in snapshot.support[:3]],
            "resistance": [r.model_dump() for r in snapshot.resistance[:3]],
            "week_52_high": float(snapshot.week_52_high),
            "week_52_low": float(snapshot.week_52_low),
            "pct_from_52w_high": float(snapshot.pct_from_52w_high),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("analyze_failed", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail="Analysis failed") from e
