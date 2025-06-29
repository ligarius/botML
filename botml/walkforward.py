"""Walk-forward optimization utilities."""

from typing import Dict, Iterable, Tuple, List

import pandas as pd
from sklearn.base import BaseEstimator, clone
from sklearn.metrics import accuracy_score
import pickle


def rolling_windows(df: pd.DataFrame, train_size: int, test_size: int) -> Iterable[Tuple[pd.DataFrame, pd.DataFrame]]:
    """Yield rolling train/test splits."""
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be positive")
    n = len(df)
    for start in range(0, n - train_size - test_size + 1, test_size):
        train = df.iloc[start : start + train_size]
        test = df.iloc[start + train_size : start + train_size + test_size]
        yield train.reset_index(drop=True), test.reset_index(drop=True)


def walk_forward_optimize(
    df: pd.DataFrame,
    features: List[str],
    label_col: str,
    models: Dict[str, BaseEstimator],
    train_size: int,
    test_size: int,
    export_path: str = "best_model.pkl",
) -> Tuple[str, float, Dict[str, List[float]]]:
    """Evaluate models on rolling windows and save the best performer."""
    if not models:
        raise ValueError("models dictionary is empty")

    metrics: Dict[str, List[float]] = {name: [] for name in models}

    for train_df, test_df in rolling_windows(df, train_size, test_size):
        X_train, y_train = train_df[features], train_df[label_col]
        X_test, y_test = test_df[features], test_df[label_col]
        for name, model in models.items():
            m = clone(model)
            m.fit(X_train, y_train)
            preds = m.predict(X_test)
            acc = accuracy_score(y_test, preds)
            metrics[name].append(acc)

    avg = {name: sum(vals) / len(vals) for name, vals in metrics.items()}
    best_name = max(avg, key=avg.get)

    best_model = clone(models[best_name])
    best_model.fit(df[features], df[label_col])

    with open(export_path, "wb") as fh:
        pickle.dump(best_model, fh)

    return best_name, avg[best_name], metrics
