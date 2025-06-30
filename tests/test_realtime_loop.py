import json
import pandas as pd

from live_trading import LiveTrader
from tests.test_risk import MockClient
from realtime_loop import check_manual_closures


def test_manual_close_stop(tmp_path, caplog):
    client = MockClient()
    open_file = tmp_path / "trades.json"
    trader = LiveTrader("BTCUSDT", 10000, client=client, open_trades_file=str(open_file))

    trade = trader.open_trade(100, direction="long")
    row = pd.Series({"close": 99.0, "high": 100.0, "low": 98.5})

    with caplog.at_level("INFO"):
        check_manual_closures(trader, row)

    assert trade not in trader.open_trades
    with open(open_file) as fh:
        data = json.load(fh)
    assert data == []
    assert "stop" in caplog.text


def test_manual_close_take_profit(tmp_path):
    client = MockClient()
    open_file = tmp_path / "trades.json"
    trader = LiveTrader("BTCUSDT", 10000, client=client, open_trades_file=str(open_file))

    trade = trader.open_trade(100, direction="long")
    row = pd.Series({"close": 103.0, "high": 103.0, "low": 100.0})

    check_manual_closures(trader, row)

    assert trade not in trader.open_trades
    with open(open_file) as fh:
        data = json.load(fh)
    assert data == []
