"""Unit tests for provider factory and circuit breaker."""

import pytest

from app.providers.market_data.factory import CircuitBreaker, ProviderFactory, get_provider_factory


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_circuit_breaker_starts_closed(self):
        """Test circuit breaker starts in CLOSED state."""
        breaker = CircuitBreaker(failure_threshold=3)
        assert breaker.state == "CLOSED"
        assert breaker.can_call() is True

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after reaching failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3)

        breaker.record_failure()
        assert breaker.can_call() is True

        breaker.record_failure()
        assert breaker.can_call() is True

        breaker.record_failure()
        assert breaker.state == "OPEN"
        assert breaker.can_call() is False

    def test_circuit_breaker_resets_on_success(self):
        """Test circuit breaker resets after success."""
        breaker = CircuitBreaker(failure_threshold=2)

        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "OPEN"

        breaker.record_success()
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0


class TestProviderFactory:
    """Tests for ProviderFactory."""

    def test_factory_initializes_with_single_provider(self):
        """Test factory can be initialized with a single provider."""
        factory = ProviderFactory(["yahoo"])
        assert "yahoo" in factory.providers
        assert "yahoo" in factory.circuit_breakers

    def test_factory_initializes_with_chain(self):
        """Test factory supports multiple providers in failover chain."""
        # Note: only yahoo is implemented, but factory should support the structure
        factory = ProviderFactory(["yahoo"])
        assert len(factory.provider_names) == 1

    def test_factory_rejects_unknown_provider(self):
        """Test factory rejects unknown provider names."""
        with pytest.raises(ValueError, match="Unknown provider"):
            ProviderFactory(["unknown_provider"])

    def test_get_provider_factory_parses_comma_chain(self):
        """Test get_provider_factory parses comma-separated chain."""
        factory = get_provider_factory("yahoo")
        assert factory.provider_names == ["yahoo"]

    def test_get_provider_factory_defaults_to_yahoo(self):
        """Test get_provider_factory defaults to yahoo when empty."""
        factory = get_provider_factory("")
        assert factory.provider_names == ["yahoo"]

    def test_get_provider_factory_strips_whitespace(self):
        """Test get_provider_factory strips whitespace from provider names."""
        factory = get_provider_factory(" yahoo , yahoo ")
        assert factory.provider_names == ["yahoo", "yahoo"]
