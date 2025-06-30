"""Performance metrics utilities."""

from __future__ import annotations

from typing import Iterable, Dict
import math
import pandas as pd

from .trade import Trade


def compute_metrics(trades: Iterable[Trade], equity_curve: Iterable[float]) -> Dict[str, float]:
    trades = list(trades)
    equity = list(equity_curve)
    profits = [t.pnl() for t in trades if t.pnl() > 0]
    losses = [t.pnl() for t in trades if t.pnl() < 0]
    total_pnl = equity[-1] - equity[0] if equity else 0.0
    win_rate = len(profits) / len(trades) if trades else 0.0
    profit_factor = sum(profits) / abs(sum(losses)) if losses else float('inf')
    returns = pd.Series(equity).pct_change().dropna()
    if not returns.empty:
        sharpe = returns.mean() / returns.std() * math.sqrt(len(returns))
    else:
        sharpe = 0.0
    cum = pd.Series(equity).cummax()
    drawdown = (pd.Series(equity) - cum).min()
    return {
        "pnl": total_pnl,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown": drawdown,
        "sharpe": sharpe,
    }
