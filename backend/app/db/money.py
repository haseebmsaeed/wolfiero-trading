"""Decimal precision helpers for Firestore storage.

Firestore has no native Decimal type. We store money/scores as scaled integers:
- Prices (4 decimal places): multiply by 10,000 → store/retrieve as integer
- Scores/quality (2 decimal places): multiply by 100 → store/retrieve as integer
- All conversion happens through Decimal arithmetic (never float) to preserve precision.

This module is the single point of contact for the Decimal ↔ integer conversion,
ensuring correctness throughout the codebase per CLAUDE.md rule: "Money is Decimal, never float."
"""

from decimal import ROUND_HALF_UP, Decimal


def to_firestore_int(value: Decimal, scale: int) -> int:
    """Convert a Decimal to a scaled integer for Firestore storage.

    Args:
        value: Decimal value to convert
        scale: Number of decimal places (e.g., 4 for prices, 2 for scores)

    Returns:
        Scaled integer (e.g., $123.4567 with scale=4 → 1234567)

    Raises:
        ValueError: If value has more decimal places than scale allows
    """
    if value is None:
        raise ValueError("Cannot convert None to Firestore int")

    # Verify the value doesn't have more precision than scale allows
    scaled = value * Decimal(10 ** scale)
    if scaled % 1 != 0:
        raise ValueError(
            f"Value {value} has more than {scale} decimal places; "
            f"cannot store in Firestore at scale {scale}"
        )

    return int(scaled.to_integral_value(rounding=ROUND_HALF_UP))


def from_firestore_int(value: int, scale: int) -> Decimal:
    """Convert a scaled integer from Firestore back to a Decimal.

    Args:
        value: Scaled integer from Firestore
        scale: Number of decimal places (must match what was used in to_firestore_int)

    Returns:
        Decimal value (e.g., 1234567 with scale=4 → $123.4567)
    """
    if value is None:
        raise ValueError("Cannot convert None from Firestore int")

    return Decimal(value) / Decimal(10 ** scale)
