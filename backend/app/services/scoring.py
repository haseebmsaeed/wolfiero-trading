"""Composite scoring engine for ranking candidates."""

from decimal import Decimal
from typing import NamedTuple

from app.logging import get_logger

logger = get_logger(__name__)


class ComponentScore(NamedTuple):
    """A single component score."""

    raw: Decimal
    normalized: Decimal
    weight: Decimal
    contribution: Decimal


class ScoreBreakdown(NamedTuple):
    """Complete score breakdown."""

    technical_score: ComponentScore
    momentum_score: ComponentScore
    relative_strength_score: ComponentScore
    volume_score: ComponentScore
    regime_fit_score: ComponentScore
    catalyst_score: ComponentScore
    reward_risk_score: ComponentScore
    total_score: Decimal


class ScoringService:
    """Composite scoring engine implementing the spec formula."""

    # Component weights
    WEIGHTS = {
        "technical": Decimal("0.25"),
        "momentum": Decimal("0.15"),
        "relative_strength": Decimal("0.15"),
        "volume": Decimal("0.10"),
        "regime_fit": Decimal("0.10"),
        "catalyst": Decimal("0.10"),
        "reward_risk": Decimal("0.15"),
    }

    def score_candidate(
        self,
        setup_quality: Decimal,
        ma_stack_score: Decimal,
        distance_from_support: Decimal,
        rsi_score: Decimal,
        macd_state_score: Decimal,
        roc_score: Decimal,
        rs_percentile: Decimal,
        volume_ratio: Decimal,
        regime_fit: Decimal = Decimal("0.50"),
        catalyst_score: Decimal = Decimal("0.50"),
        reward_risk: Decimal = Decimal("2.00"),
    ) -> ScoreBreakdown:
        """Score a candidate using the composite formula.

        All inputs should be 0–1 or appropriately normalized.
        Missing values default to 0.5 (neutral).

        Returns:
            ScoreBreakdown with all component scores
        """
        # Technical score: setup (0.5) + MA stack (0.2) + distance from support (0.3)
        technical = (
            setup_quality * Decimal("0.50")
            + ma_stack_score * Decimal("0.20")
            + distance_from_support * Decimal("0.30")
        )

        # Momentum score: RSI (0.4, band-scored) + MACD (0.3) + ROC (0.3)
        momentum = (
            rsi_score * Decimal("0.40")
            + macd_state_score * Decimal("0.30")
            + roc_score * Decimal("0.30")
        )

        # Relative strength: percentile/100
        rs_score = min(rs_percentile / Decimal("100"), Decimal("1.00"))

        # Volume score: ratio vs 20-day avg, clipped at 3.0x then scaled
        volume = min(volume_ratio / Decimal("3.00"), Decimal("1.00"))

        # Reward/risk score: min(rr/4.0, 1.0)
        rr_score = min(reward_risk / Decimal("4.00"), Decimal("1.00"))

        # Compute total
        total = (
            technical * self.WEIGHTS["technical"]
            + momentum * self.WEIGHTS["momentum"]
            + rs_score * self.WEIGHTS["relative_strength"]
            + volume * self.WEIGHTS["volume"]
            + regime_fit * self.WEIGHTS["regime_fit"]
            + catalyst_score * self.WEIGHTS["catalyst"]
            + rr_score * self.WEIGHTS["reward_risk"]
        )

        # Scale to 0–100
        final_score = total * Decimal("100")

        # Build breakdown
        breakdown = ScoreBreakdown(
            technical_score=ComponentScore(
                raw=technical,
                normalized=technical,
                weight=self.WEIGHTS["technical"],
                contribution=technical * self.WEIGHTS["technical"],
            ),
            momentum_score=ComponentScore(
                raw=momentum,
                normalized=momentum,
                weight=self.WEIGHTS["momentum"],
                contribution=momentum * self.WEIGHTS["momentum"],
            ),
            relative_strength_score=ComponentScore(
                raw=rs_percentile,
                normalized=rs_score,
                weight=self.WEIGHTS["relative_strength"],
                contribution=rs_score * self.WEIGHTS["relative_strength"],
            ),
            volume_score=ComponentScore(
                raw=volume_ratio,
                normalized=volume,
                weight=self.WEIGHTS["volume"],
                contribution=volume * self.WEIGHTS["volume"],
            ),
            regime_fit_score=ComponentScore(
                raw=regime_fit,
                normalized=regime_fit,
                weight=self.WEIGHTS["regime_fit"],
                contribution=regime_fit * self.WEIGHTS["regime_fit"],
            ),
            catalyst_score=ComponentScore(
                raw=catalyst_score,
                normalized=catalyst_score,
                weight=self.WEIGHTS["catalyst"],
                contribution=catalyst_score * self.WEIGHTS["catalyst"],
            ),
            reward_risk_score=ComponentScore(
                raw=reward_risk,
                normalized=rr_score,
                weight=self.WEIGHTS["reward_risk"],
                contribution=rr_score * self.WEIGHTS["reward_risk"],
            ),
            total_score=final_score,
        )

        return breakdown
