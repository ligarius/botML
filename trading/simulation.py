import random

class Simulator:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.balance = 1000  # Capital virtual inicial
        self.commission_pct = 0.001

    def simulate(self, signals):
        for signal in signals:
            fill_price = self._simulate_slippage(signal)
            self.balance -= fill_price * self.commission_pct
            self.logger.info(f"Simulación: {signal} ejecutada a {fill_price}, balance: {self.balance:.2f}")

    def _simulate_slippage(self, signal):
        # Dummy: slippage aleatorio +/- 0.1%
        return float(signal.get("price", 100)) * (1 + random.uniform(-0.001, 0.001))
