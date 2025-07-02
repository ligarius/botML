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
            trade_amount = signal.get("amount")
            if trade_amount is None:
                self.logger.warning("Falta campo 'amount' en signal: %s", signal)
                trade_amount = self.config.get("trade_size", 10)
            if "price" not in signal:
                self.logger.warning("Falta campo 'price' en signal: %s", signal)
            fill_price = self._simulate_slippage(signal)
            side = signal.get("side")
            if side == "BUY":
                self.balance -= trade_amount * fill_price
            elif side == "SELL":
                self.balance += trade_amount * fill_price
            else:
                self.logger.warning("Valor 'side' inválido en signal: %s", signal)
            self.logger.info(
                "Trade ejecutado | Modo: Simulado | Símbolo: %s | Acción: %s | Monto: %s | Precio: %.2f | Score: %s | Balance post-trade: %.2f",
                signal.get("symbol", "n/a"),
                side,
                trade_amount,
                fill_price,
                signal.get("score", "n/a"),
                self.balance,
            )

    def _simulate_slippage(self, signal):
        """Return a fill price with random slippage applied."""

        # Dummy: slippage aleatorio +/- 0.1%
        return float(signal.get("price", 100)) * (1 + random.uniform(-0.001, 0.001))
