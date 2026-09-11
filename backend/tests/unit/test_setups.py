"""Unit tests for setup detection."""

import pytest
from decimal import Decimal

from app.services.setups import SetupResult, detect_best_setup
from app.schemas.technical import (
    TechnicalSnapshot,
    TrendMetrics,
    MomentumMetrics,
    RSIMetrics,
    MACDState,
    VolatilityMetrics,
    VolumeMetrics,
    RelativeStrengthMetrics,
)


@pytest.fixture
def uptrend_snapshot():
    """Create a snapshot showing a strong uptrend."""
    return TechnicalSnapshot(
        symbol="NVDA",
        as_of_date="2026-01-15",
        close=Decimal("500.00"),
        trend=TrendMetrics(
            direction="UPTREND",
            strength=Decimal("0.8"),
            above_20_ema=True,
            above_50_sma=True,
            above_200_sma=True,
            ma_stack_aligned=True,
            slope_50_sma_20d_pct=Decimal("2.5"),
        ),
        momentum=MomentumMetrics(
            rsi_14=RSIMetrics(value=Decimal("60"), state="NEUTRAL"),
            macd=MACDState(
                line=Decimal("1.5"),
                signal=Decimal("1.2"),
                histogram=Decimal("0.3"),
                state="BULLISH_ABOVE_ZERO",
            ),
            roc_20d_pct=Decimal("3.2"),
        ),
        volatility=VolatilityMetrics(
            atr_14=Decimal("3.5"),
            atr_pct_of_price=Decimal("0.7"),
            realized_vol_20d_pct=Decimal("15.0"),
            volatility_regime="NORMAL",
            bollinger_width_percentile=Decimal("50"),
        ),
        volume=VolumeMetrics(
            avg_20d=50000000,
            ratio_vs_avg=Decimal("1.1"),
            dollar_volume_20d=Decimal("25000000"),
            trend="STABLE",
        ),
        relative_strength=RelativeStrengthMetrics(
            vs_spy_1m=Decimal("2.5"),
            vs_spy_3m=Decimal("5.0"),
            vs_spy_6m=Decimal("8.0"),
            percentile_rank=75,
            vs_sector_3m=Decimal("1.5"),
        ),
        support=[],
        resistance=[],
        week_52_high=Decimal("520.00"),
        week_52_low=Decimal("400.00"),
        pct_from_52w_high=Decimal("-3.8"),
        bars_available=400,
        last_bar_date="2026-01-15",
        gaps_detected=0,
    )


@pytest.fixture
def downtrend_snapshot():
    """Create a snapshot showing a downtrend."""
    return TechnicalSnapshot(
        symbol="SPY",
        as_of_date="2026-01-15",
        close=Decimal("450.00"),
        trend=TrendMetrics(
            direction="DOWNTREND",
            strength=Decimal("0.6"),
            above_20_ema=False,
            above_50_sma=False,
            above_200_sma=False,
            ma_stack_aligned=False,
            slope_50_sma_20d_pct=Decimal("-1.5"),
        ),
        momentum=MomentumMetrics(
            rsi_14=RSIMetrics(value=Decimal("35"), state="NEUTRAL"),
            macd=MACDState(
                line=Decimal("-0.5"),
                signal=Decimal("-0.3"),
                histogram=Decimal("-0.2"),
                state="BEARISH_BELOW_ZERO",
            ),
            roc_20d_pct=Decimal("-2.1"),
        ),
        volatility=VolatilityMetrics(
            atr_14=Decimal("4.0"),
            atr_pct_of_price=Decimal("0.9"),
            realized_vol_20d_pct=Decimal("18.0"),
            volatility_regime="NORMAL",
            bollinger_width_percentile=Decimal("40"),
        ),
        volume=VolumeMetrics(
            avg_20d=80000000,
            ratio_vs_avg=Decimal("1.3"),
            dollar_volume_20d=Decimal("36000000"),
            trend="INCREASING",
        ),
        relative_strength=RelativeStrengthMetrics(
            vs_spy_1m=Decimal("-1.0"),
            vs_spy_3m=Decimal("-2.5"),
            vs_spy_6m=Decimal("-4.0"),
            percentile_rank=25,
            vs_sector_3m=Decimal("-1.5"),
        ),
        support=[],
        resistance=[],
        week_52_high=Decimal("480.00"),
        week_52_low=Decimal("420.00"),
        pct_from_52w_high=Decimal("-6.3"),
        bars_available=400,
        last_bar_date="2026-01-15",
        gaps_detected=0,
    )


@pytest.fixture
def range_snapshot():
    """Create a snapshot showing a range-bound market."""
    return TechnicalSnapshot(
        symbol="QQQ",
        as_of_date="2026-01-15",
        close=Decimal("475.00"),
        trend=TrendMetrics(
            direction="RANGE",
            strength=Decimal("0.5"),
            above_20_ema=True,
            above_50_sma=False,
            above_200_sma=True,
            ma_stack_aligned=False,
            slope_50_sma_20d_pct=Decimal("0.1"),
        ),
        momentum=MomentumMetrics(
            rsi_14=RSIMetrics(value=Decimal("50"), state="NEUTRAL"),
            macd=MACDState(
                line=Decimal("0.1"),
                signal=Decimal("0.05"),
                histogram=Decimal("0.05"),
                state="BULLISH_ABOVE_ZERO",
            ),
            roc_20d_pct=Decimal("0.5"),
        ),
        volatility=VolatilityMetrics(
            atr_14=Decimal("3.0"),
            atr_pct_of_price=Decimal("0.6"),
            realized_vol_20d_pct=Decimal("12.0"),
            volatility_regime="LOW",
            bollinger_width_percentile=Decimal("30"),
        ),
        volume=VolumeMetrics(
            avg_20d=60000000,
            ratio_vs_avg=Decimal("0.9"),
            dollar_volume_20d=Decimal("28000000"),
            trend="STABLE",
        ),
        relative_strength=RelativeStrengthMetrics(
            vs_spy_1m=Decimal("0.5"),
            vs_spy_3m=Decimal("1.0"),
            vs_spy_6m=Decimal("2.0"),
            percentile_rank=50,
            vs_sector_3m=Decimal("0.5"),
        ),
        support=[],
        resistance=[],
        week_52_high=Decimal("495.00"),
        week_52_low=Decimal("450.00"),
        pct_from_52w_high=Decimal("-4.0"),
        bars_available=400,
        last_bar_date="2026-01-15",
        gaps_detected=0,
    )


class TestSetupResult:
    """Tests for SetupResult class."""

    def test_setup_result_creation(self):
        """Test creating a SetupResult."""
        result = SetupResult(
            setup_type="UPTREND",
            quality=Decimal("0.85"),
            direction="LONG",
            description="Strong uptrend",
        )

        assert result.setup_type == "UPTREND"
        assert result.quality == Decimal("0.85")
        assert result.direction == "LONG"

    def test_setup_result_to_dict(self):
        """Test SetupResult serialization."""
        result = SetupResult(
            setup_type="DOWNTREND",
            quality=Decimal("0.70"),
            direction="SHORT",
            description="Weak downtrend",
            triggered=True,
            trigger_condition="Close below MA50",
        )

        d = result.to_dict()

        assert d["type"] == "DOWNTREND"
        assert d["quality"] == 0.70
        assert d["direction"] == "SHORT"
        assert d["triggered"] is True


class TestDetectBestSetup:
    """Tests for detect_best_setup function."""

    def test_uptrend_setup_detected(self, uptrend_snapshot):
        """Test detection of uptrend setup."""
        setup = detect_best_setup(uptrend_snapshot)

        assert setup.setup_type == "UPTREND"
        assert setup.direction == "LONG"
        assert setup.quality == uptrend_snapshot.trend.strength
        assert setup.triggered is False

    def test_downtrend_setup_detected(self, downtrend_snapshot):
        """Test detection of downtrend setup."""
        setup = detect_best_setup(downtrend_snapshot)

        assert setup.setup_type == "DOWNTREND"
        assert setup.direction == "SHORT"
        assert setup.quality == downtrend_snapshot.trend.strength
        assert setup.triggered is False

    def test_no_setup_in_range(self, range_snapshot):
        """Test that RANGE trend produces NONE setup."""
        setup = detect_best_setup(range_snapshot)

        assert setup.setup_type == "NONE"
        assert setup.direction == "FLAT"
        assert setup.quality == Decimal("0")
        assert setup.triggered is False

    def test_setup_quality_bounded_0_1(self, uptrend_snapshot):
        """Test that setup quality is always between 0 and 1."""
        setup = detect_best_setup(uptrend_snapshot)

        assert Decimal("0") <= setup.quality <= Decimal("1")

    def test_setup_dict_keys(self, uptrend_snapshot):
        """Test that setup dict has all required keys."""
        setup = detect_best_setup(uptrend_snapshot)
        d = setup.to_dict()

        required_keys = {"type", "quality", "direction", "description", "triggered", "trigger_condition"}
        assert required_keys.issubset(set(d.keys()))
