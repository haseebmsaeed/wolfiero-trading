"""Admin endpoints for system operations."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.universe import UniverseService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/universe/refresh")
async def refresh_universe(
    trade_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger universe refresh.

    Args:
        trade_date: Date to refresh for (defaults to today)

    Returns:
        Refresh result with entered/exited counts
    """
    universe_service = UniverseService(db)

    try:
        result = await universe_service.refresh_universe(trade_date)
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
    db: AsyncSession = Depends(get_db),
):
    """Get current universe statistics.

    Returns:
        Universe size and sector breakdown
    """
    universe_service = UniverseService(db)

    try:
        stats = await universe_service.get_universe_stats()
        return {
            "status": "success",
            "data": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {e}")
