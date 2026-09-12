"""Fake in-memory repository implementations for unit testing.

These implement all Repository Protocols using simple dict storage, enabling unit tests
to run with zero database/emulator/Docker dependencies. Perfect for testing services
in isolation.
"""

import uuid
from datetime import date

import pandas as pd


class FakeStockRepository:
    """In-memory Stock repository."""

    def __init__(self):
        self.stocks: dict[str, dict] = {}

    async def get_by_symbol(self, symbol: str) -> dict | None:
        return self.stocks.get(symbol)

    async def list_active(self) -> list[dict[str, object]]:
        return [s for s in self.stocks.values() if s.get("is_active", False)]

    async def list_universe(self) -> list[dict[str, object]]:
        return [
            s for s in self.stocks.values()
            if s.get("is_active", False) and s.get("in_universe", False)
        ]

    async def upsert(self, symbol: str, data: dict) -> None:
        self.stocks[symbol] = {**self.stocks.get(symbol, {"symbol": symbol}), **data}

    async def update_in_universe_batch(
        self, symbols_to_add: set[str], symbols_to_remove: set[str]
    ) -> None:
        for symbol in symbols_to_add:
            if symbol in self.stocks:
                self.stocks[symbol]["in_universe"] = True
        for symbol in symbols_to_remove:
            if symbol in self.stocks:
                self.stocks[symbol]["in_universe"] = False


class FakePriceHistoryRepository:
    """In-memory PriceHistory repository."""

    def __init__(self):
        self.bars: dict[str, pd.DataFrame] = {}

    async def get_bars(
        self, symbol: str, start_date: date | None = None, end_date: date | None = None
    ) -> pd.DataFrame:
        if symbol not in self.bars:
            return pd.DataFrame()
        df = self.bars[symbol]
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
        return df

    async def upsert_batch(self, symbol: str, bars: pd.DataFrame) -> None:
        if symbol not in self.bars:
            self.bars[symbol] = bars.copy()
        else:
            existing = self.bars[symbol]
            new_df = pd.concat([existing, bars])
            self.bars[symbol] = new_df[~new_df.index.duplicated(keep='last')]

    async def count(self, symbol: str) -> int:
        if symbol not in self.bars:
            return 0
        return len(self.bars[symbol])

    async def latest_date(self, symbol: str) -> date | None:
        if symbol not in self.bars or len(self.bars[symbol]) == 0:
            return None
        return self.bars[symbol].index[-1].date() if hasattr(
            self.bars[symbol].index[-1], 'date'
        ) else self.bars[symbol].index[-1]


class FakeStrategyVersionRepository:
    """In-memory StrategyVersion repository."""

    def __init__(self):
        self.versions: dict[str, dict] = {}

    async def get(self, version: str) -> dict | None:
        return self.versions.get(version)

    async def create(self, version: str, data: dict) -> None:
        if version in self.versions:
            raise ValueError(f"Strategy version {version} already exists")
        self.versions[version] = {**data, "version": version}

    async def list_all(self) -> list[dict[str, object]]:
        return list(self.versions.values())


class FakeUniverseMembershipRepository:
    """In-memory UniverseMembership repository."""

    def __init__(self):
        self.memberships: dict[str, dict] = {}

    async def create(self, data: dict) -> str:
        membership_id = str(uuid.uuid4())
        self.memberships[membership_id] = {**data, "id": membership_id}
        return membership_id

    async def list_by_symbol_date(self, symbol: str, refresh_date: date) -> list[dict[str, object]]:
        return [
            m for m in self.memberships.values()
            if m.get("symbol") == symbol and m.get("refresh_date") == refresh_date
        ]

    async def list_by_date(self, refresh_date: date) -> list[dict[str, object]]:
        return [m for m in self.memberships.values() if m.get("refresh_date") == refresh_date]


class FakeScanRunRepository:
    """In-memory ScanRun repository."""

    def __init__(self):
        self.runs: dict[str, dict] = {}

    async def create(self, run_id: str, data: dict) -> None:
        if run_id in self.runs:
            raise ValueError(f"Scan run {run_id} already exists")
        self.runs[run_id] = {**data, "run_id": run_id}

    async def get(self, run_id: str) -> dict | None:
        return self.runs.get(run_id)

    async def get_by_date_version(self, trade_date: date, version: str) -> dict | None:
        for run in self.runs.values():
            if run.get("trade_date") == trade_date and run.get("strategy_version") == version:
                return run
        return None


class FakeCandidateRepository:
    """In-memory Candidate repository."""

    def __init__(self):
        self.candidates: dict[str, dict] = {}

    async def create_many(self, run_id: str, candidates: list[dict]) -> None:
        for cand in candidates:
            key = f"{run_id}_{cand['symbol']}"
            if key in self.candidates:
                raise ValueError(f"Candidate {key} already exists (immutable)")
            self.candidates[key] = {**cand, "run_id": run_id}

    async def get(self, run_id: str, symbol: str) -> dict | None:
        key = f"{run_id}_{symbol}"
        return self.candidates.get(key)

    async def list_by_run(
        self, run_id: str, include_vetoed: bool = False, limit: int = 20
    ) -> list[dict[str, object]]:
        results = [
            c for c in self.candidates.values()
            if c.get("run_id") == run_id
            and (include_vetoed or not c.get("is_vetoed", False))
        ]
        results.sort(key=lambda c: c.get("rank", 999))
        return results[:limit]

    async def list_by_date(
        self, trade_date: date, include_vetoed: bool = False, limit: int = 20
    ) -> list[dict[str, object]]:
        results = [
            c for c in self.candidates.values()
            if c.get("trade_date") == trade_date
            and (include_vetoed or not c.get("is_vetoed", False))
        ]
        results.sort(key=lambda c: c.get("rank", 999))
        return results[:limit]
