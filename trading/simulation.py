"""Trading simulator used for backtests or dry runs."""

import random


class Simulator:
    """Simulate order execution without interacting with an exchange."""

    def __init__(self, config, logger):
        """Create a new simulator instance.

        Parameters
        ----------
        config : dict
            Configuration values.
        logger : logging.Logger
            Logger for simulation output.
        """

        self.config = config
        self.logger = logger
        self.balance = 1000  # Capital virtual inicial
        self.commission_pct = 0.001

    def simulate(self, signals):
        """Process signals updating the virtual balance."""

        for signal in signals:
            fill_price = self._simulate_slippage(signal)
            self.balance -= fill_price * self.commission_pct
            self.logger.info(
                f"Simulación: {signal} ejecutada a {fill_price}, balance: {self.balance:.2f}"
            )

    def _simulate_slippage(self, signal):
        """Return a fill price with random slippage applied."""

        # Dummy: slippage aleatorio +/- 0.1%
        return float(signal.get("price", 100)) * (1 + random.uniform(-0.001, 0.001))
