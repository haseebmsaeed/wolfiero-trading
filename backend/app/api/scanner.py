"""Scanner API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.scanner import ScannerService
from app.services.market_data import MarketDataService
from app.config import get_settings
from app.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/scanner", tags=["scanner"])


@router.post("/run")
async def run_scan(
    trade_date: date | None = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a market scan for a specific date.

    Returns:
        202 with run_id; 409 if scan already running for that date/version

    Raises:
        HTTPException: If scan cannot be started
    """
    settings = get_settings()
    if trade_date is None:
        trade_date = date.today()

    market_data_service = MarketDataService(db)
    scanner_service = ScannerService(db, market_data_service)

    try:
        result = await scanner_service.scan(
            trade_date=trade_date,
            strategy_version=settings.strategy_version,
            force=False,
        )
        return {
            "status": "accepted",
            "run_id": result["run_id"],
            "trade_date": str(trade_date),
        }
    except Exception as e:
        logger.error("scan_trigger_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Scan failed: {e}")


@router.get("/runs/{run_id}")
async def get_scan_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get details of a scan run."""
    market_data_service = MarketDataService(db)
    scanner_service = ScannerService(db, market_data_service)

    try:
        result = await scanner_service.get_scan_run(run_id)
        if not result:
            raise HTTPException(status_code=404, detail="Scan run not found")
        return {
            "status": "success",
            "data": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_scan_run_failed", run_id=run_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get scan run: {e}")


@router.get("/candidates")
async def get_candidates(
    date_param: date | None = None,
    limit: int = 20,
    include_vetoed: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Get ranked candidates from the latest scan.

    Args:
        date_param: Date to get candidates for (defaults to today)
        limit: Max candidates to return
        include_vetoed: Include vetoed candidates

    Returns:
        List of candidates with scores and reasons
    """
    if date_param is None:
        date_param = date.today()

    market_data_service = MarketDataService(db)
    scanner_service = ScannerService(db, market_data_service)

    try:
        candidates = await scanner_service.get_candidates(
            trade_date=date_param,
            limit=limit,
            include_vetoed=include_vetoed,
        )

        if not candidates:
            return {
                "status": "success",
                "meta": {"message": "No candidates for this date"},
                "data": [],
            }

        return {
            "status": "success",
            "data": candidates,
        }
    except Exception as e:
        logger.error("get_candidates_failed", date=str(date_param), error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get candidates: {e}")
