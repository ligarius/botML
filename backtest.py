"""Backtesting utilities for running strategies on historical data."""

from dataclasses import dataclass
from typing import Callable, List, Optional

import pandas as pd

from botml.risk import PositionSizer, RiskManager
from botml.utils import load_config, setup_logging

CONFIG = load_config()
setup_logging(CONFIG)


@dataclass
class Trade:
    entry_index: int
    entry_price: float
    direction: str
    size: float
    stop: float
    take_profit: float
    exit_index: Optional[int] = None
    exit_price: Optional[float] = None


class Backtester:
    """Simple backtester using close prices and shared risk logic."""

    def __init__(self, data: pd.DataFrame, strategy: Callable[[pd.Series], Optional[str]],
                 account_size: float = 1000.0,
                 risk_manager: Optional[RiskManager] = None,
                 sizer: Optional[PositionSizer] = None):
        self.data = data.reset_index(drop=True)
        self.strategy = strategy
        self.account_size = account_size
        self.risk_manager = risk_manager or RiskManager(account_size)
        self.sizer = sizer or PositionSizer(account_size)
        self.equity = account_size
        self.trades: List[Trade] = []
        self.open_trade: Optional[Trade] = None

    def _close_trade(self, index: int, price: float):
        if not self.open_trade:
            return
        trade = self.open_trade
        trade.exit_index = index
        trade.exit_price = price
        if trade.direction == 'long':
            pnl = (price - trade.entry_price) * trade.size
        else:
            pnl = (trade.entry_price - price) * trade.size
        self.equity += pnl
        self.open_trade = None

    def run(self) -> float:
        for i, row in self.data.iterrows():
            price = float(row['close'])
            high = float(row.get('high', price))
            low = float(row.get('low', price))

            if self.open_trade:
                t = self.open_trade
                if t.direction == 'long':
                    if low <= t.stop:
                        self._close_trade(i, t.stop)
                        continue
                    if high >= t.take_profit:
                        self._close_trade(i, t.take_profit)
                        continue
                else:
                    if high >= t.stop:
                        self._close_trade(i, t.stop)
                        continue
                    if low <= t.take_profit:
                        self._close_trade(i, t.take_profit)
                        continue

            signal = self.strategy(row)
            if signal in ('long', 'short') and self.open_trade is None:
                stop = self.risk_manager.stop_loss_price(price, signal)
                take_profit = self.risk_manager.take_profit_price(price, signal)
                size = self.sizer.size_from_stop(price, stop)
                self.open_trade = Trade(i, price, signal, size, stop, take_profit)
                self.trades.append(self.open_trade)

        if self.open_trade:
            # Close any remaining open trade at final price
            self._close_trade(len(self.data) - 1, float(self.data.iloc[-1]['close']))
        return self.equity
