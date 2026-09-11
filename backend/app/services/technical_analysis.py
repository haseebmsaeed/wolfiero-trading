"""Technical analysis service — turn indicators into trading signals."""

from datetime import date
from decimal import Decimal

import pandas as pd

from app.schemas.technical import (
    MACDState,
    MomentumMetrics,
    RelativeStrengthMetrics,
    ResistanceLevel,
    RSIMetrics,
    SupportLevel,
    TechnicalSnapshot,
    TrendMetrics,
    VolatilityMetrics,
    VolumeMetrics,
)
from app.services import indicators


class TechnicalAnalysisService:
    """Service for technical analysis of a symbol."""

    def __init__(self, symbol: str, bars_df: pd.DataFrame):
        """Initialize with symbol and historical bars.

        Args:
            symbol: e.g. 'NVDA'
            bars_df: DataFrame with OHLCV (indexed by date)
        """
        self.symbol = symbol
        self.bars = bars_df
        self.close = bars_df["Close"]
        self.high = bars_df["High"]
        self.low = bars_df["Low"]
        self.volume = bars_df["Volume"]

    async def analyze(self) -> TechnicalSnapshot:
        """Perform full technical analysis.

        Returns:
            TechnicalSnapshot with all indicators and classifications
        """
        if len(self.bars) < 50:
            raise ValueError(f"{self.symbol}: insufficient history ({len(self.bars)} bars)")

        # Compute all indicators
        trend = self._analyze_trend()
        momentum = self._analyze_momentum()
        volatility = self._analyze_volatility()
        volume_metrics = self._analyze_volume()
        rs_metrics = self._analyze_relative_strength()
        support, resistance = self._find_support_resistance()

        # Get 52-week stats
        year_ago_idx = max(0, len(self.bars) - 252)
        week_52_high = self.high.iloc[year_ago_idx:].max()
        week_52_low = self.low.iloc[year_ago_idx:].min()
        pct_from_high = (self.close.iloc[-1] / week_52_high - 1) * 100

        snapshot = TechnicalSnapshot(
            symbol=self.symbol,
            as_of_date=str(self.bars.index[-1].date()),
            close=Decimal(str(self.close.iloc[-1])),
            trend=trend,
            momentum=momentum,
            volatility=volatility,
            volume=volume_metrics,
            relative_strength=rs_metrics,
            support=support,
            resistance=resistance,
            week_52_high=Decimal(str(week_52_high)),
            week_52_low=Decimal(str(week_52_low)),
            pct_from_52w_high=Decimal(str(pct_from_high)),
            bars_available=len(self.bars),
            last_bar_date=str(self.bars.index[-1].date()),
            gaps_detected=0,  # TODO: Detect gaps
        )

        return snapshot

    def _analyze_trend(self) -> TrendMetrics:
        """Classify trend: uptrend, downtrend, or range."""
        sma_20 = indicators.sma(self.close, 20)
        sma_50 = indicators.sma(self.close, 50)
        sma_200 = indicators.sma(self.close, 200)
        ema_20 = indicators.ema(self.close, 20)

        close_now = self.close.iloc[-1]
        sma_50_now = sma_50.iloc[-1]
        sma_200_now = sma_200.iloc[-1]
        ema_20_now = ema_20.iloc[-1]

        # Trend determination
        above_200 = close_now > sma_200_now
        above_50 = close_now > sma_50_now
        above_20 = close_now > ema_20_now
        stack_aligned = sma_50_now > sma_200_now

        if above_200 and above_50 and stack_aligned:
            direction = "UPTREND"
            # Strength based on distance from MA and slope
            pct_above_50 = (close_now / sma_50_now - 1) * 100
            strength = min(Decimal("1.0"), Decimal(str(pct_above_50 / 5)))  # 5% = full strength
        elif close_now < sma_200_now and not above_50 and not stack_aligned:
            direction = "DOWNTREND"
            pct_below_50 = (sma_50_now / close_now - 1) * 100
            strength = min(Decimal("1.0"), Decimal(str(pct_below_50 / 5)))
        else:
            direction = "RANGE"
            strength = Decimal("0.5")

        # 50-SMA slope
        sma_50_20d_ago = sma_50.iloc[-20]
        slope_50 = (sma_50_now / sma_50_20d_ago - 1) * 100 if sma_50_20d_ago > 0 else 0

        return TrendMetrics(
            direction=direction,
            strength=strength,
            above_20_ema=above_20,
            above_50_sma=above_50,
            above_200_sma=above_200,
            ma_stack_aligned=stack_aligned,
            slope_50_sma_20d_pct=Decimal(str(slope_50)),
        )

    def _analyze_momentum(self) -> MomentumMetrics:
        """Analyze momentum indicators."""
        rsi = indicators.rsi(self.close, 14)
        rsi_val = float(rsi.iloc[-1])

        if rsi_val < 30:
            rsi_state = "OVERSOLD"
        elif rsi_val > 70:
            rsi_state = "OVERBOUGHT"
        else:
            rsi_state = "NEUTRAL"

        # MACD
        macd_line, signal_line, histogram = indicators.macd(self.close)
        macd_val = float(macd_line.iloc[-1])
        signal_val = float(signal_line.iloc[-1])
        hist_val = float(histogram.iloc[-1])

        if macd_val > 0 and hist_val > 0:
            macd_state = "BULLISH_ABOVE_ZERO"
        elif macd_val > 0 and hist_val < 0:
            macd_state = "BULLISH_BELOW_ZERO"
        elif macd_val < 0 and hist_val > 0:
            macd_state = "BEARISH_ABOVE_ZERO"
        else:
            macd_state = "BEARISH_BELOW_ZERO"

        # ROC
        roc = indicators.roc(self.close, 20)
        roc_val = float(roc.iloc[-1])

        return MomentumMetrics(
            rsi_14=RSIMetrics(value=Decimal(str(rsi_val)), state=rsi_state),
            macd=MACDState(
                line=Decimal(str(macd_val)),
                signal=Decimal(str(signal_val)),
                histogram=Decimal(str(hist_val)),
                state=macd_state,
            ),
            roc_20d_pct=Decimal(str(roc_val)),
        )

    def _analyze_volatility(self) -> VolatilityMetrics:
        """Analyze volatility indicators."""
        atr = indicators.atr(self.high, self.low, self.close, 14)
        atr_val = float(atr.iloc[-1])
        close_val = float(self.close.iloc[-1])
        atr_pct = (atr_val / close_val * 100) if close_val > 0 else 0

        # Volatility regime
        atr_50d_avg = atr.iloc[-50:].mean()
        if atr_val > atr_50d_avg * 1.2:
            vol_regime = "HIGH"
        elif atr_val < atr_50d_avg * 0.8:
            vol_regime = "LOW"
        else:
            vol_regime = "NORMAL"

        # Realized vol
        real_vol = indicators.realized_volatility(self.close, 20, annualized=True)
        real_vol_val = float(real_vol.iloc[-1]) * 100

        # Bollinger width percentile
        bb_percentile = indicators.bollinger_width_percentile(self.close, lookback=50)
        bb_pct = float(bb_percentile.iloc[-1]) if not pd.isna(bb_percentile.iloc[-1]) else 50

        return VolatilityMetrics(
            atr_14=Decimal(str(atr_val)),
            atr_pct_of_price=Decimal(str(atr_pct)),
            realized_vol_20d_pct=Decimal(str(real_vol_val)),
            volatility_regime=vol_regime,
            bollinger_width_percentile=Decimal(str(bb_pct)),
        )

    def _analyze_volume(self) -> VolumeMetrics:
        """Analyze volume."""
        avg_volume = self.volume.iloc[-20:].mean()
        ratio = self.volume.iloc[-1] / avg_volume

        # Dollar volume
        dollar_vol_avg = (self.close.iloc[-20:] * self.volume.iloc[-20:]).mean()

        # Trend
        if ratio > 1.2:
            vol_trend = "INCREASING"
        elif ratio < 0.8:
            vol_trend = "DECREASING"
        else:
            vol_trend = "STABLE"

        return VolumeMetrics(
            avg_20d=int(avg_volume),
            ratio_vs_avg=Decimal(str(ratio)),
            dollar_volume_20d=Decimal(str(dollar_vol_avg)),
            trend=vol_trend,
        )

    def _analyze_relative_strength(self) -> RelativeStrengthMetrics:
        """Analyze relative strength vs SPY (placeholder)."""
        # Note: This requires SPY data which isn't available in the DataFrame
        # In real implementation, we'd compute against SPY bars from the database
        return RelativeStrengthMetrics(
            vs_spy_1m=Decimal("0"),
            vs_spy_3m=Decimal("0"),
            vs_spy_6m=Decimal("0"),
            percentile_rank=50,
            vs_sector_3m=Decimal("0"),
        )

    def _find_support_resistance(self) -> tuple[list[SupportLevel], list[ResistanceLevel]]:
        """Find support and resistance levels."""
        # Use swings + moving averages
        pivots_high, pivots_low = indicators.swing_pivots(self.high, self.low, lookback=5)

        support = []
        for date_val, price in pivots_low:
            support.append(
                SupportLevel(
                    price=Decimal(str(price)),
                    strength=Decimal("0.8"),
                    type="SWING_LOW",
                )
            )

        resistance = []
        for date_val, price in pivots_high:
            resistance.append(
                ResistanceLevel(
                    price=Decimal(str(price)),
                    strength=Decimal("0.8"),
                    type="SWING_HIGH",
                )
            )

        # Add moving average support
        sma_50 = indicators.sma(self.close, 50)
        if not pd.isna(sma_50.iloc[-1]):
            support.append(
                SupportLevel(
                    price=Decimal(str(sma_50.iloc[-1])),
                    strength=Decimal("0.6"),
                    type="MA_50",
                )
            )

        # Sort
        support.sort(key=lambda x: x.price, reverse=True)
        resistance.sort(key=lambda x: x.price)

        return support, resistance
