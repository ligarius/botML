import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import numpy as np
import hyperoptimize


def test_optimize_model_returns_estimator(monkeypatch):
    df = pd.DataFrame({'close': np.linspace(1, 2, 20)})
    monkeypatch.setattr(hyperoptimize, 'load_data', lambda: df)
    model = hyperoptimize.optimize_model()
    assert hasattr(model, 'predict')
    assert hasattr(model, 'n_features_in_')
