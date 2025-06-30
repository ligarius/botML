"""Helper routines for backtesting."""

from datetime import datetime
from typing import Any

import pandas as pd


def parse_date(s: str) -> datetime:
    return pd.to_datetime(s).to_pydatetime()


def to_timestamp(dt: datetime) -> str:
    return dt.isoformat()


def log(msg: str):
    print(msg)
