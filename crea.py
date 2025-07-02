import os

folders = [
    "data_feed",
    "models",
    "trading",
    "backtest",
    "dashboard",
    "logging_utils",
    "watchdog",
]

files = {
    "main.py": '''
from data_feed.downloader import DataFeed
from models.manager import ModelManager
from trading.live import Trader
from trading.simulation import Simulator
from backtest.engine import Backtester
from dashboard.dashboard import Dashboard
from logging_utils.logging import setup_logging
from watchdog.watchdog import Watchdog

import yaml

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    logger = setup_logging(config)
    mode = config.get("mode", "live")

    feed = DataFeed(config, logger)
    model_manager = ModelManager(config, logger)
    trader = Trader(config, logger)
    simulator = Simulator(config, logger)
    backtester = Backtester(config, logger)
    dashboard = Dashboard(config, logger)
    watchdog = Watchdog(config, logger)

    while True:
        watchdog.heartbeat()
        feed.update()
        if mode == "live":
            signals = model_manager.predict(feed.latest_data())
            trader.execute(signals)
        elif mode == "test":
            signals = model_manager.predict(feed.latest_data())
            simulator.simulate(signals)
        elif mode == "backtest":
            backtester.run()
            break
        if model_manager.need_retrain():
            model_manager.retrain(feed.history())
        dashboard.update(trader.stats(), model_manager.stats())

if __name__ == "__main__":
    main()
''',

    "config.yaml": '''api_url: https://api.binance.com
database_path: binance_1m.db
symbols: [BTCUSDT, ETHUSDT]
interval: '1m'
mode: live   # live | test | backtest
log_level: INFO
log_file: bot.log
watchdog_timeout: 120
''',

    "requirements.txt": '''pandas
numpy
scikit-learn
pyyaml
joblib
streamlit
requests
''',
}

class_skeletons = {
    "data_feed/downloader.py": '''
class DataFeed:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def update(self):
        self.logger.info("Actualizando datos de mercado...")

    def latest_data(self):
        pass

    def history(self):
        pass
''',
    "models/manager.py": '''
class ModelManager:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.model = None

    def predict(self, df):
        pass

    def need_retrain(self):
        pass

    def retrain(self, history_df):
        self.logger.info("Reentrenando modelo...")

    def stats(self):
        pass
''',
    "trading/live.py": '''
class Trader:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def execute(self, signals):
        self.logger.info(f"Ejecutando {len(signals)} señales en vivo...")

    def stats(self):
        pass
''',
    "trading/simulation.py": '''
class Simulator:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def simulate(self, signals):
        self.logger.info(f"Simulando {len(signals)} señales...")
''',
    "backtest/engine.py": '''
class Backtester:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def run(self):
        self.logger.info("Iniciando backtest completo...")
''',
    "dashboard/dashboard.py": '''
class Dashboard:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def update(self, trader_stats, model_stats):
        pass
''',
    "logging_utils/logging.py": '''
import logging

def setup_logging(config):
    level = config.get("log_level", "INFO")
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(config.get("log_file", "bot.log")),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("Bot")
''',
    "watchdog/watchdog.py": '''
import time

class Watchdog:
    def __init__(self, config, logger):
        self.last_heartbeat = time.time()
        self.timeout = config.get("watchdog_timeout", 120)
        self.logger = logger

    def heartbeat(self):
        now = time.time()
        if now - self.last_heartbeat > self.timeout:
            self.logger.error("Watchdog: reiniciando proceso...")
        self.last_heartbeat = now
'''
}

# Crear carpetas y archivos
os.makedirs("bot", exist_ok=True)
os.chdir("bot")

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    open(os.path.join(folder, "__init__.py"), "a").close()

for fname, content in files.items():
    with open(fname, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

for fname, content in class_skeletons.items():
    with open(fname, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print("Estructura creada. Listo para implementar tu bot.")
