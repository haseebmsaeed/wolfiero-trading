"""Data repositories for Firestore-backed storage.

The repository pattern provides a thin abstraction over Firestore, allowing services
to be tested with fake in-memory implementations without touching the database or emulator.

All repositories implement Protocol interfaces defined in protocols.py, ensuring
type safety and enabling easy mock implementations for unit tests.
"""

from app.repositories.candidate import CandidateRepository
from app.repositories.price_history import PriceHistoryRepository
from app.repositories.scan_run import ScanRunRepository
from app.repositories.stock import StockRepository
from app.repositories.strategy_version import StrategyVersionRepository
from app.repositories.universe_membership import UniverseMembershipRepository

__all__ = [
    "CandidateRepository",
    "PriceHistoryRepository",
    "ScanRunRepository",
    "StockRepository",
    "StrategyVersionRepository",
    "UniverseMembershipRepository",
]
