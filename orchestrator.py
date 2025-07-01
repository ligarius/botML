import argparse
import csv
import json
import logging
import pickle
import sqlite3
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV

import bot
from typing import Tuple, Dict

from backtest import MultiPairBacktester, compute_metrics
from live_trading import LiveTrader
from botml.features import add_features
from botml.labeling import create_labels
from botml.utils import load_config, setup_logging


def load_price_data(db_path: str, symbol: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    table = f"_{symbol}"
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    conn.close()
    return df


def generate_features_and_labels(config: dict, df: pd.DataFrame) -> pd.DataFrame:
    """Add features and labels using configuration options."""
    horizon = int(config.get("label_horizon", 5))
    threshold = float(config.get("label_threshold", 0.002))
    df = add_features(df)
    df = create_labels(df, horizon=horizon, threshold=threshold)
    return df


def train_random_forest(df: pd.DataFrame, model_path: Path) -> RandomForestClassifier:
    features = [c for c in df.columns if c not in {'label', 'open_time'}]
    X = df[features]
    y = df['label']
    split = int(len(df) * 0.7)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X.iloc[:split], y.iloc[:split])
    pickle.dump(clf, open(model_path, 'wb'))
    logger = logging.getLogger(__name__)
    logger.info("Model saved to %s", model_path)
    return clf


def hyperopt_random_forest(df: pd.DataFrame, model_path: Path) -> RandomForestClassifier:
    features = [c for c in df.columns if c not in {'label', 'open_time'}]
    X = df[features]
    y = df['label']
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [None, 5, 10],
    }
    base_model = RandomForestClassifier(random_state=42)
    search = GridSearchCV(base_model, param_grid=param_grid, cv=3, n_jobs=-1)
    search.fit(X, y)
    best = search.best_estimator_
    pickle.dump(best, open(model_path, 'wb'))
    logger = logging.getLogger(__name__)
    logger.info("Best model saved to %s", model_path)
    return best


def backtest_model(
    data: Dict[str, pd.DataFrame],
    model: RandomForestClassifier,
    commission_pct: float = 0.0,
) -> Tuple[float, dict, list]:
    sample_df = next(iter(data.values()))
    feat_cols = [c for c in sample_df.columns if c not in {"label", "open_time"}]

    def strategy(row, sym):
        pred = model.predict(row[feat_cols].to_frame().T)[0]
        return "long" if pred == 1 else None

    bt = MultiPairBacktester(data, strategy, commission_pct=commission_pct)
    equity = bt.run()
    trades = list(bt.all_trades())
    metrics = compute_metrics(trades, bt.equity_curve)
    logger = logging.getLogger(__name__)
    logger.info("Backtest finished with equity %.2f", equity)
    return equity, metrics, trades


def run_live_trading(symbol: str, price: float, model: RandomForestClassifier, last_row: pd.Series):
    feat_cols = [c for c in last_row.index if c not in {'label', 'open_time'}]
    pred = model.predict(last_row[feat_cols].to_frame().T)[0]
    if pred == 1:
        trader = LiveTrader(symbol, account_size=1000)
        trader.open_trade(price, direction='long')
        logger = logging.getLogger(__name__)
        logger.info("Live trade opened at price %.2f", price)


def main():
    parser = argparse.ArgumentParser(description="Run the botML workflow")
    parser.add_argument('--hyperopt', action='store_true', help='Use hyperparameter optimization')
    parser.add_argument('--live', action='store_true', help='Launch live trading after backtest')
    parser.add_argument('--report', default='orchestrator_report.txt', help='Path to save the report file')
    args = parser.parse_args()

    config = load_config()
    logger = setup_logging(config, __name__)

    logger.info("Starting data download")
    bot.download_and_store_all()

    db_path = config.get('database_path', 'binance_1m.db')
    symbols = config.get('symbols') or ['BTCUSDT']
    data: Dict[str, pd.DataFrame] = {}
    for sym in symbols:
        df = load_price_data(db_path, sym)
        df = generate_features_and_labels(config, df)
        data[sym] = df

    train_df = pd.concat(data.values(), ignore_index=True)

    model_path = Path('rf_best.pkl' if args.hyperopt else 'rf_model.pkl')
    if args.hyperopt:
        model = hyperopt_random_forest(train_df, model_path)
    else:
        model = train_random_forest(train_df, model_path)

    commission_pct = float(config.get('commission_pct', 0.0))
    equity, metrics, trades = backtest_model(data, model, commission_pct=commission_pct)

    start_equity = equity - metrics.get("pnl", 0.0)
    roi = metrics.get("pnl", 0.0) / start_equity if start_equity else 0.0

    logger.info("Backtested symbols %s", ", ".join(symbols))
    for t in trades:
        logger.info(
            "Trade %s %s -> %s entry %.2f exit %.2f pnl %.2f",
            t.symbol,
            t.entry_time,
            t.exit_time,
            t.entry_price,
            t.exit_price,
            t.pnl(),
        )

    logger.info(
        "ROI: %.2f%% | Profit factor: %.2f | Sharpe: %.2f | Drawdown: %.2f",
        roi * 100,
        metrics.get("profit_factor", 0.0),
        metrics.get("sharpe", 0.0),
        metrics.get("max_drawdown", 0.0),
    )

    if args.live:
        last_sym = symbols[0]
        run_live_trading(last_sym, float(data[last_sym].iloc[-1]['close']), model, data[last_sym].iloc[-1])

    summary = {
        "symbols": ",".join(symbols),
        "final_equity": round(equity, 2),
        "model": str(model_path),
    }
    with open(args.report, "w", newline="") as fh:
        if args.report.endswith(".json"):
            json.dump(summary, fh)
        elif args.report.endswith(".csv"):
            writer = csv.DictWriter(fh, fieldnames=summary.keys())
            writer.writeheader()
            writer.writerow(summary)
        else:
            for k, v in summary.items():
                fh.write(f"{k}: {v}\n")
    logger.info("Report written to %s", args.report)


if __name__ == '__main__':
    main()
