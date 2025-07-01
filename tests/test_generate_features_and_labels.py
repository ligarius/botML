import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import numpy as np

import orchestrator


def make_df(n=60):
    base = np.linspace(1, 1.6, n)
    return pd.DataFrame({
        "open_time": pd.date_range("2024-01-01", periods=n, freq="min"),
        "open": base,
        "high": base + 0.01,
        "low": base - 0.01,
        "close": base,
        "volume": np.linspace(100, 200, n),
    })


def test_generate_features_and_labels_custom_config():
    df = make_df()
    cfg = {"label_horizon": 1, "label_threshold": 0.005}
    labeled = orchestrator.generate_features_and_labels(cfg, df)
    assert labeled["label"].sum() > 0

    cfg_far = {"label_horizon": 5, "label_threshold": 0.1}
    labeled_far = orchestrator.generate_features_and_labels(cfg_far, make_df())
    assert labeled["label"].sum() > labeled_far["label"].sum()
