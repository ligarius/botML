"""Simple live trading skeleton using the risk module."""

from dataclasses import dataclass
from typing import Optional

from risk import PositionSizer, RiskManager

@dataclass
class Trade:
    entry_price: float
    direction: str  # 'long' or 'short'
    size: float
    stop: float
    take_profit: float

class LiveTrader:
    def __init__(self, account_size: float,
                 risk_manager: Optional[RiskManager] = None,
                 sizer: Optional[PositionSizer] = None):
        self.account_size = account_size
        self.sizer = sizer or PositionSizer(account_size)
        self.risk_manager = risk_manager or RiskManager(account_size)
        self.open_trades = []

    def open_trade(self, entry_price: float, direction: str = "long") -> Trade:
        stop = self.risk_manager.stop_loss_price(entry_price, direction)
        take_profit = self.risk_manager.take_profit_price(entry_price, direction)
        size = self.sizer.size_from_stop(entry_price, stop)
        trade = Trade(entry_price, direction, size, stop, take_profit)
        # In a real implementation, send order to exchange here
        self.open_trades.append(trade)
        return trade

    def update_equity(self, equity: float) -> bool:
        """Update equity and enforce max drawdown."""
        return self.risk_manager.update_equity(equity)
