"""Engine to run historical backtests of trading strategies."""


class Backtester:
    """Coordinate the backtesting process."""

    def __init__(self, config, logger):
        """Initialize the engine with configuration and logger."""

        self.config = config
        self.logger = logger

    def run(self):
        """Execute the backtest over historical data."""

        self.logger.info("Backtest: simulando histórico completo...")
        # Aquí llamas a Simulator con histórico completo, generas métricas, etc.
