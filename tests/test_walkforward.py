import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression

from botml.walkforward import rolling_windows, walk_forward_optimize


def make_df(n=60):
    rng = np.random.default_rng(0)
    f1 = rng.standard_normal(n)
    df = pd.DataFrame({'f1': f1})
    df['label'] = (df['f1'] > 0).astype(int)
    return df


def test_rolling_windows_counts():
    df = make_df()
    windows = list(rolling_windows(df, train_size=10, test_size=5))
    assert len(windows) == 10
    for train, test in windows:
        assert len(train) == 10
        assert len(test) == 5


def test_walk_forward_optimize_selects_best(tmp_path):
    df = make_df()
    models = {
        'dummy': DummyClassifier(strategy='most_frequent'),
        'lr': LogisticRegression(max_iter=1000, solver='liblinear'),
    }
    export = tmp_path / 'best.pkl'
    best, score, metrics = walk_forward_optimize(
        df,
        features=['f1'],
        label_col='label',
        models=models,
        train_size=10,
        test_size=5,
        export_path=str(export),
    )
    assert best == 'lr'
    assert 'dummy' in metrics and 'lr' in metrics
    assert export.exists()
