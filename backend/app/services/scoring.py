"""Composite scoring engine for ranking candidates."""

from decimal import Decimal
from typing import ClassVar, NamedTuple

import pandas as pd

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
    WEIGHTS: ClassVar[dict[str, Decimal]] = {
        "technical": Decimal("0.25"),
        "momentum": Decimal("0.15"),
        "relative_strength": Decimal("0.15"),
        "volume": Decimal("0.10"),
        "regime_fit": Decimal("0.10"),
        "catalyst": Decimal("0.10"),
        "reward_risk": Decimal("0.15"),
    }

    def __init__(self, weights: dict | None = None):
        """Initialize with optional custom weights."""
        if weights:
            self.WEIGHTS = {k: Decimal(str(v)) for k, v in weights.items()}  # type: ignore

    def score_candidate(
        self,
        bars_df: pd.DataFrame,
        setup_type: str,
        setup_quality: Decimal,
        rs_percentile: Decimal,
        regime: str = "RISK_ON",
    ) -> ScoreBreakdown:
        """Score a candidate using the composite formula.

        Args:
            bars_df: OHLCV bars DataFrame
            setup_type: Type of setup (BREAKOUT, PULLBACK, etc.)
            setup_quality: Setup quality 0-1
            rs_percentile: RS percentile 0-100
            regime: Market regime (RISK_ON, NEUTRAL, RISK_OFF)

        Returns:
            ScoreBreakdown with all component scores
        """
        # Technical score: setup + MA stack + distance from support
        ma_stack_score = self._score_ma_stack(bars_df)
        distance_from_support = Decimal("0.5")  # Stub
        technical_raw = (
            setup_quality * Decimal("0.50")
            + ma_stack_score * Decimal("0.20")
            + distance_from_support * Decimal("0.30")
        )
        technical = min(technical_raw, Decimal("1.0"))

        # Momentum score: RSI (band-scored) + MACD + ROC
        rsi_score = self._score_rsi(bars_df)
        macd_state_score = Decimal("0.5")  # Stub
        roc_score = self._score_roc(bars_df)
        momentum_raw = (
            rsi_score * Decimal("0.40")
            + macd_state_score * Decimal("0.30")
            + roc_score * Decimal("0.30")
        )
        momentum = min(momentum_raw, Decimal("1.0"))

        # Relative strength: percentile/100
        rs_score = min(rs_percentile / Decimal("100"), Decimal("1.00"))

        # Volume score: ratio vs 20-day avg, clipped at 3.0x
        volume_ratio = self._get_volume_ratio(bars_df)
        volume = min(volume_ratio / Decimal("3.00"), Decimal("1.00"))

        # Regime fit: lookup table
        regime_fit = self._get_regime_fit(setup_type, regime)

        # Catalyst: stub (0.5 neutral)
        catalyst_score = Decimal("0.50")

        # Reward/risk: stub (0.5 neutral)
        rr_score = Decimal("0.50")

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

        # Scale to 0-100
        final_score = total * Decimal("100")

        # Build breakdown
        breakdown = ScoreBreakdown(
            technical_score=ComponentScore(
                raw=technical_raw,
                normalized=technical,
                weight=self.WEIGHTS["technical"],
                contribution=technical * self.WEIGHTS["technical"],
            ),
            momentum_score=ComponentScore(
                raw=momentum_raw,
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
                raw=rr_score,
                normalized=rr_score,
                weight=self.WEIGHTS["reward_risk"],
                contribution=rr_score * self.WEIGHTS["reward_risk"],
            ),
            total_score=final_score,
        )

        return breakdown

    def _score_ma_stack(self, bars_df: pd.DataFrame) -> Decimal:
        """Score MA alignment: how well price fits the MA stack."""
        close = bars_df["Close"].iloc[-1]
        sma_50 = bars_df["Close"].rolling(50).mean().iloc[-1]
        sma_200 = bars_df["Close"].rolling(200).mean().iloc[-1]

        if close > sma_50 > sma_200:
            return Decimal("1.0")
        elif close > sma_200:
            return Decimal("0.7")
        else:
            return Decimal("0.3")

    def _score_rsi(self, bars_df: pd.DataFrame) -> Decimal:
        """Score RSI as a band (45-70 optimal, not monotonic)."""
        close = bars_df["Close"]
        rsi = self._calculate_rsi(close)

        # Band scoring:
        # RSI < 30: poor (0.3)
        # RSI 30-45: weak (0.5-0.8)
        # RSI 45-70: optimal (0.8-1.0)
        # RSI 70-85: warning (1.0-0.5)
        # RSI > 85: poor (0.2)
        if rsi < 30:
            score = Decimal("0.3")
        elif rsi < 45:
            score = Decimal("0.5") + Decimal(str((rsi - 30) / 30 * 0.3))
        elif rsi <= 70:
            score = Decimal("0.8") + Decimal(str((rsi - 45) / 25 * 0.2))
        elif rsi <= 85:
            score = Decimal("1.0") - Decimal(str((rsi - 70) / 15 * 0.5))
        else:
            score = Decimal("0.2")

        return min(Decimal("1.0"), max(Decimal("0.0"), score))

    def _score_roc(self, bars_df: pd.DataFrame) -> Decimal:
        """Score 20-day rate of change."""
        close = bars_df["Close"]
        if len(close) < 20:
            return Decimal("0.5")

        roc = ((close.iloc[-1] / close.iloc[-20]) - 1) * 100
        # 0-20% ROC is optimal
        score = Decimal(str(max(0.0, min(1.0, (roc / 20.0) * 0.8 + 0.1))))
        return score

    def _get_volume_ratio(self, bars_df: pd.DataFrame) -> Decimal:
        """Get volume ratio vs 20-day average."""
        if len(bars_df) < 20:
            return Decimal("1.0")

        volume = bars_df["Volume"]
        vol_20day = volume.iloc[-20:].mean()
        vol_today = volume.iloc[-1]

        if vol_20day == 0:
            return Decimal("1.0")

        ratio = Decimal(str(vol_today / vol_20day))
        return ratio

    def _get_regime_fit(self, setup_type: str, regime: str) -> Decimal:
        """Look up how well this setup suits the regime."""
        regime_fits = {
            "RISK_ON": {
                "BREAKOUT": Decimal("0.90"),
                "PULLBACK": Decimal("0.95"),
                "CONSOLIDATION": Decimal("0.70"),
                "MOMENTUM": Decimal("0.85"),
            },
            "NEUTRAL": {
                "BREAKOUT": Decimal("0.70"),
                "PULLBACK": Decimal("0.80"),
                "CONSOLIDATION": Decimal("0.80"),
                "MOMENTUM": Decimal("0.60"),
            },
            "RISK_OFF": {
                "BREAKOUT": Decimal("0.40"),
                "PULLBACK": Decimal("0.50"),
                "CONSOLIDATION": Decimal("0.60"),
                "MOMENTUM": Decimal("0.20"),
            },
        }

        return regime_fits.get(regime, {}).get(setup_type, Decimal("0.50"))

    def _calculate_rsi(self, close: pd.Series, period: int = 14) -> float:
        """Calculate RSI."""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] != 0 else 0
        rsi = 100.0 - (100.0 / (1.0 + rs)) if rs > 0 else 0
        return rsi
