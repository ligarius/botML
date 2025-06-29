import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import numpy as np
from botml.features import add_features


def sample_df(n=50):
    base = np.arange(n, dtype=float) + 100
    data = {
        "open_time": pd.date_range("2024-01-01", periods=n, freq="T"),
        "open": base,
        "high": base + 1,
        "low": base - 1,
        "close": base + np.sin(np.arange(n)),
        "volume": np.linspace(1000, 1010, n),
    }
    return pd.DataFrame(data)


def test_add_features_columns():
    df = sample_df(50)
    fe = add_features(df)
    expected = [
        'return_1m', 'return_5m', 'return_10m',
        'SMA_5', 'SMA_10', 'SMA_20',
        'EMA_5', 'EMA_10', 'EMA_20',
        'STD_10', 'STD_20', 'RSI_14',
        'ATR_14', 'MACD', 'MACD_signal',
        'volume_zscore_30', 'max_20', 'min_20',
        'bullish_candle', 'bearish_candle'
    ]
    for col in expected:
        assert col in fe.columns
    assert not fe.isna().any().any()
    # max rolling window is 30 -> first 29 rows dropped
    assert len(fe) == 50 - 29
