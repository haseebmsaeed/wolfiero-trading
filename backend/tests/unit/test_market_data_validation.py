"""Unit tests for market data validation."""

import pandas as pd
import pytest
from decimal import Decimal
from datetime import date

from app.services.market_data import validate_ohlcv, ValidationResult


class TestValidateOHLCV:
    """Tests for OHLCV validation."""

    def test_valid_ohlcv_passes(self):
        """Test that valid OHLCV passes validation."""
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [102.0, 103.0, 104.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [101.0, 102.0, 103.0],
            'Volume': [1000000, 1100000, 1200000],
        })

        result = validate_ohlcv(df, 'NVDA')

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_empty_dataframe_is_valid(self):
        """Test that empty DataFrame is valid (no data is better than bad data)."""
        df = pd.DataFrame({
            'Open': [], 'High': [], 'Low': [], 'Close': [], 'Volume': []
        })

        result = validate_ohlcv(df, 'NVDA')

        assert result.is_valid is True

    def test_nan_in_open_fails(self):
        """Test that NaN in Open column fails validation."""
        df = pd.DataFrame({
            'Open': [100.0, float('nan'), 102.0],
            'High': [102.0, 103.0, 104.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [101.0, 102.0, 103.0],
            'Volume': [1000000, 1100000, 1200000],
        })

        result = validate_ohlcv(df, 'NVDA')

        assert result.is_valid is False
        assert any('NaN values in Open' in err for err in result.errors)

    def test_high_less_than_low_fails(self):
        """Test that High < Low fails validation."""
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [102.0, 100.0, 104.0],  # High < Low on row 2
            'Low': [99.0, 101.0, 101.0],
            'Close': [101.0, 102.0, 103.0],
            'Volume': [1000000, 1100000, 1200000],
        })

        result = validate_ohlcv(df, 'NVDA')

        assert result.is_valid is False
        assert any('High < Low' in err for err in result.errors)

    def test_high_less_than_max_open_close_fails(self):
        """Test that High < max(Open, Close) fails validation."""
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [102.0, 100.0, 104.0],  # High < Close on row 2
            'Low': [99.0, 100.0, 101.0],
            'Close': [101.0, 102.0, 103.0],
            'Volume': [1000000, 1100000, 1200000],
        })

        result = validate_ohlcv(df, 'NVDA')

        assert result.is_valid is False

    def test_low_greater_than_min_open_close_fails(self):
        """Test that Low > min(Open, Close) fails validation."""
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [102.0, 103.0, 104.0],
            'Low': [99.0, 100.0, 103.0],  # Low > Close on row 3
            'Close': [101.0, 102.0, 102.5],
            'Volume': [1000000, 1100000, 1200000],
        })

        result = validate_ohlcv(df, 'NVDA')

        assert result.is_valid is False

    def test_negative_volume_fails(self):
        """Test that negative volume fails validation."""
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [102.0, 103.0, 104.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [101.0, 102.0, 103.0],
            'Volume': [1000000, -1100000, 1200000],  # Negative
        })

        result = validate_ohlcv(df, 'NVDA')

        assert result.is_valid is False
        assert any('Negative volume' in err for err in result.errors)

    def test_extreme_move_flagged(self):
        """Test that extreme moves are flagged."""
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [102.0, 103.0, 160.0],  # 60% move
            'Low': [99.0, 100.0, 101.0],
            'Close': [101.0, 102.0, 160.0],  # 60% move from open
            'Volume': [1000000, 1100000, 1200000],
        })

        result = validate_ohlcv(df, 'NVDA', max_daily_move_pct=50.0)

        assert result.is_valid is False
        assert any('Extreme moves' in err for err in result.errors)

    def test_validation_result_bool(self):
        """Test that ValidationResult can be used as boolean."""
        valid = ValidationResult(is_valid=True)
        invalid = ValidationResult(is_valid=False, errors=["Test error"])

        assert bool(valid) is True
        assert bool(invalid) is False
