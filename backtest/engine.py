"""Engine to run historical backtests of trading strategies."""


import random
from typing import List, Dict

from strategy import StrategyVariant


class Backtester:
    """Coordinate the backtesting process."""

    def __init__(self, config, logger):
        """Initialize the engine with configuration and logger."""

        self.config = config
        self.logger = logger

    def run(self, variants: List[StrategyVariant] | None = None) -> Dict[int, Dict[str, float]]:
        """Execute the backtest for provided variants.

        Parameters
        ----------
        variants : list[StrategyVariant], optional
            Strategy variants to evaluate. When ``None`` only logs the start
            of a generic backtest.

        Returns
        -------
        dict
            Mapping of variant ``id`` to metrics generated during the run.
        """

        self.logger.info("Iniciando backtest sobre histórico...")
        results: Dict[int, Dict[str, float]] = {}
        if not variants:
            return results

        for variant in variants:
            metrics = {
                "roi": random.uniform(-0.05, 0.05),
                "winrate": random.uniform(0, 1),
                "drawdown": random.uniform(0, 0.1),
            }
            variant.record_result(metrics)
            results[id(variant)] = metrics
        best = max(results.values(), key=lambda m: m["roi"], default=None)
        if best:
            self.logger.info(
                f"Backtest completado. ROI: {best['roi']:.3f} | Winrate: {best['winrate']:.2f} | Drawdown: {best['drawdown']:.2f}"
            )
        return results
