"""Unit tests for technical indicators with golden fixtures.

These tests use hand-verified indicator values from real market data.
Golden values are from TradingView and verified independently.
"""

import pytest
import numpy as np
import pandas as pd
from decimal import Decimal

from app.services import indicators
from tests.fixtures.sample_ohlcv import get_sample_dataframe, GOLDEN_VALUES


class TestMovingAverages:
    """Tests for moving average indicators."""

    def test_sma_basic(self):
        """Test simple moving average calculation."""
        df = get_sample_dataframe()
        sma_20 = indicators.sma(df['Close'], 20)

        # Last value should match golden
        assert abs(float(sma_20.iloc[-1]) - float(GOLDEN_VALUES['sma_20'])) < 0.1

        # First 19 values should be NaN
        assert sma_20.iloc[0:19].isna().all()

    def test_ema_basic(self):
        """Test exponential moving average calculation."""
        df = get_sample_dataframe()
        ema_12 = indicators.ema(df['Close'], 12)

        # Last value should match golden within tolerance
        assert abs(float(ema_12.iloc[-1]) - float(GOLDEN_VALUES['ema_12'])) < 1.0

    def test_sma_monotonicity(self):
        """Test that SMA responds slower than raw price."""
        df = get_sample_dataframe()
        sma = indicators.sma(df['Close'], 10)
        close = df['Close']

        # SMA should have smaller daily changes than close
        sma_changes = sma.diff().abs()
        close_changes = close.diff().abs()

        # Average change in SMA should be less than close
        assert sma_changes.mean() < close_changes.mean()


class TestMomentumIndicators:
    """Tests for momentum indicators."""

    def test_rsi_basic(self):
        """Test RSI calculation."""
        df = get_sample_dataframe()
        rsi = indicators.rsi(df['Close'], period=14)

        # Last value should match golden within tolerance
        assert abs(float(rsi.iloc[-1]) - float(GOLDEN_VALUES['rsi_14'])) < 2.0

        # RSI should be within [0, 100]
        assert rsi.dropna().between(0, 100).all()

    def test_rsi_bounds(self):
        """Test that RSI stays within [0, 100]."""
        df = get_sample_dataframe()
        rsi = indicators.rsi(df['Close'], period=14)

        valid_rsi = rsi.dropna()
        assert valid_rsi.min() >= 0
        assert valid_rsi.max() <= 100

    def test_macd_basic(self):
        """Test MACD calculation."""
        df = get_sample_dataframe()
        macd_line, signal, histogram = indicators.macd(
            df['Close'], fast=12, slow=26, signal=9
        )

        # Last values should match golden within tolerance
        assert abs(float(macd_line.iloc[-1]) - float(GOLDEN_VALUES['macd_line'])) < 0.5
        assert abs(float(signal.iloc[-1]) - float(GOLDEN_VALUES['macd_signal'])) < 0.5
        assert abs(float(histogram.iloc[-1]) - float(GOLDEN_VALUES['macd_histogram'])) < 0.2

    def test_macd_histogram_is_difference(self):
        """Test that MACD histogram = line - signal."""
        df = get_sample_dataframe()
        macd_line, signal, histogram = indicators.macd(df['Close'])

        # Histogram should equal line - signal (within floating point error)
        diff = (macd_line - signal - histogram).dropna()
        assert (diff.abs() < 1e-6).all()

    def test_roc_basic(self):
        """Test Rate of Change calculation."""
        df = get_sample_dataframe()
        roc = indicators.roc(df['Close'], period=5)

        # First 5 values should be NaN (need period bars before calculating)
        assert roc.iloc[:5].isna().all()

        # Non-NaN values should make sense (should have 15 valid values with 20 bars and period 5)
        valid_roc = roc.dropna()
        assert len(valid_roc) == 15


class TestVolatilityIndicators:
    """Tests for volatility indicators."""

    def test_atr_basic(self):
        """Test ATR calculation."""
        df = get_sample_dataframe()
        atr = indicators.atr(df['High'], df['Low'], df['Close'], period=14)

        # Last value should match golden within tolerance
        assert abs(float(atr.iloc[-1]) - float(GOLDEN_VALUES['atr_14'])) < 0.5

        # ATR should be positive
        assert atr.dropna().gt(0).all()

    def test_atr_non_negative(self):
        """Test that ATR is always non-negative."""
        df = get_sample_dataframe()
        atr = indicators.atr(df['High'], df['Low'], df['Close'])

        assert atr.dropna().ge(0).all()

    def test_bollinger_bands_relationship(self):
        """Test that bollinger band relationships hold."""
        df = get_sample_dataframe()
        upper, middle, lower = indicators.bollinger_bands(df['Close'], period=20, num_std=2)

        # Upper > Middle > Lower
        assert (upper.dropna() > middle.dropna()).all()
        assert (middle.dropna() > lower.dropna()).all()

    def test_realized_volatility_positive(self):
        """Test that realized volatility is always non-negative."""
        df = get_sample_dataframe()
        vol = indicators.realized_volatility(df['Close'])

        assert vol.dropna().ge(0).all()

    def test_bollinger_width_percentile_bounds(self):
        """Test that BB width percentile is [0, 100]."""
        df = get_sample_dataframe()
        percentile = indicators.bollinger_width_percentile(df['Close'], lookback=15)

        valid = percentile.dropna()
        if len(valid) > 0:
            assert valid.min() >= 0
            assert valid.max() <= 100


class TestVolumeIndicators:
    """Tests for volume indicators."""

    def test_volume_ratio_basic(self):
        """Test volume ratio calculation."""
        df = get_sample_dataframe()
        ratio = indicators.volume_ratio(df['Volume'], period=20)

        # Today's volume / 20-day average
        # Last value should be positive
        assert ratio.iloc[-1] > 0

    def test_volume_ratio_equals_one_at_average(self):
        """Test that volume ratio = 1 when volume equals average."""
        import pandas as pd

        # Create constant volume
        constant_volume = pd.Series([1000000] * 30)
        ratio = indicators.volume_ratio(constant_volume, period=10)

        # Should be 1.0 after warm-up
        assert ratio.iloc[-1] == pytest.approx(1.0)


class TestRelativeStrength:
    """Tests for relative strength indicators."""

    def test_rs_percentile_bounds(self):
        """Test that RS percentile is [0, 100]."""
        df = get_sample_dataframe()

        # Create fake percentile series (not real RS)
        prices = df['Close']
        percentile = indicators.rs_percentile(prices, lookback=10)

        valid = percentile.dropna()
        if len(valid) > 0:
            assert valid.min() >= 0
            assert valid.max() <= 100


class TestSwingPivots:
    """Tests for swing pivot detection."""

    def test_swing_pivots_returns_tuples(self):
        """Test that swing pivots returns (date, price) tuples."""
        df = get_sample_dataframe()
        highs, lows = indicators.swing_pivots(df['High'], df['Low'], lookback=3)

        # Should return lists of tuples
        assert isinstance(highs, list)
        assert isinstance(lows, list)

        if len(highs) > 0:
            assert len(highs[0]) == 2  # (date, price)

    def test_swing_pivots_no_duplicates(self):
        """Test that swing pivots has no duplicate dates."""
        df = get_sample_dataframe()
        highs, lows = indicators.swing_pivots(df['High'], df['Low'], lookback=2)

        high_dates = [h[0] for h in highs]
        low_dates = [l[0] for l in lows]

        # No duplicates within each
        assert len(high_dates) == len(set(high_dates))
        assert len(low_dates) == len(set(low_dates))


class TestIndicatorNaNHandling:
    """Tests for NaN handling in warm-up periods."""

    def test_sma_nan_warmup(self):
        """Test that SMA returns NaN during warm-up."""
        df = get_sample_dataframe()
        sma = indicators.sma(df['Close'], 20)

        # First period-1 should be NaN
        assert sma.iloc[0:19].isna().all()
        # Last should be valid
        assert not pd.isna(sma.iloc[-1])

    def test_rsi_nan_warmup(self):
        """Test that RSI returns some NaN values during initialization."""
        df = get_sample_dataframe()
        rsi = indicators.rsi(df['Close'], 14)

        # RSI has minimal NaN values (just first value due to diff)
        assert pd.isna(rsi.iloc[0])
        # But quickly produces valid values
        assert not pd.isna(rsi.iloc[1])

    def test_no_padding(self):
        """Test that indicators don't artificially pad with forward-fill."""
        df = get_sample_dataframe()
        rsi = indicators.rsi(df['Close'], 14)

        # RSI should have a minimal number of NaN values (only during initialization)
        nan_count = rsi.isna().sum()
        # With Wilder's smoothing, RSI starts with very few NaN values
        assert nan_count <= 2  # Only initial NaN due to diff()
