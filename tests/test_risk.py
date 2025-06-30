import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
from botml.risk import PositionSizer, RiskManager
from live_trading import LiveTrader


class MockClient:
    def __init__(self, min_notional=0):
        self.orders = []
        self.min_notional = min_notional

    def create_order(self, **params):
        self.orders.append(params)
        return {"status": "ok", **params}

    def reconnect(self):
        pass

    def get_symbol_min_notional(self, symbol):
        return self.min_notional


def test_position_sizer_and_risk_manager():
    sizer = PositionSizer(account_size=10000, risk_per_trade=0.01)
    risk = RiskManager(account_size=10000, stop_loss_pct=0.01, take_profit_pct=0.02)

    stop = risk.stop_loss_price(100, direction="long")
    take_profit = risk.take_profit_price(100, direction="long")
    size = sizer.size_from_stop(100, stop)

    assert stop == 99
    assert take_profit == 102
    assert size == 100


def test_live_trader_open_trade(tmp_path):
    client = MockClient()
    open_file = tmp_path / "trades.json"
    trader = LiveTrader("BTCUSDT", 10000, client=client, open_trades_file=str(open_file))

    trade = trader.open_trade(100, direction="long", bracket=True)

    assert len(client.orders) == 3
    market, stop, take_profit = client.orders
    assert market["side"] == "BUY"
    assert market["quantity"] == trade.size
    assert stop["type"] == "STOP_MARKET" and stop["stopPrice"] == trade.stop
    assert take_profit["type"] == "TAKE_PROFIT_MARKET" and take_profit["stopPrice"] == trade.take_profit

    with open(open_file) as fh:
        data = json.load(fh)
    assert data[0]["stop"] == trade.stop
    assert data[0]["take_profit"] == trade.take_profit


def test_open_trade_below_min_notional(tmp_path, caplog):
    client = MockClient(min_notional=20000)
    open_file = tmp_path / "trades.json"
    trader = LiveTrader("BTCUSDT", 10000, client=client, open_trades_file=str(open_file))

    with caplog.at_level("INFO"):
        trade = trader.open_trade(100, direction="long")

    assert trade is None
    assert client.orders == []
    assert "below minimum" in caplog.text
