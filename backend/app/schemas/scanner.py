"""Scanner and scoring schemas."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class StageResult(BaseModel):
    """Result from a single scanner stage."""

    stage: str
    entered: int
    exited: int
    dropped_reasons: dict[str, int]
    timing_seconds: float


class ScanFunnel(BaseModel):
    """Complete scanner funnel results."""

    trade_date: date
    strategy_version: str
    stages: list[StageResult]
    total_survivors: int
    data_coverage_pct: Decimal


class ScoreBreakdown(BaseModel):
    """Detailed score component breakdown."""

    technical_score: dict
    momentum_score: dict
    relative_strength_score: dict
    volume_score: dict
    regime_fit_score: dict
    catalyst_score: dict
    reward_risk_score: dict
    total_score: Decimal


class CandidateResponse(BaseModel):
    """A candidate from the scan results."""

    rank: int
    symbol: str
    score: Decimal
    setup_type: str
    setup_quality: Decimal
    score_breakdown: ScoreBreakdown
    is_vetoed: bool
    veto_reasons: list[str] | None = None

    class Config:
        json_schema_extra = {"example": {  # noqa: RUF012
            "rank": 1,
            "symbol": "NVDA",
            "score": 82.5,
            "setup_type": "PULLBACK",
            "setup_quality": 0.75,
            "is_vetoed": False,
        }}


class ScanRunResponse(BaseModel):
    """Scan run details."""

    run_id: str
    trade_date: date
    status: str
    funnel: ScanFunnel | None = None
    error_message: str | None = None


class CandidatesListResponse(BaseModel):
    """List of candidates from a scan."""

    scan_date: date
    total_candidates: int
    total_vetoed: int
    candidates: list[CandidateResponse]
