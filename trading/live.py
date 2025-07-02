class Trader:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def execute(self, signals):
        for signal in signals:
            self.logger.info(f"Enviando orden real: {signal}")
            # Aquí implementas llamada a la API de Binance para crear orden

    def stats(self):
        return {}
