"""Unified command-line interface for botML."""

from __future__ import annotations

import argparse
import os
import runpy
from pathlib import Path

from botml.utils import load_config


# ------------------------------- command handlers -----------------------------


def run_train_model(_: argparse.Namespace) -> None:
    """Execute ``train_model.py``."""
    runpy.run_module("train_model", run_name="__main__")


def run_hyperopt(args: argparse.Namespace) -> None:
    """Execute ``hyperoptimize.py`` using the provided configuration."""
    config = load_config()
    import hyperoptimize

    hyperoptimize.DB_PATH = config.get("database_path", "binance_1m.db")
    hyperoptimize.SYMBOL = (config.get("symbols") or ["BTCUSDT"])[0]
    model = hyperoptimize.optimize_model()
    with open("rf_best.pkl", "wb") as fh:
        import pickle

        pickle.dump(model, fh)
    print("Saved best model to rf_best.pkl")


def run_backtest(args: argparse.Namespace) -> None:
    """Replicate ``run_backtest.py``."""
    from pathlib import Path
    import sqlite3
    import pandas as pd
    from backtest.engine import MultiPairBacktester
    from backtest.report import report_summary_console

    if len(args.symbols) != len(args.csv):
        raise ValueError(
            f"Number of symbols ({len(args.symbols)}) does not match number of CSV files ({len(args.csv)})"
        )

    for symbol, path in zip(args.symbols, args.csv):
        csv_path = Path(path)
        if not csv_path.is_file():
            if not args.db_path:
                raise FileNotFoundError(f"CSV file not found: {path}")
            query = (
                f"SELECT open_time, open, high, low, close, volume FROM _{symbol}"
            )
            with sqlite3.connect(args.db_path) as conn:
                df = pd.read_sql(query, conn)
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(csv_path, index=False)
            print(f"created {csv_path} from table _{symbol}")

    data = {sym: pd.read_csv(path) for sym, path in zip(args.symbols, args.csv)}

    def strat(row, symbol):
        return "long" if row.name == 0 else None

    bt = MultiPairBacktester(
        data,
        strat,
        initial_capital=args.capital,
        risk_per_trade=args.risk,
        min_notional=args.min_notional,
        commission_pct=args.commission,
    )
    equity = bt.run()
    report_summary_console(list(bt.all_trades()), bt.equity_curve)
    print(f"final_equity: {equity}")


def run_research_loop(_: argparse.Namespace) -> None:
    """Start the research loop."""
    import research_loop

    research_loop.main_loop()


def run_realtime_loop(args: argparse.Namespace) -> None:
    """Start realtime trading loop."""
    import realtime_loop

    realtime_loop.run_loop(args.interval)


def run_orchestrator(args: argparse.Namespace) -> None:
    """Replicate ``orchestrator.py`` CLI."""
    import orchestrator

    # Recreate the behaviour of orchestrator.main
    config = load_config()
    logger = orchestrator.setup_logging(config, __name__)

    logger.info("Starting data download")
    import bot

    bot.download_and_store_all()

    db_path = config.get("database_path", "binance_1m.db")
    symbols = config.get("symbols") or ["BTCUSDT"]
    data = {}
    for sym in symbols:
        df = orchestrator.load_price_data(db_path, sym)
        df = orchestrator.generate_features_and_labels(config, df)
        data[sym] = df

    train_df = pd.concat(data.values(), ignore_index=True)

    model_path = Path("rf_best.pkl" if args.hyperopt else "rf_model.pkl")
    if args.hyperopt:
        model = orchestrator.hyperopt_random_forest(train_df, model_path)
    else:
        model = orchestrator.train_random_forest(train_df, model_path)

    commission_pct = float(config.get("commission_pct", 0.0))
    equity, metrics, trades = orchestrator.backtest_model(
        data, model, commission_pct=commission_pct
    )

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
        orchestrator.run_live_trading(
            last_sym,
            float(data[last_sym].iloc[-1]["close"]),
            model,
            data[last_sym].iloc[-1],
        )

    summary = {
        "symbols": ",".join(symbols),
        "final_equity": round(equity, 2),
        "model": str(model_path),
    }
    with open(args.report, "w", newline="") as fh:
        import csv
        import json

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


def run_live_trading(args: argparse.Namespace) -> None:
    """Open a single trade using :class:`LiveTrader`."""
    from live_trading import LiveTrader, PositionSizer, RiskManager

    config = load_config()
    symbol = args.symbol or (config.get("symbols") or ["BTCUSDT"])[0]
    trader = LiveTrader(
        symbol,
        account_size=args.account_size,
        sizer=PositionSizer(args.account_size, risk_per_trade=args.risk),
        risk_manager=RiskManager(args.account_size, max_drawdown_pct=args.drawdown),
    )
    trader.open_trade(price=args.price, direction=args.direction, bracket=True)


# ---------------------------------- parser ------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="botML command line interface")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("train-model", help="Train model").set_defaults(func=run_train_model)
    sub.add_parser("hyperopt", help="Hyperparameter search").set_defaults(func=run_hyperopt)

    p_bt = sub.add_parser("backtest", help="Run simple backtest")
    p_bt.add_argument("--symbols", nargs="+", required=True)
    p_bt.add_argument("--csv", nargs="+", required=True)
    p_bt.add_argument("--capital", type=float, default=1000.0)
    p_bt.add_argument("--risk", type=float, default=0.01)
    p_bt.add_argument("--min_notional", type=float, default=0.0)
    p_bt.add_argument("--commission", type=float, default=0.0)
    p_bt.add_argument("--db-path")
    p_bt.set_defaults(func=run_backtest)

    sub.add_parser("research-loop", help="Run offline research loop").set_defaults(func=run_research_loop)

    p_rt = sub.add_parser("realtime-loop", help="Run realtime trading loop")
    p_rt.add_argument("--interval", type=int, default=60)
    p_rt.set_defaults(func=run_realtime_loop)

    p_orch = sub.add_parser("orchestrator", help="Full workflow orchestrator")
    p_orch.add_argument("--hyperopt", action="store_true")
    p_orch.add_argument("--live", action="store_true")
    p_orch.add_argument("--report", default="orchestrator_report.txt")
    p_orch.set_defaults(func=run_orchestrator)

    p_live = sub.add_parser("live-trading", help="Open a single live trade")
    p_live.add_argument("--price", type=float, required=True)
    p_live.add_argument("--symbol")
    p_live.add_argument("--direction", choices=["long", "short"], default="long")
    p_live.add_argument("--account-size", type=float, default=1000.0)
    p_live.add_argument("--risk", type=float, default=0.02)
    p_live.add_argument("--drawdown", type=float, default=0.1)
    p_live.set_defaults(func=run_live_trading)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    os.environ["BOTML_CONFIG"] = str(Path(args.config))
    args.func(args)


if __name__ == "__main__":
    main()
