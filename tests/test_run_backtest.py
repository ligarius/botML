import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pathlib import Path
import pandas as pd
import run_backtest


def test_run_backtest_outputs_equity(tmp_path, capsys, monkeypatch):
    csv_path = tmp_path / 'btc.csv'
    df = pd.DataFrame({'close': [1, 1.1, 1.2], 'high': [1, 1.1, 1.2], 'low': [1, 1, 1]})
    df.to_csv(csv_path, index=False)
    monkeypatch.setattr(sys, 'argv', ['run_backtest.py', '--symbols', 'BTCUSDT', '--csv', str(csv_path)])
    run_backtest.main()
    out = capsys.readouterr().out
    assert 'final_equity:' in out
    value = float(out.strip().split(':')[-1])
    assert value > 0
