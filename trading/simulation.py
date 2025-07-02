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
        self.balance = config.get("balance", 1000)  # Capital virtual inicial
        self.commission_pct = 0.001

    def simulate(self, signals):
        """Process signals updating the virtual balance."""

        for signal in signals:
            usdt_amount = signal.get("usdt_amount")
            if usdt_amount is None:
                self.logger.warning("Falta campo 'usdt_amount' en signal: %s", signal)
                usdt_amount = self.config.get("trade_size", 10)
            price = signal.get("price")
            if price is None:
                self.logger.warning("Falta campo 'price' en signal: %s", signal)
                price = 0
            qty = signal.get("qty", usdt_amount / price if price else 0)
            fill_price = self._simulate_slippage(signal)
            side = signal.get("side")
            if side == "BUY":
                if usdt_amount > self.balance:
                    self.logger.warning(
                        f"Trade rechazado: monto ({usdt_amount}) mayor que el balance disponible ({self.balance})."
                    )
                    continue
                self.balance -= usdt_amount
            elif side == "SELL":
                self.balance += qty * fill_price
            else:
                self.logger.warning("Valor 'side' inválido en signal: %s", signal)
            self.logger.info(
                "Trade ejecutado | Modo: Simulado | Símbolo: %s | Acción: %s | Monto USDT: %s | Qty: %.8f | Precio: %.2f | Balance post-trade: %.2f",
                signal.get("symbol", "n/a"),
                side,
                usdt_amount,
                qty,
                fill_price,
                self.balance,
            )

    def _simulate_slippage(self, signal):
        """Return a fill price with random slippage applied."""

        # Dummy: slippage aleatorio +/- 0.1%
        return float(signal.get("price", 100)) * (1 + random.uniform(-0.001, 0.001))
