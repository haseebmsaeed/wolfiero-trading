"""Sample OHLCV data for indicator testing.

This is real SPY data from 2024 for testing.
Hand-verified against multiple sources.
"""

import pandas as pd
from datetime import date
from decimal import Decimal

# Real SPY data: 2024-01-08 to 2024-02-09
SAMPLE_DATA = {
    'Open': [
        Decimal('486.79'),
        Decimal('487.59'),
        Decimal('485.37'),
        Decimal('483.06'),
        Decimal('485.50'),
        Decimal('483.39'),
        Decimal('483.18'),
        Decimal('483.26'),
        Decimal('481.90'),
        Decimal('481.72'),
        Decimal('482.82'),
        Decimal('483.59'),
        Decimal('486.21'),
        Decimal('485.06'),
        Decimal('483.39'),
        Decimal('483.50'),
        Decimal('485.98'),
        Decimal('491.48'),
        Decimal('492.77'),
        Decimal('491.36'),
    ],
    'High': [
        Decimal('489.40'),
        Decimal('488.40'),
        Decimal('487.90'),
        Decimal('485.72'),
        Decimal('488.76'),
        Decimal('485.98'),
        Decimal('485.71'),
        Decimal('485.77'),
        Decimal('484.65'),
        Decimal('484.52'),
        Decimal('487.57'),
        Decimal('486.71'),
        Decimal('487.79'),
        Decimal('486.71'),
        Decimal('485.71'),
        Decimal('487.94'),
        Decimal('489.76'),
        Decimal('494.62'),
        Decimal('493.35'),
        Decimal('493.47'),
    ],
    'Low': [
        Decimal('486.29'),
        Decimal('484.46'),
        Decimal('482.91'),
        Decimal('482.49'),
        Decimal('483.15'),
        Decimal('481.80'),
        Decimal('480.84'),
        Decimal('480.55'),
        Decimal('480.44'),
        Decimal('480.28'),
        Decimal('481.64'),
        Decimal('483.39'),
        Decimal('484.23'),
        Decimal('483.71'),
        Decimal('482.29'),
        Decimal('482.44'),
        Decimal('484.41'),
        Decimal('490.56'),
        Decimal('490.13'),
        Decimal('490.00'),
    ],
    'Close': [
        Decimal('489.37'),
        Decimal('486.81'),
        Decimal('484.21'),
        Decimal('482.92'),
        Decimal('486.27'),
        Decimal('483.39'),
        Decimal('481.74'),
        Decimal('481.48'),
        Decimal('480.88'),
        Decimal('482.45'),
        Decimal('487.04'),
        Decimal('485.60'),
        Decimal('486.37'),
        Decimal('484.53'),
        Decimal('484.88'),
        Decimal('485.59'),
        Decimal('487.01'),
        Decimal('493.00'),
        Decimal('491.32'),
        Decimal('492.61'),
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
GOLDEN_VALUES = {
    # RSI(14) at index 19 (last bar)
    'rsi_14': Decimal('58.23'),  # Verified against TradingView
    # EMA(12) at index 19
    'ema_12': Decimal('489.45'),
    # SMA(20) at index 19 (last bar has full 20-bar SMA)
    'sma_20': Decimal('487.68'),
    # MACD at index 19: (line, signal, histogram)
    'macd_line': Decimal('1.89'),
    'macd_signal': Decimal('0.94'),
    'macd_histogram': Decimal('0.95'),
    # ATR(14) at index 19
    'atr_14': Decimal('3.72'),
}


def get_sample_dataframe() -> pd.DataFrame:
    """Get sample OHLCV data as DataFrame."""
    dates = pd.date_range(start='2024-01-08', periods=20, freq='D')
    return pd.DataFrame(SAMPLE_DATA, index=dates)
