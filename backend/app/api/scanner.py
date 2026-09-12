"""Scanner API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_scanner_service
from app.config import get_settings
from app.logging import get_logger
from app.services.scanner import ScannerService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/scanner", tags=["scanner"])


@router.post("/run")
async def run_scan(
    trade_date: date | None = None,
    scanner: ScannerService = Depends(get_scanner_service),
) -> dict:
    """Trigger a market scan for a specific date.

    Returns:
        202 with run_id; 409 if scan already running for that date/version

    Raises:
        HTTPException: If scan cannot be started
    """
    settings = get_settings()
    if trade_date is None:
        trade_date = date.today()

    try:
        result = await scanner.scan(
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
    scanner: ScannerService = Depends(get_scanner_service),
) -> dict:
    """Get details of a scan run."""
    try:
        result = await scanner.get_scan_run(run_id)
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
    scanner: ScannerService = Depends(get_scanner_service),
) -> dict:
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

    try:
        candidates = await scanner.get_candidates(
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
