import argparse
import json
import pickle
import time
from pathlib import Path

import pandas as pd

import bot
from live_trading import LiveTrader, Trade
from botml.features import add_features
from botml.utils import load_config, setup_logging


CONFIG = load_config()
LOGGER = setup_logging(CONFIG, __name__)


def load_recent_candles(symbol: str, limit: int = 50) -> pd.DataFrame:
    """Fetch recent klines for a symbol and return as DataFrame."""
    klines = bot.fetch_klines(symbol, CONFIG.get("interval", "1m"), limit=limit)
    df = bot.klines_to_df(klines)
    return df


def load_model(symbol: str):
    """Load model for the symbol or fall back to rf_best.pkl."""
    model_file = Path(f"rf_{symbol.lower()}.pkl")
    if not model_file.exists():
        model_file = Path("rf_best.pkl")
    with open(model_file, "rb") as fh:
        return pickle.load(fh)


def restore_open_trades(trader: LiveTrader) -> None:
    """Load open trades from the configured json file."""
    path = Path(trader.open_trades_file)
    if not path.exists():
        return
    try:
        with open(path) as fh:
            data = json.load(fh)
        trader.open_trades = [Trade(**t) for t in data]
    except Exception:
        LOGGER.warning("Failed to load open trades from %s", path)


def check_manual_closures(trader: LiveTrader, row: pd.Series) -> None:
    """Close trades when stop or take-profit is hit using latest data."""
    high = float(row.get("high", row["close"]))
    low = float(row.get("low", row["close"]))
    for trade in list(trader.open_trades):
        reason = None
        price = None
        if trade.direction == "long":
            if low <= trade.stop:
                reason = "stop"
                price = trade.stop
            elif high >= trade.take_profit:
                reason = "take_profit"
                price = trade.take_profit
        else:
            if high >= trade.stop:
                reason = "stop"
                price = trade.stop
            elif low <= trade.take_profit:
                reason = "take_profit"
                price = trade.take_profit
        if reason:
            trader.close_trade(trade)
            LOGGER.info(
                "Closed %s trade at %.2f due to %s",
                trade.direction,
                price,
                reason,
            )


def trading_cycle(symbol: str, trader: LiveTrader) -> None:
    df = load_recent_candles(symbol)
    df = add_features(df)
    if df.empty:
        LOGGER.warning("No data to process for %s", symbol)
        return
    equity_path = Path(CONFIG.get("equity_curve_file", "equity_curve.csv"))
    if equity_path.exists():
        try:
            eq = pd.read_csv(equity_path)["equity"].iloc[-1]
            trader.update_equity(float(eq))
        except Exception:
            LOGGER.warning("Failed to read equity from %s", equity_path)
    if trader.paused:
        LOGGER.info("Trading is paused - skipping signal evaluation")
        return
    model = load_model(symbol)
    feat_cols = [c for c in df.columns if c not in {"open_time", "label"}]
    last_row = df.iloc[-1]
    check_manual_closures(trader, last_row)
    pred = model.predict(last_row[feat_cols].to_frame().T)[0]
    LOGGER.info("Signal for %s: %s", symbol, pred)
    if pred == 1:
        price = float(last_row["close"])
        trader.open_trade(price, direction="long", bracket=True)
        LOGGER.info("Opened long trade on %s at %.2f", symbol, price)


def run_loop(interval: int = 60) -> None:
    symbol = (CONFIG.get("symbols") or ["BTCUSDT"])[0]
    trader = LiveTrader(symbol, account_size=1000)
    restore_open_trades(trader)
    while True:
        start = time.time()
        LOGGER.info("--- Cycle start ---")
        try:
            trading_cycle(symbol, trader)
        except Exception as exc:
            LOGGER.exception("Error in cycle: %s", exc)
        LOGGER.info("--- Cycle end ---")
        elapsed = time.time() - start
        if elapsed < interval:
            time.sleep(interval - elapsed)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run realtime trading loop")
    parser.add_argument("--interval", type=int, default=60,
                        help="Seconds between cycles")
    args = parser.parse_args()
    run_loop(args.interval)


if __name__ == "__main__":
    main()
