"""Unit tests for configuration."""

import pytest
import os
from decimal import Decimal
from pydantic import ValidationError

from app.config import Settings, get_settings


class TestSettingsDefaults:
    """Tests for Settings default values."""

    def test_log_level_valid(self):
        """Test that log level is valid."""
        settings = Settings()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        assert settings.log_level in valid_levels

    def test_firestore_config_defaults(self):
        """Test Firestore configuration defaults."""
        settings = Settings()
        assert settings.gcp_project_id == "wolfiero-dev"
        assert isinstance(settings.google_application_credentials, str)

    def test_market_provider_defaults_to_yahoo(self):
        """Test that market provider defaults are set."""
        settings = Settings()
        assert settings.market_data_provider == "yahoo"


class TestSettingsValidation:
    """Tests for configuration validation."""

    def test_risk_per_trade_valid_range(self):
        """Test that risk_per_trade is within valid range (0-5%)."""
        settings = Settings(risk_per_trade_pct=1.5)
        assert 0 < settings.risk_per_trade_pct < 5

    def test_portfolio_heat_valid_range(self):
        """Test that max portfolio heat is within valid range."""
        settings = Settings(max_portfolio_heat_pct=6.0)
        assert 0 < settings.max_portfolio_heat_pct <= 50

    def test_min_reward_risk_valid(self):
        """Test that min reward/risk ratio is >= 1.0."""
        settings = Settings(min_reward_risk=2.0)
        assert settings.min_reward_risk >= 1.0

    def test_setup_quality_in_range(self):
        """Test that min_setup_quality is between 0 and 1."""
        settings = Settings(min_setup_quality=0.45)
        assert 0 <= settings.min_setup_quality <= 1


class TestSettingsCaching:
    """Tests for get_settings caching."""

    def test_get_settings_returns_singleton(self):
        """Test that get_settings uses LRU cache."""
        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the same object (cached)
        assert settings1 is settings2

    def test_settings_is_singleton(self):
        """Test that get_settings returns same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        # Verify it's truly cached
        assert id(settings1) == id(settings2)


class TestSettingsEnvironmentOverrides:
    """Tests for environment variable overrides."""

    def test_gcp_project_id_from_env(self, monkeypatch):
        """Test that GCP_PROJECT_ID env var overrides default."""
        test_project = "my-test-project"
        monkeypatch.setenv("GCP_PROJECT_ID", test_project)

        # Clear cache to force reload
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.gcp_project_id == test_project


class TestSettingsJSONEncoders:
    """Tests for JSON encoding of settings."""

    def test_settings_serializable(self):
        """Test that settings can be converted to dict."""
        settings = Settings(risk_per_trade_pct=0.025)

        # Should not raise when converting to dict
        d = settings.model_dump()
        assert d["risk_per_trade_pct"] == 0.025
        assert isinstance(d, dict)

    def test_settings_json_serializable(self):
        """Test that settings can be dumped to JSON."""
        settings = Settings()

        # Should be JSON-compatible
        d = settings.model_dump(mode="json")
        assert isinstance(d, dict)
        assert "log_level" in d
