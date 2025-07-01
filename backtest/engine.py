"""Engine for backtesting multiple symbols simultaneously."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Optional
from datetime import datetime

import pandas as pd

from .portfolio import Portfolio
from .trade import Trade


class MultiPairBacktester:
    """Iterate over historical data for multiple symbols."""

    def __init__(
        self,
        data: Dict[str, pd.DataFrame],
        strategy: Callable[[pd.Series, str], Optional[str]],
        initial_capital: float = 1000.0,
        risk_per_trade: float = 0.01,
        min_notional: float = 0.0,
        commission_pct: float = 0.0,
    ):
        self.data = {s: df.reset_index(drop=True) for s, df in data.items()}
        self.strategy = strategy
        self.portfolio = Portfolio(initial_capital, risk_per_trade)
        self.min_notional = min_notional
        self.commission_pct = commission_pct
        self.equity_curve = [initial_capital]
        self.trades: Dict[str, list[Trade]] = {s: [] for s in data}
        self.open_trades: Dict[str, Trade] = {}

    def _close_trade(self, symbol: str, index: int, price: float, reason: str):
        trade = self.open_trades.pop(symbol)
        trade.exit_index = index
        exit_row = self.data[symbol].iloc[index]
        trade.exit_time = exit_row.get("open_time", datetime.utcnow())
        trade.exit_price = price
        trade.reason = reason
        fee = (trade.entry_price + price) * trade.size * self.commission_pct
        trade.fees = fee
        pnl = (
            price - trade.entry_price
            if trade.direction == "long"
            else trade.entry_price - price
        ) * trade.size - fee
        self.portfolio.update_equity(pnl)
        self.trades[symbol].append(trade)
        self.equity_curve.append(self.portfolio.equity)

    def run(self) -> float:
        max_len = max(len(df) for df in self.data.values())
        for i in range(max_len):
            for symbol, df in self.data.items():
                if i >= len(df):
                    continue
                row = df.iloc[i]
                price = float(row["close"])
                high = float(row.get("high", price))
                low = float(row.get("low", price))

                trade = self.open_trades.get(symbol)
                if trade:
                    if trade.direction == "long":
                        if low <= trade.stop:
                            self._close_trade(symbol, i, trade.stop, "stop")
                            continue
                        if high >= trade.take_profit:
                            self._close_trade(symbol, i, trade.take_profit, "take_profit")
                            continue
                    else:
                        if high >= trade.stop:
                            self._close_trade(symbol, i, trade.stop, "stop")
                            continue
                        if low <= trade.take_profit:
                            self._close_trade(symbol, i, trade.take_profit, "take_profit")
                            continue

                if symbol not in self.open_trades:
                    signal = self.strategy(row, symbol)
                    if signal in {"long", "short"}:
                        size = self.portfolio.position_size(price)
                        if size * price < self.min_notional:
                            continue
                        stop = price * (1 - self.portfolio.stop_loss_pct)
                        take = price * (1 + self.portfolio.take_profit_pct)
                        if signal == "short":
                            stop = price * (1 + self.portfolio.stop_loss_pct)
                            take = price * (1 - self.portfolio.take_profit_pct)
                        trade = Trade(
                            symbol=symbol,
                            direction=signal,
                            entry_index=i,
                            entry_time=row.get("open_time", datetime.utcnow()),
                            entry_price=price,
                            size=size,
                            stop=stop,
                            take_profit=take,
                        )
                        self.open_trades[symbol] = trade

            self.equity_curve.append(self.portfolio.equity)

        for symbol in list(self.open_trades):
            trade = self.open_trades[symbol]
            df = self.data[symbol]
            price = float(df.iloc[-1]["close"])
            self._close_trade(symbol, len(df) - 1, price, "end")

        return self.portfolio.equity

    def all_trades(self) -> Iterable[Trade]:
        for trades in self.trades.values():
            for t in trades:
                yield t
