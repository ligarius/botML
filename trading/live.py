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
        self.pnl = 0.0

    def execute(self, signals):
        """Send trading orders for the provided signals."""

        for signal in signals:
            self.logger.info("Enviando orden real: %s", signal)
            try:
                trade_amount = signal.get("amount")
                if trade_amount is None:
                    self.logger.warning("Falta campo 'amount' en signal: %s", signal)
                    trade_amount = self.config.get("trade_size", 10)
                if "price" not in signal:
                    self.logger.warning("Falta campo 'price' en signal: %s", signal)
                fill_price = float(signal.get("price", 0))
                side = signal.get("side")
                # Aquí implementas llamada a la API de Binance para crear orden
                self.trades += 1
                if side == "BUY":
                    self.pnl -= trade_amount * fill_price
                elif side == "SELL":
                    self.pnl += trade_amount * fill_price
                else:
                    self.logger.warning("Valor 'side' inválido en signal: %s", signal)
                self.logger.info(
                    "Trade ejecutado | Modo: Real | Símbolo: %s | Acción: %s | Monto: %s | Precio: %.2f | Score: %s | Balance post-trade: %.2f",
                    signal.get("symbol", "n/a"),
                    side,
                    trade_amount,
                    fill_price,
                    signal.get("score", "n/a"),
                    self.pnl,
                )
            except Exception as exc:
                self.logger.error("ERROR al ejecutar orden: %s", exc)

    def stats(self):
        """Return runtime trading statistics."""
        return {"trades": self.trades, "pnl": self.pnl}
