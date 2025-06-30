import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd

from backtest.engine import MultiPairBacktester


def make_data():
    df1 = pd.DataFrame({
        'close': [1.0, 1.2, 1.3],
        'high': [1.0, 1.2, 1.3],
        'low': [1.0, 1.2, 1.3],
    })
    df2 = pd.DataFrame({
        'close': [2.0, 2.1, 2.2],
        'high': [2.0, 2.1, 2.2],
        'low': [2.0, 2.1, 2.2],
    })
    return {'A': df1, 'B': df2}


def test_min_notional_blocks_trade():
    data = make_data()

    def strat(row, symbol):
        return 'long' if row.name == 0 else None

    bt = MultiPairBacktester(data, strat, initial_capital=1000, min_notional=1e6)
    equity = bt.run()
    assert equity == 1000
    assert list(bt.all_trades()) == []


def test_backtester_runs_trades():
    data = make_data()

    def strat(row, symbol):
        return 'long' if row.name == 0 else None

    bt = MultiPairBacktester(data, strat, initial_capital=1000, risk_per_trade=0.1)
    equity = bt.run()
    trades = list(bt.all_trades())
    assert len(trades) == 2
    assert equity > 1000
