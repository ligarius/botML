"""Utility functions for saving and loading bot metrics."""

from __future__ import annotations

import json
from typing import Any, List, Dict

from strategy import StrategyVariant


def gather_metrics(trader: Any, model_manager: Any, variants: List[StrategyVariant] | None = None) -> Dict[str, Any]:
    """Collect metrics from core components for serialization."""
    data = {
        "trader": trader.stats(),
        "model": model_manager.stats(),
    }
    if variants:
        data["variants"] = [
            {
                "gen": v.generation,
                **v.params,
                **(v.history[-1] if v.history else {}),
            }
            for v in variants
        ]
    return data


def save_metrics(metrics: Dict[str, Any], path: str = "results.json") -> None:
    """Write metrics to a JSON file."""
    with open(path, "w") as f:
        json.dump(metrics, f)


def load_metrics(path: str = "results.json") -> Dict[str, Any]:
    """Read metrics from a JSON file."""
    with open(path) as f:
        return json.load(f)
