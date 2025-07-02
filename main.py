from data_feed.downloader import DataFeed
from models.manager import ModelManager
from trading.live import Trader
from trading.simulation import Simulator
from backtest.engine import Backtester
from dashboard.dashboard import Dashboard
from logging_utils.logging import setup_logging
from watchdog.watchdog import Watchdog
import time

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
        time.sleep(config.get("cycle_sleep", 60))

if __name__ == "__main__":
    main()
