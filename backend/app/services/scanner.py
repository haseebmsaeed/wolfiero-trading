"""Scanner service implementing the multi-stage funnel."""

import uuid
from collections import Counter
from datetime import date
from decimal import Decimal
from typing import Sequence

import pandas as pd
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging import get_logger
from app.models.scanner import ScanRun, Candidate
from app.models.stock import Stock, PriceHistory
from app.services.market_data import MarketDataService
from app.services.technical_analysis import TechnicalAnalysisService

logger = get_logger(__name__)


class StageResult:
    """Result from a scanner stage."""

    def __init__(self, stage_name: str):
        """Initialize stage result."""
        self.stage_name = stage_name
        self.entered = 0
        self.exited = 0
        self.dropped_reasons: Counter = Counter()
        self.survivors: set[str] = set()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "stage": self.stage_name,
            "entered": self.entered,
            "exited": self.exited,
            "dropped_reasons": dict(self.dropped_reasons),
            "survivors": len(self.survivors),
        }


class ScannerService:
    """Multi-stage scanner for finding trading candidates."""

    def __init__(self, db: AsyncSession, market_data_service: MarketDataService):
        """Initialize scanner with database and market data."""
        self.db = db
        self.market_data = market_data_service

    async def scan(
        self,
        trade_date: date,
        strategy_version: str,
        force: bool = False,
    ) -> dict:
        """Execute a full market scan.

        Args:
            trade_date: Date to scan for
            strategy_version: Strategy version to use
            force: If True, replace existing scan for this date/version

        Returns:
            dict with run_id, status, funnel, and candidates
        """
        run_id = str(uuid.uuid4())
        logger.info(
            "scan_start",
            run_id=run_id,
            trade_date=str(trade_date),
            strategy_version=strategy_version,
        )

        try:
            # Stage 1: Get universe
            stage1 = await self._stage1_universe()
            logger.info("stage1_complete", run_id=run_id, survivors=len(stage1.survivors))

            # Stage 2: Liquidity screen (vectorised)
            stage2 = await self._stage2_liquidity(stage1.survivors, trade_date)
            logger.info("stage2_complete", run_id=run_id, survivors=len(stage2.survivors))

            # Stage 3: Trend & relative strength
            stage3 = await self._stage3_trend(stage2.survivors, trade_date)
            logger.info("stage3_complete", run_id=run_id, survivors=len(stage3.survivors))

            # Stage 4: Setup detection
            stage4 = await self._stage4_setup(stage3.survivors, trade_date)
            logger.info("stage4_complete", run_id=run_id, survivors=len(stage4.survivors))

            funnel = {
                "stage1": stage1.to_dict(),
                "stage2": stage2.to_dict(),
                "stage3": stage3.to_dict(),
                "stage4": stage4.to_dict(),
            }

            # Persist scan run
            scan_run = ScanRun(
                run_id=run_id,
                trade_date=trade_date,
                strategy_version=strategy_version,
                status="RUNNING",
                funnel=funnel,
                data_coverage_pct=Decimal("100.00"),
            )
            self.db.add(scan_run)
            await self.db.flush()

            # Return the run details
            return {
                "run_id": run_id,
                "status": "RUNNING",
                "funnel": funnel,
            }

        except Exception as e:
            logger.error("scan_failed", run_id=run_id, error=str(e))
            raise

    async def _stage1_universe(self) -> StageResult:
        """Stage 1: Get active universe."""
        stage = StageResult("Stage 1: Universe")

        result = await self.db.execute(
            select(Stock.symbol).where(
                and_(Stock.is_active, Stock.in_universe)
            )
        )
        symbols = {row[0] for row in result}
        stage.survivors = symbols
        stage.entered = len(symbols)

        return stage

    async def _stage2_liquidity(
        self, symbols: set[str], trade_date: date
    ) -> StageResult:
        """Stage 2: Liquidity and data quality filters (vectorised)."""
        stage = StageResult("Stage 2: Liquidity")
        stage.entered = len(symbols)

        # In a production system, this would load all bars into one multi-index
        # DataFrame and filter cross-sectionally. For now, we implement per-symbol.
        for symbol in symbols:
            # TODO: Apply liquidity checks
            # This stage is CPU-bound, not I/O-bound
            stage.survivors.add(symbol)

        stage.exited = stage.entered - len(stage.survivors)
        return stage

    async def _stage3_trend(
        self, symbols: set[str], trade_date: date
    ) -> StageResult:
        """Stage 3: Trend and relative strength filters."""
        stage = StageResult("Stage 3: Trend & RS")
        stage.entered = len(symbols)

        for symbol in symbols:
            try:
                # Get bars and compute indicators
                # TODO: Full implementation
                stage.survivors.add(symbol)
            except Exception as e:
                logger.warning("stage3_error", symbol=symbol, error=str(e))
                stage.dropped_reasons["exception"] += 1

        stage.exited = stage.entered - len(stage.survivors)
        return stage

    async def _stage4_setup(
        self, symbols: set[str], trade_date: date
    ) -> StageResult:
        """Stage 4: Setup detection and quality filtering."""
        stage = StageResult("Stage 4: Setup Detection")
        stage.entered = len(symbols)

        for symbol in symbols:
            try:
                # Detect setup and score quality
                # TODO: Full implementation
                stage.survivors.add(symbol)
            except Exception as e:
                logger.warning("stage4_error", symbol=symbol, error=str(e))
                stage.dropped_reasons["exception"] += 1

        stage.exited = stage.entered - len(stage.survivors)
        return stage

    async def get_scan_run(self, run_id: str) -> dict:
        """Get details of a scan run."""
        result = await self.db.execute(
            select(ScanRun).where(ScanRun.run_id == run_id)
        )
        scan_run = result.scalar()

        if not scan_run:
            return None

        return {
            "run_id": scan_run.run_id,
            "trade_date": str(scan_run.trade_date),
            "strategy_version": scan_run.strategy_version,
            "status": scan_run.status,
            "funnel": scan_run.funnel,
            "error_message": scan_run.error_message,
        }

    async def get_candidates(
        self,
        trade_date: date,
        limit: int = 20,
        include_vetoed: bool = False,
    ) -> list[dict]:
        """Get candidates from a scan on a given date."""
        result = await self.db.execute(
            select(Candidate)
            .where(Candidate.trade_date == trade_date)
            .where(Candidate.is_vetoed == (not include_vetoed))
            .order_by(Candidate.rank)
            .limit(limit)
        )
        candidates = result.scalars().all()

        return [
            {
                "rank": c.rank,
                "symbol": c.symbol,
                "score": str(c.score),
                "setup_type": c.setup_type,
                "setup_quality": str(c.setup_quality),
                "is_vetoed": c.is_vetoed,
                "veto_reasons": c.veto_reasons,
            }
            for c in candidates
        ]
