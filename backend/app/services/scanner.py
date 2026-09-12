"""Scanner service implementing the multi-stage funnel."""

import uuid
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from typing import NamedTuple

import pandas as pd
import pandas_market_calendars as mcal

from app.logging import get_logger
from app.repositories.protocols import (
    CandidateRepository,
    PriceHistoryRepository,
    ScanRunRepository,
    StockRepository,
)
from app.services import indicators
from app.services.market_data import MarketDataService
from app.services.scoring import ScoringService

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


class SetupResult(NamedTuple):
    """Setup detection result."""

    setup_type: str
    quality: Decimal


class ScannerService:
    """Multi-stage scanner for finding trading candidates."""

    MIN_BARS_STAGE2 = 250
    MIN_PRICE = Decimal("5.00")
    MIN_DOLLAR_VOLUME = Decimal("20000000")
    DATA_LOOKBACK_DAYS = 20
    MAX_DATA_STALENESS = 3
    MIN_SETUP_QUALITY = Decimal("0.45")
    MIN_RS_PERCENTILE = Decimal("50")

    def __init__(
        self,
        market_data_service: MarketDataService,
        stock_repository: StockRepository,
        price_history_repository: PriceHistoryRepository,
        scan_run_repository: ScanRunRepository,
        candidate_repository: CandidateRepository,
    ):
        """Initialize scanner with repositories and market data."""
        self.market_data = market_data_service
        self.stock_repo = stock_repository
        self.price_repo = price_history_repository
        self.scan_run_repo = scan_run_repository
        self.candidate_repo = candidate_repository
        self.calendar = mcal.get_calendar("NYSE")

    async def scan(
        self,
        trade_date: date,
        strategy_version: str,
        force: bool = False,
    ) -> dict:
        """Execute a full market scan."""
        run_id = str(uuid.uuid4())
        logger.info(
            "scan_start",
            run_id=run_id,
            trade_date=str(trade_date),
            strategy_version=strategy_version,
        )

        try:
            # Stage 1: Universe
            stage1 = await self._stage1_universe()
            logger.info("stage1_complete", run_id=run_id, survivors=len(stage1.survivors))

            # Stage 2: Liquidity (vectorised)
            stage2 = await self._stage2_liquidity(stage1.survivors, trade_date)
            logger.info("stage2_complete", run_id=run_id, survivors=len(stage2.survivors))

            # Stage 3: Trend & RS
            stage3, rs_percentiles = await self._stage3_trend(stage2.survivors, trade_date)
            logger.info("stage3_complete", run_id=run_id, survivors=len(stage3.survivors))

            # Stage 4: Setup detection (returns dict of symbol -> (setup_type, quality, bars))
            stage4, setup_info = await self._stage4_setup(stage3.survivors, trade_date)
            logger.info("stage4_complete", run_id=run_id, survivors=len(stage4.survivors))

            funnel = {
                "stage1": stage1.to_dict(),
                "stage2": stage2.to_dict(),
                "stage3": stage3.to_dict(),
                "stage4": stage4.to_dict(),
            }

            # Stage 5: Scoring and candidate creation
            candidates = await self._stage5_scoring(
                setup_info, rs_percentiles, run_id, trade_date
            )
            logger.info("stage5_complete", run_id=run_id, candidates=len(candidates))

            # Persist scan run
            await self.scan_run_repo.create(
                run_id,
                {
                    "trade_date": trade_date,
                    "strategy_version": strategy_version,
                    "status": "COMPLETED",
                    "funnel": funnel,
                    "data_coverage_pct": Decimal("100.00"),
                },
            )

            return {
                "run_id": run_id,
                "status": "COMPLETED",
                "funnel": funnel,
                "candidates": len(candidates),
            }

        except Exception as e:
            logger.error("scan_failed", run_id=run_id, error=str(e))
            raise

    async def _stage1_universe(self) -> StageResult:
        """Stage 1: Get active universe."""
        stage = StageResult("Stage 1: Universe")

        stocks = await self.stock_repo.list_universe()
        symbols = {stock["symbol"] for stock in stocks}
        stage.survivors = symbols
        stage.entered = len(symbols)

        return stage

    async def _stage2_liquidity(
        self, symbols: set[str], trade_date: date
    ) -> StageResult:
        """Stage 2: Liquidity and data quality filters (vectorised)."""
        stage = StageResult("Stage 2: Liquidity")
        stage.entered = len(symbols)

        lookback_start = trade_date - timedelta(days=self.DATA_LOOKBACK_DAYS + 10)

        for symbol in symbols:
            try:
                # Check: stock exists
                stock = await self.stock_repo.get_by_symbol(symbol)
                if not stock:
                    stage.dropped_reasons["no_stock_record"] += 1
                    continue

                # Check: minimum bars
                total_bars = await self.price_repo.count(symbol)
                if total_bars < self.MIN_BARS_STAGE2:
                    stage.dropped_reasons["insufficient_bars"] += 1
                    continue

                # Get recent bars for liquidity and freshness checks
                bars_df = await self.price_repo.get_bars(
                    symbol, start_date=lookback_start, end_date=trade_date
                )

                if bars_df.empty:
                    stage.dropped_reasons["no_recent_bars"] += 1
                    continue

                # Check: data freshness
                last_date = bars_df.index[-1]
                if hasattr(last_date, "date"):
                    last_date = last_date.date()
                trading_days_since = len(
                    self.calendar.valid_days(start_date=last_date, end_date=trade_date)
                )
                if trading_days_since > self.MAX_DATA_STALENESS:
                    stage.dropped_reasons["stale_data"] += 1
                    continue

                # Check: price threshold (last close)
                last_close_val = bars_df["close"].iloc[-1]
                if isinstance(last_close_val, Decimal):
                    last_close = last_close_val
                else:
                    last_close = Decimal(str(last_close_val))

                if last_close < self.MIN_PRICE:
                    stage.dropped_reasons["below_price_floor"] += 1
                    continue

                # Check: dollar volume (20-day average)
                if len(bars_df) >= self.DATA_LOOKBACK_DAYS:
                    lookback_bars = bars_df.tail(self.DATA_LOOKBACK_DAYS)
                    closes = lookback_bars["close"]
                    volumes = lookback_bars["volume"]

                    if isinstance(closes.iloc[0], Decimal):
                        avg_dollar_vol = (closes * volumes).sum() / len(closes)
                    else:
                        avg_dollar_vol = Decimal(str((closes * volumes).sum() / len(closes)))

                    if avg_dollar_vol < self.MIN_DOLLAR_VOLUME:
                        stage.dropped_reasons["low_dollar_volume"] += 1
                        continue

                # All checks passed
                stage.survivors.add(symbol)

            except Exception as e:
                logger.warning("stage2_error", symbol=symbol, error=str(e))
                stage.dropped_reasons["exception"] += 1
                continue

        stage.exited = stage.entered - len(stage.survivors)
        return stage

    async def _stage3_trend(
        self, symbols: set[str], trade_date: date
    ) -> tuple[StageResult, dict[str, Decimal]]:
        """Stage 3: Trend and relative strength filters.

        Returns:
            (StageResult, dict of symbol -> RS percentile)
        """
        stage = StageResult("Stage 3: Trend & RS")
        stage.entered = len(symbols)

        # Get RS percentiles for all survivors (batch computation)
        rs_percentiles = await self._compute_rs_percentiles(symbols)

        for symbol in symbols:
            try:
                # Get bars
                bars_df = await self.market_data.get_bars(symbol, days=250)
                if bars_df is None or len(bars_df) < 200:
                    stage.dropped_reasons["insufficient_bars"] += 1
                    continue

                close = bars_df["Close"]

                # Compute SMAs and EMA
                sma_50 = indicators.sma(close, 50)
                sma_200 = indicators.sma(close, 200)
                ema_20 = indicators.ema(close, 20)

                close_now = close.iloc[-1]
                sma_50_now = sma_50.iloc[-1]
                sma_200_now = sma_200.iloc[-1]
                ema_20_now = ema_20.iloc[-1]

                # Check: Close > 200-SMA
                if close_now <= sma_200_now:
                    stage.dropped_reasons["below_200sma"] += 1
                    continue

                # Check: Close > 50-SMA
                if close_now <= sma_50_now:
                    stage.dropped_reasons["below_50sma"] += 1
                    continue

                # Check: 50-SMA slope > 0
                sma_50_20d_ago = sma_50.iloc[-20]
                if sma_50_now <= sma_50_20d_ago:
                    stage.dropped_reasons["negative_slope"] += 1
                    continue

                # Check: RS percentile >= 50
                rs_pct = rs_percentiles.get(symbol, 0)
                if rs_pct < self.MIN_RS_PERCENTILE:
                    stage.dropped_reasons["low_rs"] += 1
                    continue

                # Check: Not extended (close <= 15% above 20-EMA)
                extension_pct = ((close_now / ema_20_now) - 1) * 100
                if extension_pct > 15:
                    stage.dropped_reasons["extended"] += 1
                    continue

                # Passed all checks
                stage.survivors.add(symbol)

            except Exception as e:
                logger.warning("stage3_error", symbol=symbol, error=str(e))
                stage.dropped_reasons["exception"] += 1
                continue

        stage.exited = stage.entered - len(stage.survivors)
        return stage, rs_percentiles

    async def _stage4_setup(
        self, symbols: set[str], trade_date: date
    ) -> tuple[StageResult, dict]:
        """Stage 4: Setup detection and quality filtering.

        Returns:
            (StageResult, dict of symbol -> (setup_type, quality, bars_df))
        """
        stage = StageResult("Stage 4: Setup Detection")
        stage.entered = len(symbols)
        setup_info = {}

        for symbol in symbols:
            try:
                # Get bars and detect best setup
                bars_df = await self.market_data.get_bars(symbol, days=250)
                if bars_df is None or len(bars_df) < 60:
                    stage.dropped_reasons["insufficient_bars"] += 1
                    continue

                # Run all setup detectors and keep best
                setups: list[SetupResult] = []

                # Breakout detection (placeholder)
                breakout_quality = await self._detect_breakout(bars_df)
                if breakout_quality > 0:
                    setups.append(SetupResult("BREAKOUT", breakout_quality))

                # Pullback detection (placeholder)
                pullback_quality = await self._detect_pullback(bars_df)
                if pullback_quality > 0:
                    setups.append(SetupResult("PULLBACK", pullback_quality))

                # Consolidation detection (placeholder)
                consolidation_quality = await self._detect_consolidation(bars_df)
                if consolidation_quality > 0:
                    setups.append(SetupResult("CONSOLIDATION", consolidation_quality))

                # Momentum continuation (placeholder)
                momentum_quality = await self._detect_momentum(bars_df)
                if momentum_quality > 0:
                    setups.append(SetupResult("MOMENTUM", momentum_quality))

                # Keep best setup
                if not setups:
                    stage.dropped_reasons["no_setups"] += 1
                    continue

                best_setup = max(setups, key=lambda s: s.quality)

                if best_setup.quality < self.MIN_SETUP_QUALITY:
                    stage.dropped_reasons["low_setup_quality"] += 1
                    continue

                # Passed: store setup info for candidate creation
                stage.survivors.add(symbol)
                setup_info[symbol] = (best_setup.setup_type, best_setup.quality, bars_df)

            except Exception as e:
                logger.warning("stage4_error", symbol=symbol, error=str(e))
                stage.dropped_reasons["exception"] += 1
                continue

        stage.exited = stage.entered - len(stage.survivors)
        return stage, setup_info

    async def _compute_rs_percentiles(self, symbols: set[str]) -> dict[str, Decimal]:
        """Compute relative strength percentiles for symbols."""
        percentiles = {}

        # Placeholder: compute 3-month RS percentile vs universe
        # Full implementation would compare each symbol's strength vs all others
        for symbol in symbols:
            try:
                bars = await self.market_data.get_bars(symbol, days=90)
                if bars is not None and len(bars) > 0:
                    # Simple momentum: ROC over 20 days
                    close = bars["Close"]
                    if len(close) > 20:
                        roc = ((close.iloc[-1] / close.iloc[-20]) - 1) * 100
                        # Placeholder: convert to percentile (0-100)
                        percentiles[symbol] = Decimal(str(min(100, max(0, roc + 50))))
                    else:
                        percentiles[symbol] = Decimal("50")
                else:
                    percentiles[symbol] = Decimal("50")
            except Exception:
                percentiles[symbol] = Decimal("50")

        return percentiles

    async def _detect_breakout(self, bars_df: pd.DataFrame) -> Decimal:
        """Detect breakout setup quality."""
        try:
            # Placeholder implementation
            high = bars_df["High"]
            volume = bars_df["Volume"]

            # Resistance: highest high in last 60 bars
            resistance = high.iloc[-60:].max()

            # Check if at resistance (within 2% above)
            current_close = bars_df["Close"].iloc[-1]
            if current_close >= resistance * 0.98:
                # Volume confirmation
                vol_avg = volume.iloc[-20:].mean()
                vol_ratio = volume.iloc[-1] / vol_avg if vol_avg > 0 else 1

                # Base quality: if volume >= 1.3x, quality score
                quality = Decimal("0.75") if vol_ratio >= 1.3 else Decimal("0.50")
                return quality

            return Decimal("0.25")
        except Exception:
            return Decimal("0.25")

    async def _detect_pullback(self, bars_df: pd.DataFrame) -> Decimal:
        """Detect pullback setup quality."""
        try:
            close = bars_df["Close"]
            volume = bars_df["Volume"]
            ema_20 = indicators.ema(close, 20)

            # Recent high and support
            recent_high = close.iloc[-30:].max()
            support = ema_20.iloc[-1]

            # Check if pulling back to support
            if support < close.iloc[-1] < recent_high:
                retracement_pct = (
                    (recent_high - close.iloc[-1]) / (recent_high - support) * 100
                )
                if 3 <= retracement_pct <= 15:
                    # Volume contraction on pullback - strong signal
                    vol_avg_20 = volume.iloc[-20:].mean()
                    vol_avg_3 = volume.iloc[-3:].mean()
                    if vol_avg_3 < vol_avg_20:
                        quality = Decimal(str(min(1.0, 0.8)))
                        return quality
                    else:
                        # No volume contraction but right retracement
                        quality = Decimal("0.55")
                        return quality

            return Decimal("0.20")
        except Exception:
            return Decimal("0.20")

    async def _detect_consolidation(self, bars_df: pd.DataFrame) -> Decimal:
        """Detect consolidation/coil setup quality."""
        try:
            # Placeholder implementation
            close = bars_df["Close"]
            high = bars_df["High"]
            low = bars_df["Low"]

            # Range over last 10 bars
            recent_range = (high.iloc[-10:].max() - low.iloc[-10:].min()) / close.iloc[
                -1
            ]

            # Check if range is tight (<10%)
            if recent_range < 0.10:
                # Bollinger bands compression
                bb_range = (
                    high.iloc[-20:].max() - low.iloc[-20:].min()
                ) / close.iloc[-1]
                compression = 1 - (recent_range / bb_range) if bb_range > 0 else 0

                quality = Decimal(str(min(1.0, compression)))
                return quality

            return Decimal("0")
        except Exception:
            return Decimal("0")

    async def _detect_momentum(self, bars_df: pd.DataFrame) -> Decimal:
        """Detect momentum continuation setup quality."""
        try:
            # Placeholder implementation
            close = bars_df["Close"]
            high = bars_df["High"]

            # RS percentile (3-month)
            if len(close) >= 63:
                roc_3m = ((close.iloc[-1] / close.iloc[-63]) - 1) * 100
                if roc_3m > 0:
                    # Distance to 52-week high
                    high_52w = high.iloc[-252:].max()
                    distance_pct = (1 - (close.iloc[-1] / high_52w)) * 100

                    if distance_pct < 10:
                        quality = Decimal(str(min(1.0, roc_3m / 100)))
                        return quality

            return Decimal("0")
        except Exception:
            return Decimal("0")

    async def get_scan_run(self, run_id: str) -> dict | None:
        """Get details of a scan run."""
        scan_run = await self.scan_run_repo.get(run_id)

        if not scan_run:
            return None

        return {
            "run_id": scan_run["run_id"],
            "trade_date": str(scan_run["trade_date"]),
            "strategy_version": scan_run["strategy_version"],
            "status": scan_run["status"],
            "funnel": scan_run["funnel"],
            "error_message": scan_run.get("error_message"),
        }

    async def get_candidates(
        self,
        trade_date: date,
        limit: int = 20,
        include_vetoed: bool = False,
    ) -> list[dict]:
        """Get candidates from a scan on a given date."""
        candidates = await self.candidate_repo.list_by_date(
            trade_date, include_vetoed=include_vetoed, limit=limit
        )

        return [
            {
                "rank": c.get("rank"),
                "symbol": c["symbol"],
                "score": str(c["score"]),
                "setup_type": c["setup_type"],
                "setup_quality": str(c["setup_quality"]),
                "is_vetoed": c.get("is_vetoed", False),
                "veto_reasons": c.get("veto_reasons"),
            }
            for c in candidates
        ]

    async def _stage5_scoring(
        self,
        setup_info: dict,
        rs_percentiles: dict[str, Decimal],
        run_id: str,
        trade_date: date,
    ) -> list[dict]:
        """Stage 5: Score candidates and create records.

        Args:
            setup_info: dict of symbol -> (setup_type, quality, bars_df)
            rs_percentiles: dict of symbol -> RS percentile
            run_id: Scan run ID
            trade_date: Trading date

        Returns:
            List of created candidate dicts
        """
        scoring_service = ScoringService()
        candidates = []

        for symbol, (setup_type, setup_quality, bars_df) in setup_info.items():
            try:
                rs_pct = rs_percentiles.get(symbol, Decimal("50"))

                # Score the candidate
                score_breakdown = scoring_service.score_candidate(
                    bars_df=bars_df,
                    setup_type=setup_type,
                    setup_quality=setup_quality,
                    rs_percentile=rs_pct,
                    regime="RISK_ON",
                )

                # Verify stock exists
                stock = await self.stock_repo.get_by_symbol(symbol)
                if not stock:
                    logger.warning("stage5_no_stock", symbol=symbol)
                    continue

                # Convert score breakdown to JSON-serializable dict
                score_breakdown_dict = {
                    name: {
                        "raw": float(c.raw),
                        "normalized": float(c.normalized),
                        "weight": float(c.weight),
                        "contribution": float(c.contribution),
                    }
                    for name, c in score_breakdown._asdict().items()
                    if name != "total_score"
                }

                # Create candidate dict
                candidate_dict = {
                    "run_id": run_id,
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "score": score_breakdown.total_score,
                    "score_breakdown": score_breakdown_dict,
                    "setup_type": setup_type,
                    "setup_quality": setup_quality,
                    "technical_snapshot": {
                        "sma_50": 0,
                        "sma_200": 0,
                        "ema_20": 0,
                        "rsi": 0,
                    },
                    "is_vetoed": False,
                    "veto_reasons": None,
                }

                candidates.append(candidate_dict)

            except Exception as e:
                logger.warning("stage5_error", symbol=symbol, error=str(e))
                continue

        # Commit all candidates
        if candidates:
            await self.candidate_repo.create_many(run_id, candidates)

        return candidates
