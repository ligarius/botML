"""Trade data container used by the backtester."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Trade:
    symbol: str
    direction: str
    entry_index: int
    entry_time: datetime
    entry_price: float
    size: float
    stop: float
    take_profit: float
    exit_index: Optional[int] = None
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    fees: float = 0.0
    reason: Optional[str] = None

    def pnl(self) -> float:
        if self.exit_price is None:
            return 0.0
        diff = (
            self.exit_price - self.entry_price
            if self.direction == "long"
            else self.entry_price - self.exit_price
        )
        return diff * self.size - self.fees
