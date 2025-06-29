import json
from pathlib import Path

import pandas as pd
import streamlit as st

from botml.utils import load_config

CONFIG = load_config()


def load_equity() -> pd.DataFrame:
    path = Path(CONFIG.get("equity_curve_file", "equity_curve.csv"))
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame({'equity': []})


def load_trades() -> pd.DataFrame:
    path = Path(CONFIG.get("open_trades_file", "open_trades.json"))
    if path.exists():
        with open(path) as fh:
            trades = json.load(fh)
        return pd.DataFrame(trades)
    return pd.DataFrame()


def tail_log(lines: int = 100) -> str:
    path = Path(CONFIG.get("log_file", "bot.log"))
    if path.exists():
        with open(path, "r") as fh:
            return "".join(fh.readlines()[-lines:])
    return ""


st.title("botML Dashboard")

st.subheader("Equity Curve")
eq = load_equity()
if not eq.empty:
    st.line_chart(eq["equity"])
else:
    st.write("No equity data available")

st.subheader("Open Trades")
trades = load_trades()
st.table(trades)

st.subheader("Recent Log Messages")
st.text(tail_log())
