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
from backtest import Backtester
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


def generate_features_and_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = add_features(df)
    df = create_labels(df)
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


def backtest_model(df: pd.DataFrame, model: RandomForestClassifier, commission_pct: float = 0.0) -> float:
    feat_cols = [c for c in df.columns if c not in {'label', 'open_time'}]

    def strategy(row):
        pred = model.predict(row[feat_cols].to_frame().T)[0]
        return 'long' if pred == 1 else None

    bt = Backtester(df, strategy, commission_pct=commission_pct)
    equity = bt.run()
    logger = logging.getLogger(__name__)
    logger.info("Backtest finished with equity %.2f", equity)
    return equity


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
    symbol = (config.get('symbols') or ['BTCUSDT'])[0]
    df = load_price_data(db_path, symbol)
    df = generate_features_and_labels(df)

    model_path = Path('rf_best.pkl' if args.hyperopt else f'rf_{symbol.lower()}.pkl')
    if args.hyperopt:
        model = hyperopt_random_forest(df, model_path)
    else:
        model = train_random_forest(df, model_path)

    commission_pct = float(config.get('commission_pct', 0.0))
    equity = backtest_model(df, model, commission_pct=commission_pct)

    if args.live:
        run_live_trading(symbol, float(df.iloc[-1]['close']), model, df.iloc[-1])

    summary = {
        "symbol": symbol,
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
