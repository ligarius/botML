import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
from backtest.walkforward import rolling_windows, walk_forward


def make_df(n=30):
    df = pd.DataFrame({'x': range(n), 'y': [0 if i % 2 == 0 else 1 for i in range(n)]})
    return df


def test_rolling_windows_counts():
    df = make_df(20)
    windows = list(rolling_windows(df, train=5, test=5))
    assert len(windows) == 3
    for tr, te in windows:
        assert len(tr) == 5
        assert len(te) == 5


def test_walk_forward_average():
    df = make_df(20)

    def fit(train_df):
        mean = train_df['y'].mean()
        return mean

    def eval_fn(model, test_df):
        return abs(model - test_df['y'].mean())

    score = walk_forward(df, 5, 5, fit, eval_fn)
    assert score >= 0
