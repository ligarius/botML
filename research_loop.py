import json
import time
from pathlib import Path

import pandas as pd

import bot
from orchestrator import (
    load_price_data,
    generate_features_and_labels,
    train_random_forest,
    backtest_model,
)
from botml.utils import load_config, setup_logging


def main_loop() -> None:
    config = load_config()
    logger = setup_logging(config, __name__)
    update_interval = int(config.get("update_interval", 900))
    db_path = config.get("database_path", "binance_1m.db")
    symbols = config.get("symbols") or ["BTCUSDT"]

    while True:
        start = time.time()
        try:
            bot.download_and_store_all()

            data = {}
            for sym in symbols:
                df = load_price_data(db_path, sym)
                df = generate_features_and_labels(config, df)
                data[sym] = df

            train_df = pd.concat(data.values(), ignore_index=True)
            model = train_random_forest(train_df, Path("rf_loop.pkl"))

            equity, metrics, _ = backtest_model(
                data,
                model,
                commission_pct=float(config.get("commission_pct", 0.0)),
            )

            feat_cols = [c for c in train_df.columns if c not in {"label", "open_time"}]
            predictions = {}
            for sym, df_sym in data.items():
                last_row = df_sym.iloc[-1]
                pred = int(model.predict(last_row[feat_cols].to_frame().T)[0])
                predictions[sym] = pred

            Path("predictions.json").write_text(json.dumps(predictions))
            Path("metrics.json").write_text(json.dumps(metrics))
        except Exception as exc:  # pragma: no cover - loop resilience
            logger.exception("Research loop error: %s", exc)
        elapsed = time.time() - start
        if elapsed < update_interval:
            time.sleep(update_interval - elapsed)


if __name__ == "__main__":
    main_loop()
