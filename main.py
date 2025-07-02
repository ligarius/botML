import random
from data_feed.downloader import DataFeed
from models.manager import ModelManager
from trading.live import Trader
from trading.simulation import Simulator
from backtest.engine import Backtester
from logging_utils.logging import setup_logging
from watchdog.watchdog import Watchdog
from strategy import StrategyVariant
from evolution import (
    evolve_population,
    save_population,
    load_population,
)
from modules.analytics import gather_metrics, save_metrics
import time
from datetime import datetime

import yaml
import os

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def check_api_keys(config, logger):
    """Validate API keys when running in live mode."""
    mode = config.get("mode", "test")
    logger.info(f"Modo de inicio: {mode}")
    api_key = os.environ.get("API_KEY", config.get("api_key"))
    api_secret = os.environ.get("API_SECRET", config.get("api_secret"))
    if mode == "live":
        if not api_key or not api_secret:
            logger.critical("Faltan claves API. No se puede operar en modo live.")
            raise SystemExit("No hay claves API. Bot detenido.")
        logger.info("Claves API cargadas correctamente.")

def main():
    config = load_config()
    logger = setup_logging(config)
    start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"=== Iniciando Bot de Trading - {start} ===")
    logger.info("Configuraci\u00f3n cargada correctamente.")
    mode = config.get("mode", "live")
    check_api_keys(config, logger)

    feed = DataFeed(config, logger)
    model_manager = ModelManager(config, logger)
    trader = Trader(config, logger)
    simulator = Simulator(config, logger)
    backtester = Backtester(config, logger)
    watchdog = Watchdog(config, logger)

    population_path = config.get("population_path", "population.json")
    population_size = config.get("population_size", 4)
    mutation_rate = config.get("mutation_rate", 0.1)
    selection_pct = config.get("selection_pct", 0.5)

    population = load_population(population_path)
    if not population:
        population = [
            StrategyVariant({"threshold": random.random()})
            for _ in range(population_size)
        ]

    try:
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
                backtester.run(population)
                break
            if model_manager.need_retrain():
                model_manager.retrain(feed.history())
            results = backtester.run(population)
            population = evolve_population(
                population,
                population_size=population_size,
                mutation_rate=mutation_rate,
                top_pct=selection_pct,
            )
            if results:
                best_id = max(results, key=lambda k: results[k]["roi"])
                best = results[best_id]
                logger.info(
                    f"Fin de ciclo evolutivo. Estrategia top: ROI {best['roi']:.3f} | Winrate: {best['winrate']:.2f}"
                )
                logger.info("Nuevas variantes generadas y mutadas.")
            save_population(population, population_path)
            metrics = gather_metrics(trader, model_manager, population)
            save_metrics(metrics, "results.json")
            logger.info(
                f"Balance actual: {metrics['trader'].get('balance', 0):.2f}"
            )
            time.sleep(config.get("cycle_sleep", 60))
    except KeyboardInterrupt:
        metrics = gather_metrics(trader, model_manager, population)
        logger.info(
            f"=== Bot detenido ===\nResumen final: Balance: {metrics['trader'].get('balance', 0):.2f}, Trades: {metrics['trader'].get('trades', 0)}"
        )

if __name__ == "__main__":
    main()
