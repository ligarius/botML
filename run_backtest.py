"""Command line interface to run MultiPairBacktester."""

import argparse
import pandas as pd

from backtest.engine import MultiPairBacktester
from backtest.report import report_console


def main():
    p = argparse.ArgumentParser(description="Run backtest")
    p.add_argument("--symbols", nargs="+", required=True)
    p.add_argument("--csv", nargs="+", required=True, help="CSV files per symbol")
    p.add_argument("--capital", type=float, default=1000.0)
    p.add_argument("--risk", type=float, default=0.01, help="Risk per trade")
    p.add_argument("--min_notional", type=float, default=0.0)
    p.add_argument("--commission", type=float, default=0.0)
    args = p.parse_args()

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
    report_console(list(bt.all_trades()), bt.equity_curve)
    print(f"final_equity: {equity}")


if __name__ == "__main__":
    main()
