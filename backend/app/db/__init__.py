"""Database models and helpers."""

from datetime import UTC, datetime, timezone


def now_utc() -> datetime:
    """Return current time in UTC as timezone-aware datetime."""
    return datetime.now(UTC)
