"""Technical indicator calculations — pure functions for OHLCV analysis.

All functions:
- Take pandas Series/DataFrame as input
- Return series with same index
- Return NaN for warm-up period (not padded)
- Are fully deterministic and testable
"""


import numpy as np
import pandas as pd

# Moving Averages

def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average.

    Args:
        series: Price series
        period: Window in bars

    Returns:
        SMA series (NaN for first period-1 bars)
    """
    return series.rolling(window=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average.

    Args:
        series: Price series
        period: Window in bars

    Returns:
        EMA series (NaN until enough bars)
    """
    return series.ewm(span=period, adjust=False).mean()


# Momentum Indicators

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing.

    Args:
        series: Price series (typically Close)
        period: Window (default 14)

    Returns:
        RSI series [0, 100] (NaN for first period+1 bars)
    """
    # Calculate changes
    delta = series.diff()

    # Separate gains and losses
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    # Wilder's smoothing (1/period alpha)
    avg_gain = gains.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1/period, adjust=False).mean()

    # RS and RSI
    rs = avg_gain / avg_loss
    rsi_values = 100 - (100 / (1 + rs))

    return rsi_values


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MACD (Moving Average Convergence Divergence).

    Args:
        series: Price series (typically Close)
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line EMA period (default 9)

    Returns:
        Tuple of (macd_line, signal_line, histogram)
        All are NaN for warm-up period
    """
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)

    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Average True Range using Wilder's smoothing.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Window (default 14)

    Returns:
        ATR series (NaN for first period bars)
    """
    # True Range
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder's smoothing
    atr_values = tr.ewm(alpha=1/period, adjust=False).mean()

    return atr_values


def bollinger_bands(
    series: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands.

    Args:
        series: Price series (typically Close)
        period: SMA window (default 20)
        num_std: Number of standard deviations (default 2)

    Returns:
        Tuple of (upper, middle, lower)
    """
    middle = sma(series, period)
    std = series.rolling(window=period).std()

    upper = middle + (num_std * std)
    lower = middle - (num_std * std)

    return upper, middle, lower


def bollinger_width_percentile(
    series: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
    lookback: int = 100,
) -> pd.Series:
    """Bollinger Band width as percentile of lookback range.

    Used to detect compression (low percentile) vs expansion (high percentile).

    Args:
        series: Price series
        period: BB period (default 20)
        num_std: BB std dev (default 2)
        lookback: Percentile lookback in bars (default 100)

    Returns:
        Percentile [0, 100] (NaN for warm-up)
    """
    upper, _, lower = bollinger_bands(series, period, num_std)
    width = upper - lower

    # Rolling min/max of width
    width_min = width.rolling(window=lookback).min()
    width_max = width.rolling(window=lookback).max()

    # Percentile
    percentile = 100 * (width - width_min) / (width_max - width_min + 1e-10)

    return percentile


# Volatility

def realized_volatility(
    close: pd.Series,
    period: int = 20,
    annualized: bool = True,
) -> pd.Series:
    """Realised volatility from log returns.

    Args:
        close: Close prices
        period: Window in bars (default 20)
        annualized: Annualise by sqrt(252) (default True)

    Returns:
        Volatility series as decimal [0, 1] (NaN for first bars)
    """
    # Log returns
    log_returns = np.log(close / close.shift())

    # Standard deviation
    vol = log_returns.rolling(window=period).std()

    if annualized:
        vol = vol * np.sqrt(252)

    return vol


# Rate of Change

def roc(series: pd.Series, period: int = 20) -> pd.Series:
    """Rate of Change: (close - close[period]) / close[period] * 100.

    Args:
        series: Price series
        period: Lookback in bars (default 20)

    Returns:
        ROC series as % (NaN for first period bars)
    """
    return 100 * (series - series.shift(period)) / series.shift(period)


# Volume

def volume_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
    """Volume ratio: today's volume / average volume.

    Args:
        volume: Volume series
        period: Average window (default 20)

    Returns:
        Ratio (NaN for first period bars)
    """
    avg_volume = volume.rolling(window=period).mean()
    return volume / avg_volume


# Relative Strength

def relative_strength(
    symbol_returns: pd.Series,
    benchmark_returns: pd.Series,
    period: int = 63,  # ~3 months
) -> pd.Series:
    """Relative strength: symbol / benchmark ratio.

    Args:
        symbol_returns: Symbol returns series
        benchmark_returns: Benchmark returns series
        period: Lookback in bars (default 63 = ~3 months)

    Returns:
        RS ratio (NaN for warm-up)
    """
    cumulative_symbol = (1 + symbol_returns).rolling(window=period).prod()
    cumulative_benchmark = (1 + benchmark_returns).rolling(window=period).prod()

    return cumulative_symbol / cumulative_benchmark


def rs_percentile(values: pd.Series, lookback: int = 252) -> pd.Series:
    """Percentile rank of a value in a lookback window.

    Used for relative strength percentile (0-100).

    Args:
        values: Series of values
        lookback: Window in bars (default 252 = 1 year)

    Returns:
        Percentile [0, 100] (NaN for warm-up)
    """
    def percentile_rank(x):
        if len(x) == 0 or x.isna().all():
            return np.nan
        return (x.iloc[-1] >= x).sum() / len(x) * 100

    return values.rolling(window=lookback).apply(percentile_rank, raw=False)


# Support/Resistance

def swing_pivots(
    high: pd.Series,
    low: pd.Series,
    lookback: int = 5,
) -> tuple[list[tuple], list[tuple]]:
    """Identify swing highs and lows.

    Args:
        high: High prices
        low: Low prices
        lookback: Bars to left and right (default 5)

    Returns:
        Tuple of (pivot_highs, pivot_lows)
        Each is list of (date, price)
    """
    pivot_highs = []
    pivot_lows = []

    for i in range(lookback, len(high) - lookback):
        # Check swing high
        if high.iloc[i] == high.iloc[i - lookback : i + lookback + 1].max():
            pivot_highs.append((high.index[i], high.iloc[i]))

        # Check swing low
        if low.iloc[i] == low.iloc[i - lookback : i + lookback + 1].min():
            pivot_lows.append((low.index[i], low.iloc[i]))

    return pivot_highs, pivot_lows
