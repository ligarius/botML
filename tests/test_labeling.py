import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
from labeling import create_labels


def test_create_labels_binary():
    df = pd.DataFrame({'close': [1.0, 1.05, 1.02, 1.04]})
    labeled = create_labels(df, horizon=1, threshold=0.03)
    assert 'label' in labeled.columns
    # expected labels: first row future return 5% > 3% -> 1; second row -2.9% -> 0; third row 1.96% < 3% ->0
    assert list(labeled['label']) == [1, 0, 0, 0]


