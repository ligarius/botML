"""Simple portfolio utilities for capital allocation."""

from dataclasses import dataclass


@dataclass
class Portfolio:
    """Manage account equity and risk sizing."""

    equity: float
    risk_per_trade: float = 0.01
    stop_loss_pct: float = 0.01
    take_profit_pct: float = 0.02

    def position_size(self, entry_price: float) -> float:
        """Return trade size based on risk per trade and stop loss."""
        risk_amount = self.equity * self.risk_per_trade
        stop_price = entry_price * (1 - self.stop_loss_pct)
        risk_per_unit = abs(entry_price - stop_price)
        if risk_per_unit <= 0:
            raise ValueError("Stop price must differ from entry price")
        size = risk_amount / risk_per_unit
        return size

    def update_equity(self, pnl: float):
        self.equity += pnl
