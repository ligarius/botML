import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import numpy as np
from botml.features import add_features
from botml.labeling import create_labels


def logistic_train(X, y, lr=0.1, epochs=200):
    w = np.zeros(X.shape[1])
    for _ in range(epochs):
        preds = 1.0 / (1.0 + np.exp(-X.dot(w)))
        gradient = X.T.dot(preds - y) / len(y)
        w -= lr * gradient
    return w


def logistic_predict(X, w):
    preds = 1.0 / (1.0 + np.exp(-X.dot(w)))
    return (preds >= 0.5).astype(int)


def make_df(n=60):
    base = np.linspace(100, 101, n)
    data = {
        "open_time": pd.date_range("2024-01-01", periods=n, freq="min"),
        "open": base,
        "high": base + 1,
        "low": base - 1,
        "close": base + np.sin(np.linspace(0, 3, n)) / 100,
        "volume": np.linspace(1000, 2000, n),
    }
    return pd.DataFrame(data)


def test_end_to_end_training():
    df = make_df()
    df = add_features(df)
    df = create_labels(df, horizon=1, threshold=0.0005)
    features_cols = ['return_1m', 'SMA_5', 'EMA_5']
    X = df[features_cols].to_numpy()
    y = df['label'].to_numpy()
    w = logistic_train(X, y, lr=0.5, epochs=300)
    preds = logistic_predict(X, w)
    assert len(preds) == len(y)
    assert set(np.unique(preds)) <= {0, 1}

