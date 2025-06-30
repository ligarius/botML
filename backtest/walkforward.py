"""Walk-forward training/testing utilities for backtesting."""

from __future__ import annotations
from typing import Iterable, Tuple

import pandas as pd


def rolling_windows(df: pd.DataFrame, train: int, test: int) -> Iterable[Tuple[pd.DataFrame, pd.DataFrame]]:
    if train <= 0 or test <= 0:
        raise ValueError("train and test sizes must be positive")
    n = len(df)
    for start in range(0, n - train - test + 1, test):
        train_df = df.iloc[start : start + train].reset_index(drop=True)
        test_df = df.iloc[start + train : start + train + test].reset_index(drop=True)
        yield train_df, test_df


def walk_forward(df: pd.DataFrame, train: int, test: int, fit_func, eval_func) -> float:
    scores = []
    for train_df, test_df in rolling_windows(df, train, test):
        model = fit_func(train_df)
        score = eval_func(model, test_df)
        scores.append(score)
    return sum(scores) / len(scores)
