"""Setup detection — identify chart patterns with graded quality."""

from decimal import Decimal

from app.schemas.technical import TechnicalSnapshot


class SetupResult:
    """Result of setup detection."""

    def __init__(
        self,
        setup_type: str,
        quality: Decimal,
        direction: str,
        description: str,
        triggered: bool = False,
        trigger_condition: str = "",
    ):
        """Initialize setup result."""
        self.setup_type = setup_type
        self.quality = quality  # 0-1
        self.direction = direction
        self.description = description
        self.triggered = triggered
        self.trigger_condition = trigger_condition

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.setup_type,
            "quality": float(self.quality),
            "direction": self.direction,
            "description": self.description,
            "triggered": self.triggered,
            "trigger_condition": self.trigger_condition,
        }


def detect_best_setup(snapshot: TechnicalSnapshot) -> SetupResult:
    """Detect the best setup, or NONE if none qualify.

    Simplified version for v1 — just checks trend.
    In full implementation, would use setups.py with graded detectors.

    Args:
        snapshot: Technical snapshot

    Returns:
        SetupResult with best setup or NONE
    """
    if snapshot.trend.direction == "UPTREND":
        quality = Decimal(str(snapshot.trend.strength))

        description = (
            f"Uptrend intact: close > 50-SMA ({snapshot.trend.above_50_sma}), "
            f"50-SMA slope +{snapshot.trend.slope_50_sma_20d_pct}%"
        )

        return SetupResult(
            setup_type="UPTREND",
            quality=quality,
            direction="LONG",
            description=description,
            triggered=False,
            trigger_condition="Close above recent swing high",
        )

    elif snapshot.trend.direction == "DOWNTREND":
        quality = Decimal(str(snapshot.trend.strength))

        description = "Downtrend intact: close < 50-SMA, MA stack inverted"

        return SetupResult(
            setup_type="DOWNTREND",
            quality=quality,
            direction="SHORT",
            description=description,
            triggered=False,
            trigger_condition="Close below recent swing low",
        )

    else:
        return SetupResult(
            setup_type="NONE",
            quality=Decimal(0),
            direction="FLAT",
            description="No clear setup detected",
            triggered=False,
            trigger_condition="",
        )
