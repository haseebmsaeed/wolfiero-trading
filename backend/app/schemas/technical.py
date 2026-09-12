"""Pydantic schemas for technical analysis output."""

from decimal import Decimal

from pydantic import BaseModel, Field


class SupportLevel(BaseModel):
    """A support level (price + strength)."""

    price: Decimal
    strength: Decimal = Field(ge=0, le=1)  # 0-1 confidence
    touches: int = 0  # Number of times price has tested
    type: str  # SWING_LOW, MA_50, MA_200, PIVOT, etc.


class ResistanceLevel(BaseModel):
    """A resistance level (price + strength)."""

    price: Decimal
    strength: Decimal = Field(ge=0, le=1)
    touches: int = 0
    type: str


class MACDState(BaseModel):
    """MACD classification."""

    line: Decimal
    signal: Decimal
    histogram: Decimal
    state: str  # BULLISH_ABOVE_ZERO, BULLISH_BELOW_ZERO, BEARISH_ABOVE_ZERO, BEARISH_BELOW_ZERO


class RSIMetrics(BaseModel):
    """RSI and overbought/oversold state."""

    value: Decimal = Field(ge=0, le=100)
    state: str  # OVERSOLD (<30), NEUTRAL (30-70), OVERBOUGHT (>70)


class TrendMetrics(BaseModel):
    """Trend classification and strength."""

    direction: str  # UPTREND, DOWNTREND, RANGE
    strength: Decimal = Field(ge=0, le=1)  # 0-1 confidence
    above_20_ema: bool
    above_50_sma: bool
    above_200_sma: bool
    ma_stack_aligned: bool  # 50-SMA > 200-SMA for uptrend
    slope_50_sma_20d_pct: Decimal  # How steep the 50-day SMA


class MomentumMetrics(BaseModel):
    """Momentum indicators."""

    rsi_14: RSIMetrics
    macd: MACDState
    roc_20d_pct: Decimal  # Rate of change over 20 days


class VolatilityMetrics(BaseModel):
    """Volatility and volume."""

    atr_14: Decimal
    atr_pct_of_price: Decimal  # ATR as % of close
    realized_vol_20d_pct: Decimal  # Annualized
    volatility_regime: str  # LOW, NORMAL, HIGH (vs. 50-day average)
    bollinger_width_percentile: Decimal = Field(ge=0, le=100)  # 0-100


class VolumeMetrics(BaseModel):
    """Volume analysis."""

    avg_20d: int
    ratio_vs_avg: Decimal  # Today / 20-day average
    dollar_volume_20d: Decimal  # 20-day avg in dollars
    trend: str  # INCREASING, DECREASING, STABLE


class RelativeStrengthMetrics(BaseModel):
    """Strength relative to market and sector."""

    vs_spy_1m: Decimal  # Return vs SPY last month (%)
    vs_spy_3m: Decimal
    vs_spy_6m: Decimal
    percentile_rank: int = Field(ge=0, le=100)  # vs. full universe
    vs_sector_3m: Decimal


class TechnicalSnapshot(BaseModel):
    """Complete technical analysis of a symbol at a point in time.

    Immutable snapshot — never updated after creation.
    Includes everything needed for setup detection and scoring.
    """

    symbol: str
    as_of_date: str  # ISO date string (market session date)
    close: Decimal

    # Classifications
    trend: TrendMetrics
    momentum: MomentumMetrics
    volatility: VolatilityMetrics
    volume: VolumeMetrics
    relative_strength: RelativeStrengthMetrics

    # Price levels
    support: list[SupportLevel] = []
    resistance: list[ResistanceLevel] = []
    week_52_high: Decimal
    week_52_low: Decimal
    pct_from_52w_high: Decimal

    # Data quality
    bars_available: int
    last_bar_date: str
    gaps_detected: int

    class Config:
        json_encoders = {Decimal: float}  # noqa: RUF012
