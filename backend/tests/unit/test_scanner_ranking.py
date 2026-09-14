"""Unit tests for Stage 5 candidate ranking and the top-N cap."""

from datetime import date
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from app.repositories.fakes import (
    FakeCandidateRepository,
    FakePriceHistoryRepository,
    FakeScanRunRepository,
    FakeStockRepository,
)
from app.services.scanner import ScannerService

TRADE_DATE = date(2026, 9, 11)


def make_bars(seed: int, rows: int = 250) -> pd.DataFrame:
    """Build a synthetic uptrending OHLCV frame."""
    rng = np.random.default_rng(seed)
    close = pd.Series(100 + np.cumsum(rng.normal(0.2, 1.0, rows)))
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": rng.integers(1_000_000, 5_000_000, rows),
        },
        index=pd.date_range(end=TRADE_DATE, periods=rows, freq="B"),
    )


def build_scanner(
    symbols: list[str], max_candidates: int = 20
) -> tuple[ScannerService, FakeCandidateRepository]:
    """Wire a ScannerService against in-memory fakes."""
    stock_repo = FakeStockRepository()
    for symbol in symbols:
        stock_repo.stocks[symbol] = {
            "symbol": symbol,
            "is_active": True,
            "in_universe": True,
        }

    candidate_repo = FakeCandidateRepository()
    scanner = ScannerService(
        market_data_service=None,  # unused by _stage5_scoring
        stock_repository=stock_repo,
        price_history_repository=FakePriceHistoryRepository(),
        scan_run_repository=FakeScanRunRepository(),
        candidate_repository=candidate_repo,
        max_candidates=max_candidates,
    )
    return scanner, candidate_repo


def build_inputs(symbols: list[str]) -> tuple[dict, dict]:
    """Build setup_info and rs_percentiles that give each symbol a distinct score."""
    # Identical bars for every symbol so relative strength is the only thing
    # that moves the composite score — otherwise price-derived components vary
    # and the expected ordering is not deterministic.
    bars = make_bars(seed=0)
    setup_info = {symbol: ("PULLBACK", Decimal("0.80"), bars) for symbol in symbols}
    rs_percentiles = {symbol: Decimal(str(index + 1)) for index, symbol in enumerate(symbols)}
    return setup_info, rs_percentiles


@pytest.mark.asyncio
async def test_every_candidate_has_a_rank():
    """Firestore's order_by("rank") omits documents lacking the field."""
    symbols = ["AAA", "BBB", "CCC"]
    scanner, _ = build_scanner(symbols)
    setup_info, rs_percentiles = build_inputs(symbols)

    candidates = await scanner._stage5_scoring(
        setup_info, rs_percentiles, run_id="run-1", trade_date=TRADE_DATE
    )

    assert len(candidates) == 3
    assert all("rank" in c for c in candidates)


@pytest.mark.asyncio
async def test_ranks_are_dense_and_one_based():
    symbols = ["AAA", "BBB", "CCC", "DDD"]
    scanner, _ = build_scanner(symbols)
    setup_info, rs_percentiles = build_inputs(symbols)

    candidates = await scanner._stage5_scoring(
        setup_info, rs_percentiles, run_id="run-2", trade_date=TRADE_DATE
    )

    assert [c["rank"] for c in candidates] == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_rank_one_has_the_highest_score():
    symbols = ["AAA", "BBB", "CCC", "DDD"]
    scanner, _ = build_scanner(symbols)
    setup_info, rs_percentiles = build_inputs(symbols)

    candidates = await scanner._stage5_scoring(
        setup_info, rs_percentiles, run_id="run-3", trade_date=TRADE_DATE
    )

    scores = [c["score"] for c in candidates]
    assert scores == sorted(scores, reverse=True)
    # DDD was given the top RS percentile, so it must rank first.
    assert candidates[0]["symbol"] == "DDD"
    assert candidates[0]["rank"] == 1


@pytest.mark.asyncio
async def test_top_n_cap_is_applied():
    symbols = [f"S{index:02d}" for index in range(30)]
    scanner, candidate_repo = build_scanner(symbols, max_candidates=5)
    setup_info, rs_percentiles = build_inputs(symbols)

    candidates = await scanner._stage5_scoring(
        setup_info, rs_percentiles, run_id="run-4", trade_date=TRADE_DATE
    )

    assert len(candidates) == 5
    assert len(candidate_repo.candidates) == 5
    assert [c["rank"] for c in candidates] == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_cap_keeps_the_highest_scoring_candidates():
    symbols = [f"S{index:02d}" for index in range(10)]
    scanner, _ = build_scanner(symbols, max_candidates=3)
    setup_info, rs_percentiles = build_inputs(symbols)

    candidates = await scanner._stage5_scoring(
        setup_info, rs_percentiles, run_id="run-5", trade_date=TRADE_DATE
    )

    # RS percentile ascends with the symbol index, so the last three win.
    assert [c["symbol"] for c in candidates] == ["S09", "S08", "S07"]


@pytest.mark.asyncio
async def test_ranked_candidates_are_readable_back_by_date():
    """The full write-then-read path the /candidates endpoint exercises."""
    symbols = ["AAA", "BBB", "CCC"]
    scanner, candidate_repo = build_scanner(symbols)
    setup_info, rs_percentiles = build_inputs(symbols)

    await scanner._stage5_scoring(setup_info, rs_percentiles, run_id="run-6", trade_date=TRADE_DATE)

    listed = await candidate_repo.list_by_date(TRADE_DATE)

    assert [c["symbol"] for c in listed] == ["CCC", "BBB", "AAA"]
    assert [c["rank"] for c in listed] == [1, 2, 3]


@pytest.mark.asyncio
async def test_empty_setup_info_writes_nothing():
    scanner, candidate_repo = build_scanner([])

    candidates = await scanner._stage5_scoring({}, {}, run_id="run-7", trade_date=TRADE_DATE)

    assert candidates == []
    assert candidate_repo.candidates == {}


@pytest.mark.asyncio
async def test_symbol_missing_from_stock_repo_is_skipped():
    symbols = ["AAA", "BBB"]
    scanner, _ = build_scanner(symbols)
    setup_info, rs_percentiles = build_inputs([*symbols, "GHOST"])

    candidates = await scanner._stage5_scoring(
        setup_info, rs_percentiles, run_id="run-8", trade_date=TRADE_DATE
    )

    assert [c["symbol"] for c in candidates] == ["BBB", "AAA"]
    assert [c["rank"] for c in candidates] == [1, 2]
