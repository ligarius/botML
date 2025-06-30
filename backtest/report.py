"""Reporting utilities for backtest results."""

from __future__ import annotations

import csv
import json
from typing import Iterable

from .trade import Trade
from .metrics import compute_metrics


def report_console(trades: Iterable[Trade], equity_curve: Iterable[float]):
    metrics = compute_metrics(trades, equity_curve)
    for k, v in metrics.items():
        print(f"{k}: {v}")


def report_summary_console(trades: Iterable[Trade], equity_curve: Iterable[float]):
    """Print a human readable summary of a backtest."""
    metrics = compute_metrics(trades, equity_curve)
    trades = list(trades)
    equity_curve = list(equity_curve)

    start_equity = equity_curve[0] if equity_curve else 0.0
    end_equity = equity_curve[-1] if equity_curve else start_equity
    net_profit = end_equity - start_equity
    avg_pnl = net_profit / len(trades) if trades else 0.0

    summary = (
        f"Start equity : {start_equity}\n"
        f"End equity   : {end_equity}\n"
        f"Net profit   : {net_profit}\n"
        f"Avg trade PnL: {avg_pnl}\n"
        f"Total trades : {len(trades)}\n"
        f"Win rate     : {metrics['win_rate']:.2%}\n"
        f"Profit factor: {metrics['profit_factor']:.2f}\n"
        f"Max drawdown : {metrics['max_drawdown']}\n"
        f"Sharpe ratio : {metrics['sharpe']:.2f}"
    )
    print(summary)


def report_csv(trades: Iterable[Trade], path: str):
    fields = list(Trade.__dataclass_fields__)
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for t in trades:
            writer.writerow({f: getattr(t, f) for f in fields})


def report_json(trades: Iterable[Trade], equity_curve: Iterable[float], path: str):
    metrics = compute_metrics(trades, equity_curve)
    data = {
        "metrics": metrics,
        "trades": [t.__dict__ for t in trades],
        "equity_curve": list(equity_curve),
    }
    with open(path, "w") as fh:
        json.dump(data, fh)
