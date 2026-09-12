"""Repository Protocol definitions for type-safe repository pattern.

These are typing.Protocol classes — not base classes, but interfaces that define
the method signatures every repository must implement. This allows mypy to verify
that both real Firestore repositories and test fakes satisfy the same contract.

Services accept repositories typed against these protocols, enabling full unit test
isolation: tests inject fake in-memory implementations with zero database/emulator
dependencies.
"""

from datetime import date
from typing import Protocol

import pandas as pd


class StockRepository(Protocol):
    """Protocol for Stock data access."""

    async def get_by_symbol(self, symbol: str) -> dict | None:
        """Get a stock by symbol (document ID)."""
        ...

    async def list_active(self) -> list[dict[str, object]]:
        """List all active stocks."""
        ...

    async def list_universe(self) -> list[dict[str, object]]:
        """List all stocks in the active universe (in_universe=True)."""
        ...

    async def upsert(self, symbol: str, data: dict) -> None:
        """Create or update a stock document."""
        ...

    async def update_in_universe_batch(
        self, symbols_to_add: set[str], symbols_to_remove: set[str]
    ) -> None:
        """Batch update in_universe flag for multiple symbols."""
        ...


class PriceHistoryRepository(Protocol):
    """Protocol for PriceHistory (OHLCV bar) data access."""

    async def get_bars(
        self, symbol: str, start_date: date | None = None, end_date: date | None = None
    ) -> pd.DataFrame:
        """Get bars for a symbol, optionally filtered by date range. Returns DataFrame."""
        ...

    async def upsert_batch(self, symbol: str, bars: pd.DataFrame) -> None:
        """Batch upsert bars for a symbol. bars is a DataFrame with trade_date index."""
        ...

    async def count(self, symbol: str) -> int:
        """Count total bars for a symbol."""
        ...

    async def latest_date(self, symbol: str) -> date | None:
        """Get the most recent trade_date for a symbol."""
        ...


class StrategyVersionRepository(Protocol):
    """Protocol for StrategyVersion data access."""

    async def get(self, version: str) -> dict | None:
        """Get a strategy version by version string."""
        ...

    async def create(self, version: str, data: dict) -> None:
        """Create a new strategy version (fails if already exists)."""
        ...

    async def list_all(self) -> list[dict[str, object]]:
        """List all strategy versions."""
        ...


class UniverseMembershipRepository(Protocol):
    """Protocol for UniverseMembership (audit log) data access."""

    async def create(self, data: dict) -> str:
        """Create a new membership change record. Returns the auto-generated ID."""
        ...

    async def list_by_symbol_date(self, symbol: str, refresh_date: date) -> list[dict[str, object]]:
        """List membership changes for a symbol on a specific date."""
        ...

    async def list_by_date(self, refresh_date: date) -> list[dict[str, object]]:
        """List all membership changes on a specific date."""
        ...


class ScanRunRepository(Protocol):
    """Protocol for ScanRun data access."""

    async def create(self, run_id: str, data: dict) -> None:
        """Create a new scan run (fails if run_id already exists)."""
        ...

    async def get(self, run_id: str) -> dict | None:
        """Get a scan run by run_id."""
        ...

    async def get_by_date_version(self, trade_date: date, version: str) -> dict | None:
        """Get the scan run for a specific date and strategy version."""
        ...


class CandidateRepository(Protocol):
    """Protocol for Candidate (immutable snapshot) data access."""

    async def create_many(self, run_id: str, candidates: list[dict]) -> None:
        """Create multiple candidate records for a run.

        Must use .create() semantics (fails on duplicate (run_id, symbol)) to enforce
        immutability and prevent accidental updates.
        """
        ...

    async def get(self, run_id: str, symbol: str) -> dict | None:
        """Get a single candidate by run_id and symbol."""
        ...

    async def list_by_run(
        self, run_id: str, include_vetoed: bool = False, limit: int = 20
    ) -> list[dict[str, object]]:
        """List candidates for a run, optionally filtering vetoed status."""
        ...

    async def list_by_date(
        self, trade_date: date, include_vetoed: bool = False, limit: int = 20
    ) -> list[dict[str, object]]:
        """List candidates for a trade date (searches all runs on that date)."""
        ...
