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
