"""Command line interface to run MultiPairBacktester."""

import argparse
from pathlib import Path
import pandas as pd

from backtest.engine import MultiPairBacktester
from backtest.report import report_summary_console


def main():
    p = argparse.ArgumentParser(
        description="Run backtest on multiple symbols."
    )
    p.add_argument("--symbols", nargs="+", required=True, help="Symbols to backtest")
    p.add_argument(
        "--csv",
        nargs="+",
        required=True,
        help="CSV file for each symbol (must match --symbols)",
    )
    p.add_argument("--capital", type=float, default=1000.0)
    p.add_argument("--risk", type=float, default=0.01, help="Risk per trade")
    p.add_argument("--min_notional", type=float, default=0.0)
    p.add_argument("--commission", type=float, default=0.0)
    p.add_argument(
        "--db-path",
        help="Optional path to binance_1m.db for auto-exporting missing CSVs",
    )
    args = p.parse_args()

    if len(args.symbols) != len(args.csv):
        raise ValueError(
            f"Number of symbols ({len(args.symbols)}) does not match number of CSV files ({len(args.csv)})"
        )

    for symbol, path in zip(args.symbols, args.csv):
        csv_path = Path(path)
        if not csv_path.is_file():
            if not args.db_path:
                raise FileNotFoundError(f"CSV file not found: {path}")
            import sqlite3

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


if __name__ == "__main__":
    main()
