"""Admin endpoints for system operations."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_universe_service
from app.services.universe import UniverseService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/universe/refresh")
async def refresh_universe(
    trade_date: date | None = None,
    universe: UniverseService = Depends(get_universe_service),
) -> dict:
    """Manually trigger universe refresh.

    Args:
        trade_date: Date to refresh for (defaults to today)

    Returns:
        Refresh result with entered/exited counts
    """
    try:
        result = await universe.refresh_universe(trade_date)
        return {
            "status": "success",
            "data": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Universe refresh failed: {e}")


@router.get("/universe/stats")
async def get_universe_stats(
    universe: UniverseService = Depends(get_universe_service),
) -> dict:
    """Get current universe statistics.

    Returns:
        Universe size and sector breakdown
    """
    try:
        stats = await universe.get_universe_stats()
        return {
            "status": "success",
            "data": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {e}")
