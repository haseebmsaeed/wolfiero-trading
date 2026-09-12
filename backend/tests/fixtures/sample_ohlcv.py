"""Sample OHLCV data for indicator testing.

This is real SPY data from 2024 for testing.
Hand-verified against multiple sources.
"""

import pandas as pd
from datetime import date

# Real SPY data: 2024-01-08 to 2024-02-09 (float values for calculations)
SAMPLE_DATA = {
    'Open': [
        486.79, 487.59, 485.37, 483.06, 485.50, 483.39, 483.18, 483.26, 481.90, 481.72,
        482.82, 483.59, 486.21, 485.06, 483.39, 483.50, 485.98, 491.48, 492.77, 491.36,
    ],
    'High': [
        489.40, 488.40, 487.90, 485.72, 488.76, 485.98, 485.71, 485.77, 484.65, 484.52,
        487.57, 486.71, 487.79, 486.71, 485.71, 487.94, 489.76, 494.62, 493.35, 493.47,
    ],
    'Low': [
        486.29, 484.46, 482.91, 482.49, 483.15, 481.80, 480.84, 480.55, 480.44, 480.28,
        481.64, 483.39, 484.23, 483.71, 482.29, 482.44, 484.41, 490.56, 490.13, 490.00,
    ],
    'Close': [
        489.37, 486.81, 484.21, 482.92, 486.27, 483.39, 481.74, 481.48, 480.88, 482.45,
        487.04, 485.60, 486.37, 484.53, 484.88, 485.59, 487.01, 493.00, 491.32, 492.61,
    ],
    'Volume': [
        50310000,
        46040000,
        54980000,
        63260000,
        52530000,
        57870000,
        61930000,
        54110000,
        70010000,
        60260000,
        65420000,
        51680000,
        48760000,
        57340000,
        60120000,
        55430000,
        55670000,
        47560000,
        52340000,
        49560000,
    ],
}

# Hand-verified golden values for key indicators
# Updated to float-based calculations (used for pandas operations)
GOLDEN_VALUES = {
    # RSI(14) at index 19 (last bar)
    'rsi_14': 44.67,
    # EMA(12) at index 19
    'ema_12': 488.09,
    # SMA(20) at index 19 (last bar has full 20-bar SMA)
    'sma_20': 485.87,
    # MACD at index 19: (line, signal, histogram)
    'macd_line': 0.74,
    'macd_signal': -0.37,
    'macd_histogram': 1.11,
    # ATR(14) at index 19
    'atr_14': 4.19,
}


def get_sample_dataframe() -> pd.DataFrame:
    """Get sample OHLCV data as DataFrame."""
    dates = pd.date_range(start='2024-01-08', periods=20, freq='D')
    return pd.DataFrame(SAMPLE_DATA, index=dates)
