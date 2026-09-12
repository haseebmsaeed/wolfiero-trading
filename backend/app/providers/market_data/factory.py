"""Market data provider factory with failover chain."""

from typing import ClassVar

from app.logging import get_logger
from app.providers.market_data.base import MarketDataProvider, ProviderError
from app.providers.market_data.yahoo import YahooProvider

logger = get_logger(__name__)


class CircuitBreaker:
    """Simple circuit breaker for provider failures."""

    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening
            reset_timeout: Seconds before attempting to reset
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self) -> None:
        """Record a successful call."""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = None  # Would be used for timeout

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                "circuit_breaker_opened",
                failure_count=self.failure_count,
            )

    def can_call(self) -> bool:
        """Check if a call can be made."""
        return self.state in ("CLOSED", "HALF_OPEN")


class ProviderFactory:
    """Factory for creating and managing provider instances."""

    PROVIDERS: ClassVar[dict[str, type[MarketDataProvider]]] = {
        "yahoo": YahooProvider,
    }

    def __init__(self, provider_names: list[str]):
        """Initialize factory with a failover chain.

        Args:
            provider_names: List of provider names in failover order
                           e.g. ["alpaca", "yahoo"]
        """
        self.provider_names = provider_names
        self.providers: dict[str, MarketDataProvider] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

        for name in provider_names:
            if name not in self.PROVIDERS:
                raise ValueError(f"Unknown provider: {name}")

            self.providers[name] = self.PROVIDERS[name]()
            self.circuit_breakers[name] = CircuitBreaker()

    async def get_quote(self, symbol: str) -> dict:
        """Get quote through failover chain.

        Tries each provider in order until one succeeds.
        """
        last_error = None

        for name in self.provider_names:
            breaker = self.circuit_breakers[name]

            if not breaker.can_call():
                logger.debug(
                    "provider_circuit_open",
                    provider=name,
                    state=breaker.state,
                )
                continue

            try:
                provider = self.providers[name]
                quote = await provider.get_quote(symbol)
                breaker.record_success()
                logger.debug("provider_success", provider=name, symbol=symbol)
                return quote.model_dump()

            except Exception as e:
                breaker.record_failure()
                last_error = e
                logger.warning(
                    "provider_failed",
                    provider=name,
                    symbol=symbol,
                    error=str(e),
                )

        # All providers failed
        raise ProviderError(
            f"All providers failed to get quote for {symbol}: {last_error}"
        )

    async def get_history(
        self,
        symbol: str,
        start: object,
        end: object,
        interval: str = "1d",
    ) -> dict[str, object]:
        """Get history through failover chain."""
        last_error = None

        for name in self.provider_names:
            breaker = self.circuit_breakers[name]

            if not breaker.can_call():
                continue

            try:
                provider = self.providers[name]
                frame = await provider.get_history(
                    symbol, start=start, end=end, interval=interval
                )
                breaker.record_success()
                logger.debug("provider_success", provider=name, symbol=symbol)
                return frame.model_dump()

            except Exception as e:
                breaker.record_failure()
                last_error = e
                logger.warning(
                    "provider_failed",
                    provider=name,
                    symbol=symbol,
                    error=str(e),
                )

        raise ProviderError(
            f"All providers failed to get history for {symbol}: {last_error}"
        )

    async def get_history_batch(
        self,
        symbols: list[str],
        start: object,
        end: object,
        interval: str = "1d",
    ) -> dict[str, object]:
        """Get history for multiple symbols."""
        last_error = None

        for name in self.provider_names:
            breaker = self.circuit_breakers[name]

            if not breaker.can_call():
                continue

            try:
                provider = self.providers[name]
                frames = await provider.get_history_batch(
                    symbols, start=start, end=end, interval=interval
                )
                breaker.record_success()
                logger.debug("provider_success", provider=name, symbol_count=len(frames))
                return {symbol: frame.model_dump() for symbol, frame in frames.items()}

            except Exception as e:
                breaker.record_failure()
                last_error = e
                logger.warning(
                    "provider_failed",
                    provider=name,
                    symbol_count=len(symbols),
                    error=str(e),
                )

        raise ProviderError(
            f"All providers failed to get batch history: {last_error}"
        )

    async def health(self) -> dict:
        """Get health status of all providers."""
        statuses = {}

        for name in self.provider_names:
            provider = self.providers[name]
            breaker = self.circuit_breakers[name]

            try:
                health = await provider.health()
                statuses[name] = {
                    "healthy": health.is_healthy,
                    "circuit": breaker.state,
                    "failures": breaker.failure_count,
                    "error": health.error,
                }
            except Exception as e:
                statuses[name] = {
                    "healthy": False,
                    "circuit": breaker.state,
                    "failures": breaker.failure_count,
                    "error": str(e),
                }

        return statuses


def get_provider_factory(provider_chain: str = "yahoo") -> ProviderFactory:
    """Create a provider factory from a comma-separated chain.

    Args:
        provider_chain: e.g. "alpaca,yahoo" or "yahoo"

    Returns:
        Configured ProviderFactory
    """
    names = [name.strip() for name in provider_chain.split(",") if name.strip()]
    if not names:
        names = ["yahoo"]

    return ProviderFactory(names)
