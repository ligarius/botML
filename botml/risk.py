"""Risk management utilities for live trading."""

from dataclasses import dataclass

from .alerts import send_alert
from .utils import load_config

CONFIG = load_config()

@dataclass
class PositionSizer:
    account_size: float
    risk_per_trade: float = 0.01  # fraction of account to risk per trade

    def size_from_stop(self, entry_price: float, stop_price: float) -> float:
        """Calculate position size based on stop level."""
        risk_per_unit = abs(entry_price - stop_price)
        if risk_per_unit <= 0:
            raise ValueError("Stop price must differ from entry price")
        risk_amount = self.account_size * self.risk_per_trade
        size = risk_amount / risk_per_unit
        return size

@dataclass
class RiskManager:
    account_size: float
    max_drawdown_pct: float = 0.2
    stop_loss_pct: float = 0.01
    take_profit_pct: float = 0.02
    alert_threshold_pct: float = 0.1

    def __post_init__(self):
        self.high_water_mark = self.account_size

    def update_equity(self, equity: float) -> bool:
        """Update equity and return True if trading is allowed."""
        self.high_water_mark = max(self.high_water_mark, equity)
        drawdown = (self.high_water_mark - equity) / self.high_water_mark
        if drawdown >= self.alert_threshold_pct:
            send_alert(f"Drawdown alert: {drawdown:.2%}", CONFIG.get('alerts', {}))
        return drawdown <= self.max_drawdown_pct

    def stop_loss_price(self, entry_price: float, direction: str = "long") -> float:
        if direction == "long":
            return entry_price * (1 - self.stop_loss_pct)
        return entry_price * (1 + self.stop_loss_pct)

    def take_profit_price(self, entry_price: float, direction: str = "long") -> float:
        if direction == "long":
            return entry_price * (1 + self.take_profit_pct)
        return entry_price * (1 - self.take_profit_pct)
