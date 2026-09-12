"""Scanner and universe document shapes for Firestore."""

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class UniverseMembership(BaseModel):
    """Firestore document: universe_membership/{id}. Append-only audit log of universe changes."""

    id: str
    symbol: str
    action: str
    reason: str
    refresh_date: date


class ScanRun(BaseModel):
    """Firestore document: scan_runs/{run_id}. One scan execution with funnel metrics."""

    run_id: str
    trade_date: date
    strategy_version: str
    status: str = "RUNNING"
    funnel: dict[str, Any]
    data_coverage_pct: Decimal | None = None
    stage_timings: dict[str, Any] | None = None
    error_message: str | None = None


class Candidate(BaseModel):
    """Firestore subcollection: scan_runs/{run_id}/candidates/{symbol}. Immutable point-in-time scan result."""

    run_id: str
    symbol: str
    trade_date: date
    rank: int | None = None
    score: Decimal
    score_breakdown: dict[str, Any]
    setup_type: str
    setup_quality: Decimal
    technical_snapshot: dict[str, Any]
    is_vetoed: bool = False
    veto_reasons: list[str] | None = None
