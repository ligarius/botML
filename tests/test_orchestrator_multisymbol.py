import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
from sklearn.dummy import DummyClassifier

import orchestrator


def test_backtest_model_multisymbol():
    df1 = pd.DataFrame({'f1': [0.1, 0.2], 'close': [1.0, 1.1], 'label': [1, 1]})
    df2 = pd.DataFrame({'f1': [0.3, 0.4], 'close': [2.0, 2.1], 'label': [1, 1]})
    train_df = pd.concat([df1, df2], ignore_index=True)
    model = DummyClassifier(strategy='constant', constant=1)
    model.fit(train_df[['f1', 'close']], train_df['label'])

    equity, metrics, trades = orchestrator.backtest_model({'A': df1, 'B': df2}, model)

    assert len(trades) == 2
    symbols = {t.symbol for t in trades}
    assert symbols == {'A', 'B'}
