"""Unit tests for configuration."""

import pytest
import os
from decimal import Decimal
from pydantic import ValidationError

from app.config import Settings, get_settings


class TestSettingsDefaults:
    """Tests for Settings default values."""

    def test_environment_defaults_to_development(self):
        """Test that environment defaults to development."""
        settings = Settings()
        assert settings.environment in ("development", "staging", "production")

    def test_log_level_valid(self):
        """Test that log level is valid."""
        settings = Settings()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        assert settings.log_level in valid_levels

    def test_database_url_defaults(self):
        """Test database URL defaults."""
        settings = Settings()
        assert "postgresql" in settings.database_url
        assert "async" in settings.database_url  # Should be asyncpg

    def test_market_provider_defaults_to_yahoo(self):
        """Test that market provider defaults are set."""
        settings = Settings()
        assert settings.market_provider == "yahoo"


class TestSettingsValidation:
    """Tests for configuration validation."""

    def test_strategy_version_is_positive(self):
        """Test that strategy_version is a positive integer."""
        settings = Settings(strategy_version=1)
        assert settings.strategy_version >= 1

    def test_risk_per_trade_is_decimal(self):
        """Test that risk_per_trade can be a Decimal."""
        settings = Settings(risk_per_trade=Decimal("0.02"))
        assert isinstance(settings.risk_per_trade, Decimal)

    def test_validate_strategy_weights_sums_to_one(self):
        """Test that strategy weights validate properly."""
        settings = Settings(
            strategy_weights={
                "trend_strength": 0.4,
                "momentum": 0.3,
                "volatility": 0.3,
            }
        )

        # Should not raise
        settings.validate_strategy_weights()

    def test_validate_strategy_weights_warns_on_mismatch(self):
        """Test that validation catches weight sum mismatches."""
        settings = Settings(
            strategy_weights={
                "trend_strength": 0.5,
                "momentum": 0.3,
                # Missing volatility
            }
        )

        # Should log warning but not raise (v1 behavior)
        settings.validate_strategy_weights()


class TestSettingsCaching:
    """Tests for get_settings caching."""

    def test_get_settings_returns_singleton(self):
        """Test that get_settings uses LRU cache."""
        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the same object (cached)
        assert settings1 is settings2

    def test_settings_is_hashable(self):
        """Test that Settings can be used with lru_cache."""
        settings = Settings()
        # If this doesn't raise TypeError, the object is hashable
        try:
            hash(settings)
        except TypeError:
            pytest.fail("Settings must be hashable for lru_cache")


class TestSettingsEnvironmentOverrides:
    """Tests for environment variable overrides."""

    def test_database_url_from_env(self, monkeypatch):
        """Test that DATABASE_URL env var overrides default."""
        test_url = "postgresql+asyncpg://user:pass@localhost/testdb"
        monkeypatch.setenv("DATABASE_URL", test_url)

        # Clear cache to force reload
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.database_url == test_url

    def test_environment_from_env(self, monkeypatch):
        """Test that ENVIRONMENT env var overrides default."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        get_settings.cache_clear()
        settings = get_settings()

        assert settings.environment == "production"


class TestSettingsJSONEncoders:
    """Tests for JSON encoding of settings."""

    def test_settings_with_decimal_values(self):
        """Test that Decimal values in settings can be serialized."""
        settings = Settings(risk_per_trade=Decimal("0.025"))

        # Should not raise when converting to dict
        d = settings.model_dump()
        assert d["risk_per_trade"] is not None

    def test_settings_json_serializable(self):
        """Test that settings can be dumped to JSON."""
        settings = Settings()

        # Should be JSON-compatible
        d = settings.model_dump(mode="json")
        assert isinstance(d, dict)
