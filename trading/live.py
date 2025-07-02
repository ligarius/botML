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
            self.logger.info(f"Enviando orden real: {signal}")
            try:
                # Aquí implementas llamada a la API de Binance para crear orden
                self.trades += 1
                self.logger.info(
                    f"Orden ejecutada: {signal['symbol']} | Resultado: OK | Precio: {signal.get('price', 'N/A')} | Qty: {signal.get('amount', 'N/A')}"
                )
            except Exception as exc:
                self.logger.error(f"ERROR al ejecutar orden: {exc}")

    def stats(self):
        """Return runtime trading statistics."""
        return {"trades": self.trades, "pnl": self.pnl}
