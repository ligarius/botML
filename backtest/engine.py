class Backtester:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def run(self):
        self.logger.info("Backtest: simulando histórico completo...")
        # Aquí llamas a Simulator con histórico completo, generas métricas, etc.
