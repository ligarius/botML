"""Evolutionary functions for managing strategy variants."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from strategy import StrategyVariant


def select_top_variants(
    variants: List[StrategyVariant], metric: str = "roi", top_pct: float = 0.5
) -> List[StrategyVariant]:
    """Return the top performing variants according to the given metric."""

    if not variants:
        return []
    ranked = sorted(
        variants,
        key=lambda v: v.history[-1].get(metric, 0) if v.history else 0,
        reverse=True,
    )
    keep = max(1, int(len(ranked) * top_pct))
    return ranked[:keep]


def evolve_population(
    variants: List[StrategyVariant],
    population_size: int,
    mutation_rate: float = 0.1,
    top_pct: float = 0.5,
    metric: str = "roi",
) -> List[StrategyVariant]:
    """Select the best variants and create mutated copies until population_size."""

    selected = select_top_variants(variants, metric=metric, top_pct=top_pct)
    new_population: List[StrategyVariant] = []
    for variant in selected:
        new_population.append(variant)
        clone = StrategyVariant(params=variant.params.copy(), generation=variant.generation + 1)
        clone.mutate(mutation_rate)
        new_population.append(clone)

    while len(new_population) < population_size:
        base = selected[0] if selected else variants[0]
        clone = StrategyVariant(params=base.params.copy(), generation=base.generation + 1)
        clone.mutate(mutation_rate)
        new_population.append(clone)

    return new_population[:population_size]


def save_population(variants: List[StrategyVariant], path: str) -> None:
    data = [
        {"params": v.params, "generation": v.generation, "history": v.history}
        for v in variants
    ]
    Path(path).write_text(json.dumps(data))


def load_population(path: str) -> List[StrategyVariant]:
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    variants = []
    for item in data:
        variant = StrategyVariant(
            params=item.get("params", {}),
            generation=item.get("generation", 0),
        )
        for hist in item.get("history", []):
            variant.record_result(hist)
        variants.append(variant)
    return variants
