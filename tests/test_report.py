import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime
from backtest.trade import Trade
from backtest.report import report_summary_console


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


def test_report_summary_console_output(capsys):
    trades = make_trades()
    equity = [1000, 1010, 1005]
    report_summary_console(trades, equity)
    output = capsys.readouterr().out
    assert "Start equity" in output and "1000" in output
    assert "End equity" in output and "1005" in output
    assert "Total trades" in output and "2" in output
    assert "Win rate" in output and "50.00%" in output
    assert "Profit factor" in output and "2.00" in output
