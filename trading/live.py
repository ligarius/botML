"""Live trading utilities for sending orders to an exchange."""


import os


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
        self.api_key = os.environ.get("API_KEY", config.get("api_key"))
        self.api_secret = os.environ.get("API_SECRET", config.get("api_secret"))

    def execute(self, signals):
        """Send trading orders for the provided signals."""

        for signal in signals:
            self.logger.info(f"Enviando orden real: {signal}")
            # Aquí implementas llamada a la API de Binance para crear orden

    def stats(self):
        """Return runtime trading statistics."""

        return {}
