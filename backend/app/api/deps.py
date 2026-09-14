"""Dependency injection for API endpoints.

Provides repositories and services to FastAPI endpoints via Depends().
"""

from fastapi import Depends

from app.config import get_settings
from app.db.firestore import get_firestore_client
from app.providers.market_data import get_provider_factory
from app.repositories import (
    CandidateRepository,
    PriceHistoryRepository,
    ScanRunRepository,
    StockRepository,
    StrategyVersionRepository,
    UniverseMembershipRepository,
)
from app.services.market_data import MarketDataService
from app.services.scanner import ScannerService
from app.services.universe import UniverseService


def get_stock_repository() -> StockRepository:
    """Get StockRepository."""
    client = get_firestore_client()
    return StockRepository(client)


def get_price_history_repository() -> PriceHistoryRepository:
    """Get PriceHistoryRepository."""
    client = get_firestore_client()
    return PriceHistoryRepository(client)


def get_strategy_version_repository() -> StrategyVersionRepository:
    """Get StrategyVersionRepository."""
    client = get_firestore_client()
    return StrategyVersionRepository(client)


def get_universe_membership_repository() -> UniverseMembershipRepository:
    """Get UniverseMembershipRepository."""
    client = get_firestore_client()
    return UniverseMembershipRepository(client)


def get_scan_run_repository() -> ScanRunRepository:
    """Get ScanRunRepository."""
    client = get_firestore_client()
    return ScanRunRepository(client)


def get_candidate_repository() -> CandidateRepository:
    """Get CandidateRepository."""
    client = get_firestore_client()
    return CandidateRepository(client)


async def get_market_data_service(
    stock_repo: StockRepository = Depends(get_stock_repository),
    price_repo: PriceHistoryRepository = Depends(get_price_history_repository),
) -> MarketDataService:
    """Get MarketDataService with dependencies."""
    settings = get_settings()
    provider_factory = get_provider_factory(settings.market_data_provider)
    return MarketDataService(provider_factory, stock_repo, price_repo)  # type: ignore


async def get_universe_service(
    stock_repo: StockRepository = Depends(get_stock_repository),
    price_repo: PriceHistoryRepository = Depends(get_price_history_repository),
    membership_repo: UniverseMembershipRepository = Depends(
        get_universe_membership_repository
    ),
) -> UniverseService:
    """Get UniverseService with dependencies."""
    return UniverseService(stock_repo, price_repo, membership_repo)


async def get_scanner_service(
    market_data: MarketDataService = Depends(get_market_data_service),
    stock_repo: StockRepository = Depends(get_stock_repository),
    price_repo: PriceHistoryRepository = Depends(get_price_history_repository),
    scan_run_repo: ScanRunRepository = Depends(get_scan_run_repository),
    candidate_repo: CandidateRepository = Depends(get_candidate_repository),
) -> ScannerService:
    """Get ScannerService with dependencies."""
    settings = get_settings()
    return ScannerService(
        market_data,
        stock_repo,
        price_repo,
        scan_run_repo,
        candidate_repo,
        max_candidates=settings.scan_max_candidates,
    )
