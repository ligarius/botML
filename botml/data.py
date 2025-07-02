"""Utilities for downloading and storing Binance candlestick data."""

import logging
import sqlite3
import time

import pandas as pd
import requests

from .utils import load_config, setup_logging

CONFIG = load_config()
LOGGER = setup_logging(CONFIG, __name__)


class BinanceAPIError(Exception):
    """Custom exception for Binance API errors."""
    pass

BINANCE_API = CONFIG.get("api_url", "https://api.binance.com")
DB_PATH = CONFIG.get("database_path", "binance_1m.db")
SYMBOLS_OVERRIDE = CONFIG.get("symbols") or []
HISTORY_DAYS = CONFIG.get("history_days", 7)
INTERVAL = CONFIG.get("interval", "1m")

# Reuse a single session for all requests
session = requests.Session()

# Default timeout for network operations
TIMEOUT = 10

def get_top_30_symbols():
    """Return the top 30 symbols by volume excluding common stablecoins."""
    try:
        response = session.get(BINANCE_API + "/api/v3/ticker/24hr", timeout=TIMEOUT)
        if response.status_code != 200:
            LOGGER.error("Failed to fetch tickers: %s - %s", response.status_code, response.text)
            return []
        r = response.json()
    except requests.exceptions.RequestException as exc:
        LOGGER.error("Error requesting tickers: %s", exc)
        return []
    except ValueError as exc:
        LOGGER.error("Invalid JSON in ticker response: %s", exc)
        return []

    sorted_tickers = sorted(
        [x for x in r if not x['symbol'].endswith('BUSD') and not x['symbol'].endswith('USDT')],
        key=lambda x: float(x['quoteVolume']), reverse=True
    )
    symbols = [x['symbol'] for x in sorted_tickers[:30]]
    return symbols

def fetch_klines(symbol, interval='1m', limit=1000, start_time=None, end_time=None):
    """Fetch candlestick data for a symbol.

    Raises BinanceAPIError on request failures.
    """
    url = BINANCE_API + "/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    if start_time:
        params['startTime'] = start_time
    if end_time:
        params['endTime'] = end_time

    try:
        response = session.get(url, params=params, timeout=TIMEOUT)
        if response.status_code != 200:
            msg = f"Failed to fetch klines for {symbol}: {response.status_code} - {response.text}"
            LOGGER.error(msg)
            raise BinanceAPIError(msg)
        data = response.json()
    except requests.exceptions.RequestException as exc:
        LOGGER.error("Network error while fetching klines for %s: %s", symbol, exc)
        raise BinanceAPIError(str(exc))
    except ValueError as exc:
        LOGGER.error("Invalid JSON in klines response for %s: %s", symbol, exc)
        raise BinanceAPIError(str(exc))

    return data

def klines_to_df(klines):
    columns = ['open_time', 'open', 'high', 'low', 'close', 'volume',
               'close_time', 'quote_asset_volume', 'num_trades',
               'taker_buy_base', 'taker_buy_quote', 'ignore']
    df = pd.DataFrame(klines, columns=columns)
    # Convert numeric columns to appropriate types
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    return df

def save_to_sqlite(df, symbol, conn):
    table = f"_{symbol}"
    # Remove duplicate rows to avoid primary key conflicts
    df = df.drop_duplicates(subset=["open_time"]).copy()
    df["open_time"] = df["open_time"].astype(str)
    columns = df.columns.tolist()
    placeholders = ",".join(["?"] * len(columns))
    insert_sql = f"INSERT OR IGNORE INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
    conn.executemany(insert_sql, df.astype(object).values.tolist())
    conn.commit()

def initialize_table(conn, symbol):
    table = f"_{symbol}"
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table} (
        open_time TEXT PRIMARY KEY,
        open REAL, high REAL, low REAL, close REAL, volume REAL,
        close_time INTEGER, quote_asset_volume TEXT,
        num_trades INTEGER, taker_buy_base TEXT,
        taker_buy_quote TEXT, ignore TEXT
    )
    """
    conn.execute(create_sql)
    conn.commit()

def interval_to_ms(interval: str) -> int:
    """Return the number of milliseconds represented by a Binance interval."""
    unit = interval[-1]
    num = int(interval[:-1])
    if unit == 'm':
        return num * 60_000
    if unit == 'h':
        return num * 60 * 60_000
    if unit == 'd':
        return num * 24 * 60 * 60_000
    if unit == 'w':
        return num * 7 * 24 * 60 * 60_000
    if unit == 'M':
        return num * 30 * 24 * 60 * 60_000
    raise ValueError(f"Unknown interval: {interval}")

def download_and_store_all():
    symbols = SYMBOLS_OVERRIDE or get_top_30_symbols()
    conn = sqlite3.connect(DB_PATH)

    default_start = int((time.time() - HISTORY_DAYS * 24 * 60 * 60) * 1000)
    interval_ms = interval_to_ms(INTERVAL)

    for symbol in symbols:
        LOGGER.info("Downloading %s...", symbol)
        initialize_table(conn, symbol)

        table = f"_{symbol}"
        row = conn.execute(f"SELECT MAX(open_time) FROM {table}").fetchone()
        if row and row[0]:
            last_ts = int(pd.to_datetime(row[0]).value / 1_000_000)
            since = last_ts + interval_ms
        else:
            since = default_start

        now_ms = int(time.time() * 1000)

        while since < now_ms:
            end_ts = since + 1000 * interval_ms
            if end_ts > now_ms:
                end_ts = now_ms

            klines = fetch_klines(symbol, INTERVAL, 1000, start_time=since, end_time=end_ts)
            if not klines:
                break

            df = klines_to_df(klines)
            save_to_sqlite(df, symbol, conn)

            since += 1000 * interval_ms
            time.sleep(0.5)  # avoid hitting API limits

    conn.close()

if __name__ == '__main__':
    download_and_store_all()
