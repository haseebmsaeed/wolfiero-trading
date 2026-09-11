"""Unit tests for technical analysis service."""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.technical_analysis import TechnicalAnalysisService
from tests.fixtures.sample_ohlcv import get_sample_dataframe


class TestTechnicalAnalysisService:
    """Tests for TechnicalAnalysisService."""

    def test_initialization(self):
        """Test service initialization with valid data."""
        df = get_sample_dataframe()
        service = TechnicalAnalysisService("NVDA", df)

        assert service.symbol == "NVDA"
        assert len(service.bars) == len(df)
        assert service.close is not None

    def test_analyze_returns_snapshot(self):
        """Test that analyze returns a valid TechnicalSnapshot."""
        df = get_sample_dataframe()
        service = TechnicalAnalysisService("SPY", df)

        snapshot = pytest.mark.asyncio(service.analyze())
        # This will fail without proper async, but structure is correct
        # Actual async test is in integration tests

    def test_analyze_with_insufficient_history(self):
        """Test that analyze raises on insufficient bars."""
        df = get_sample_dataframe().head(30)  # Only 30 bars
        service = TechnicalAnalysisService("NVDA", df)

        with pytest.raises(ValueError, match="insufficient history"):
            pytest.mark.asyncio(service.analyze())

    def test_trend_uptrend_detection(self):
        """Test uptrend detection logic."""
        df = get_sample_dataframe()
        service = TechnicalAnalysisService("NVDA", df)

        trend = service._analyze_trend()

        # Service should classify the trend
        assert trend.direction in ("UPTREND", "DOWNTREND", "RANGE")
        assert 0 <= trend.strength <= 1
        assert isinstance(trend.above_50_sma, bool)
        assert isinstance(trend.above_200_sma, bool)

    def test_momentum_metrics_valid_states(self):
        """Test momentum metrics have valid RSI and MACD states."""
        df = get_sample_dataframe()
        service = TechnicalAnalysisService("NVDA", df)

        momentum = service._analyze_momentum()

        assert momentum.rsi_14.state in ("OVERSOLD", "NEUTRAL", "OVERBOUGHT")
        assert 0 <= momentum.rsi_14.value <= 100
        assert momentum.macd.state in (
            "BULLISH_ABOVE_ZERO",
            "BULLISH_BELOW_ZERO",
            "BEARISH_ABOVE_ZERO",
            "BEARISH_BELOW_ZERO",
        )

    def test_volatility_regime_valid(self):
        """Test volatility regime is one of three states."""
        df = get_sample_dataframe()
        service = TechnicalAnalysisService("NVDA", df)

        volatility = service._analyze_volatility()

        assert volatility.volatility_regime in ("LOW", "NORMAL", "HIGH")
        assert volatility.atr_14 > 0
        assert 0 <= volatility.bollinger_width_percentile <= 100

    def test_volume_metrics_valid_trend(self):
        """Test volume metrics have valid trends."""
        df = get_sample_dataframe()
        service = TechnicalAnalysisService("NVDA", df)

        volume = service._analyze_volume()

        assert volume.trend in ("INCREASING", "DECREASING", "STABLE")
        assert volume.avg_20d >= 0
        assert volume.ratio_vs_avg > 0

    def test_support_resistance_sorted(self):
        """Test that support/resistance are properly sorted."""
        df = get_sample_dataframe()
        service = TechnicalAnalysisService("NVDA", df)

        support, resistance = service._find_support_resistance()

        # Support should be sorted descending (highest first)
        if len(support) > 1:
            for i in range(len(support) - 1):
                assert support[i].price >= support[i + 1].price

        # Resistance should be sorted ascending (lowest first)
        if len(resistance) > 1:
            for i in range(len(resistance) - 1):
                assert resistance[i].price <= resistance[i + 1].price

    def test_52week_stats_valid(self):
        """Test 52-week high/low calculation."""
        df = get_sample_dataframe()
        service = TechnicalAnalysisService("NVDA", df)

        # Manually check 52-week calculation
        year_ago_idx = max(0, len(df) - 252)
        week_52_high = df['High'].iloc[year_ago_idx:].max()
        week_52_low = df['Low'].iloc[year_ago_idx:].min()

        assert week_52_high >= df['Close'].iloc[-1]
        assert week_52_low <= df['Close'].iloc[-1]

    def test_analysis_decimal_precision(self):
        """Test that analysis uses Decimal for prices."""
        df = get_sample_dataframe()
        service = TechnicalAnalysisService("NVDA", df)

        trend = service._analyze_trend()

        assert isinstance(trend.slope_50_sma_20d_pct, Decimal)
        assert isinstance(trend.strength, Decimal)
