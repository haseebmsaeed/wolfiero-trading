"""Unit tests for Decimal ↔ scaled-integer conversion.

Verifies that money/score values round-trip correctly through Firestore storage
without losing precision — ensuring we never accidentally drift into float territory.
"""

import pytest
from decimal import Decimal

from app.db.money import to_firestore_int, from_firestore_int


class TestMoneyConversion:
    """Test Decimal ↔ scaled-int conversion for prices."""

    def test_price_to_firestore_int_basic(self):
        """Convert a simple price to integer."""
        price = Decimal("123.4567")
        result = to_firestore_int(price, scale=4)
        assert result == 1234567

    def test_price_from_firestore_int_basic(self):
        """Convert an integer back to Decimal price."""
        result = from_firestore_int(1234567, scale=4)
        assert result == Decimal("123.4567")

    def test_price_round_trip(self):
        """Verify round-trip fidelity for prices."""
        original = Decimal("99.9999")
        converted = to_firestore_int(original, scale=4)
        restored = from_firestore_int(converted, scale=4)
        assert restored == original

    def test_price_zero(self):
        """Handle zero price."""
        price = Decimal("0.0000")
        converted = to_firestore_int(price, scale=4)
        assert converted == 0
        restored = from_firestore_int(converted, scale=4)
        assert restored == Decimal("0.0000")

    def test_price_negative(self):
        """Handle negative prices (e.g., returns, losses)."""
        price = Decimal("-50.1234")
        converted = to_firestore_int(price, scale=4)
        assert converted == -501234
        restored = from_firestore_int(converted, scale=4)
        assert restored == price

    def test_price_large_values(self):
        """Handle large prices."""
        price = Decimal("999999.9999")
        converted = to_firestore_int(price, scale=4)
        assert converted == 9999999999
        restored = from_firestore_int(converted, scale=4)
        assert restored == price


class TestScoreConversion:
    """Test Decimal ↔ scaled-int conversion for scores (2 decimal places)."""

    def test_score_to_firestore_int_basic(self):
        """Convert a simple score to integer."""
        score = Decimal("87.65")
        result = to_firestore_int(score, scale=2)
        assert result == 8765

    def test_score_from_firestore_int_basic(self):
        """Convert an integer back to Decimal score."""
        result = from_firestore_int(8765, scale=2)
        assert result == Decimal("87.65")

    def test_score_round_trip(self):
        """Verify round-trip fidelity for scores."""
        original = Decimal("56.78")
        converted = to_firestore_int(original, scale=2)
        restored = from_firestore_int(converted, scale=2)
        assert restored == original

    def test_score_zero(self):
        """Handle zero score."""
        score = Decimal("0.00")
        converted = to_firestore_int(score, scale=2)
        assert converted == 0
        restored = from_firestore_int(converted, scale=2)
        assert restored == Decimal("0.00")

    def test_score_max_100(self):
        """Handle score at max (100.00)."""
        score = Decimal("100.00")
        converted = to_firestore_int(score, scale=2)
        assert converted == 10000
        restored = from_firestore_int(converted, scale=2)
        assert restored == score


class TestSetupQualityConversion:
    """Test conversion for setup quality (0-1 scale, 2 decimal places)."""

    def test_setup_quality_mid_range(self):
        """Convert mid-range setup quality."""
        quality = Decimal("0.55")
        converted = to_firestore_int(quality, scale=2)
        assert converted == 55
        restored = from_firestore_int(converted, scale=2)
        assert restored == quality

    def test_setup_quality_high(self):
        """Convert high setup quality."""
        quality = Decimal("0.95")
        converted = to_firestore_int(quality, scale=2)
        assert converted == 95
        restored = from_firestore_int(converted, scale=2)
        assert restored == quality

    def test_setup_quality_low(self):
        """Convert low setup quality."""
        quality = Decimal("0.10")
        converted = to_firestore_int(quality, scale=2)
        assert converted == 10
        restored = from_firestore_int(converted, scale=2)
        assert restored == quality


class TestPrecisionErrors:
    """Test error handling for precision violations."""

    def test_too_many_decimal_places_for_scale(self):
        """Reject values with more decimal places than scale allows."""
        # Price 123.45678 has 5 decimal places but scale=4 allows only 4
        with pytest.raises(ValueError, match="more than 4 decimal places"):
            to_firestore_int(Decimal("123.45678"), scale=4)

    def test_none_value_to_firestore(self):
        """Reject None values going to Firestore."""
        with pytest.raises(ValueError, match="Cannot convert None"):
            to_firestore_int(None, scale=4)

    def test_none_value_from_firestore(self):
        """Reject None values coming from Firestore."""
        with pytest.raises(ValueError, match="Cannot convert None"):
            from_firestore_int(None, scale=4)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_trailing_zeros_preserved(self):
        """Trailing zeros are semantically preserved through round-trip."""
        # Decimal("10.00") and Decimal("10.0") are different Decimals,
        # but after round-trip through int they should be equal in value
        original = Decimal("10.00")
        converted = to_firestore_int(original, scale=2)
        restored = from_firestore_int(converted, scale=2)
        assert restored == original

    def test_very_small_positive_value(self):
        """Handle very small positive values."""
        price = Decimal("0.0001")
        converted = to_firestore_int(price, scale=4)
        assert converted == 1
        restored = from_firestore_int(converted, scale=4)
        assert restored == price

    def test_very_small_negative_value(self):
        """Handle very small negative values."""
        price = Decimal("-0.0001")
        converted = to_firestore_int(price, scale=4)
        assert converted == -1
        restored = from_firestore_int(converted, scale=4)
        assert restored == price
