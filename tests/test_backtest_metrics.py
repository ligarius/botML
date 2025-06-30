import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime
from backtest.trade import Trade
from backtest.metrics import compute_metrics


def make_trades():
    t1 = Trade('A', 'long', 0, datetime.utcnow(), 1.0, 1, 0.9, 1.1)
    t1.exit_index = 1
    t1.exit_time = datetime.utcnow()
    t1.exit_price = 1.1
    t1.fees = 0
    t2 = Trade('A', 'long', 0, datetime.utcnow(), 1.0, 1, 0.9, 1.1)
    t2.exit_index = 1
    t2.exit_time = datetime.utcnow()
    t2.exit_price = 0.95
    t2.fees = 0
    return [t1, t2]


def test_compute_metrics_basic():
    trades = make_trades()
    equity = [1000, 1010, 1005]
    metrics = compute_metrics(trades, equity)
    assert metrics['pnl'] == 5
    assert metrics['win_rate'] == 0.5
    assert metrics['profit_factor'] > 1
