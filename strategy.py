import random
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class StrategyVariant:
    """Represent a set of trading parameters and its performance history."""

    params: Dict[str, Any]
    generation: int = 0
    history: List[Dict[str, float]] = field(default_factory=list)

    def mutate(self, mutation_rate: float = 0.1, mutation_ranges: Dict[str, tuple] | None = None) -> None:
        """Randomly tweak one of the parameters within optional ranges."""

        if not self.params:
            return
        key = random.choice(list(self.params.keys()))
        value = self.params[key]
        low, high = None, None
        if mutation_ranges and key in mutation_ranges:
            low, high = mutation_ranges[key]
        if isinstance(value, (int, float)):
            if low is None:
                low = value * (1 - mutation_rate)
            if high is None:
                high = value * (1 + mutation_rate)
            new_val = value + random.uniform(-mutation_rate, mutation_rate) * value
            new_val = max(low, min(high, new_val))
            self.params[key] = new_val
        # Non-numeric parameters are left unchanged for simplicity

    def record_result(self, metrics: Dict[str, float]) -> None:
        """Store metrics for later analysis."""

        self.history.append(metrics)
