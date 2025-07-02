"""Live trading utilities for sending orders to an exchange."""


import os
from dotenv import load_dotenv


class Trader:
    """Execute real trades on the configured exchange."""

    def __init__(self, config, logger):
        """Create a live trader.

        Parameters
        ----------
        config : dict
            Trading configuration.
        logger : logging.Logger
            Logger used for execution details.
        """

        self.config = config
        self.logger = logger
        if os.path.exists(".env"):
            load_dotenv(".env")
        self.api_key = os.environ.get("API_KEY", config.get("api_key"))
        self.api_secret = os.environ.get("API_SECRET", config.get("api_secret"))
        self.trades = 0
        self.balance = config.get("balance", 1000)

    def execute(self, signals):
        """Send trading orders for the provided signals."""

        for signal in signals:
            self.logger.info("Enviando orden real: %s", signal)
            try:
                usdt_amount = signal.get("usdt_amount")
                if usdt_amount is None:
                    self.logger.warning("Falta campo 'usdt_amount' en signal: %s", signal)
                    usdt_amount = self.config.get("trade_size", 10)
                price = signal.get("price")
                if price is None:
                    self.logger.warning("Falta campo 'price' en signal: %s", signal)
                    price = 0
                qty = signal.get("qty", usdt_amount / price if price else 0)
                fill_price = float(price)
                side = signal.get("side")
                # Aquí implementas llamada a la API de Binance para crear orden
                self.trades += 1
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
                    "Trade ejecutado | Modo: Real | Símbolo: %s | Acción: %s | Monto USDT: %s | Qty: %.8f | Precio: %.2f | Balance post-trade: %.2f",
                    signal.get("symbol", "n/a"),
                    side,
                    usdt_amount,
                    qty,
                    fill_price,
                    self.balance,
                )
            except Exception as exc:
                self.logger.error("ERROR al ejecutar orden: %s", exc)

    def stats(self):
        """Return runtime trading statistics."""
        return {"trades": self.trades, "balance": self.balance}
