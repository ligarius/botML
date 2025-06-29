import requests
import pandas as pd
import sqlite3
import time
import logging
from pathlib import Path
import yaml

# Load configuration from config.yaml located next to this script
with open(Path(__file__).resolve().parent / 'config.yaml', 'r') as fh:
    CONFIG = yaml.safe_load(fh)

# Configure logging to both console and file
level_name = CONFIG.get('log_level', 'INFO').upper()
log_file = CONFIG.get('log_file', 'bot.log')
logging.basicConfig(
    level=getattr(logging, level_name, logging.INFO),
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)


class BinanceAPIError(Exception):
    """Custom exception for Binance API errors."""
    pass

BINANCE_API = CONFIG.get('api_url', 'https://api.binance.com')
DB_PATH = CONFIG.get('database_path', 'binance_1m.db')
SYMBOLS_OVERRIDE = CONFIG.get('symbols') or []
HISTORY_DAYS = CONFIG.get('history_days', 7)
INTERVAL = CONFIG.get('interval', '1m')

# Reuse a single session for all requests
session = requests.Session()

# Default timeout for network operations
TIMEOUT = 10

def get_top_30_symbols():
    """Return the top 30 symbols by volume excluding common stablecoins."""
    try:
        response = session.get(BINANCE_API + '/api/v3/ticker/24hr', timeout=TIMEOUT)
        if response.status_code != 200:
            logging.error("Failed to fetch tickers: %s - %s", response.status_code, response.text)
            return []
        r = response.json()
    except requests.exceptions.RequestException as exc:
        logging.error("Error requesting tickers: %s", exc)
        return []
    except ValueError as exc:
        logging.error("Invalid JSON in ticker response: %s", exc)
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
    url = BINANCE_API + '/api/v3/klines'
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    if start_time:
        params['startTime'] = start_time
    if end_time:
        params['endTime'] = end_time

    try:
        response = session.get(url, params=params, timeout=TIMEOUT)
        if response.status_code != 200:
            msg = f"Failed to fetch klines for {symbol}: {response.status_code} - {response.text}"
            logging.error(msg)
            raise BinanceAPIError(msg)
        data = response.json()
    except requests.exceptions.RequestException as exc:
        logging.error("Network error while fetching klines for %s: %s", symbol, exc)
        raise BinanceAPIError(str(exc))
    except ValueError as exc:
        logging.error("Invalid JSON in klines response for %s: %s", symbol, exc)
        raise BinanceAPIError(str(exc))

    return data

def klines_to_df(klines):
    columns = ['open_time', 'open', 'high', 'low', 'close', 'volume',
               'close_time', 'quote_asset_volume', 'num_trades',
               'taker_buy_base', 'taker_buy_quote', 'ignore']
    df = pd.DataFrame(klines, columns=columns)
    # Convierte los tipos a float/integers útiles
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

def download_and_store_all():
    symbols = SYMBOLS_OVERRIDE or get_top_30_symbols()
    conn = sqlite3.connect(DB_PATH)

    # Start HISTORY_DAYS days ago
    start_ts = int((time.time() - HISTORY_DAYS * 24 * 60 * 60) * 1000)
    now_ms = int(time.time() * 1000)

    for symbol in symbols:
        logging.info("Downloading %s...", symbol)
        initialize_table(conn, symbol)
        since = start_ts

        # Loop until we reach current time or no more data
        while since < now_ms:
            end_ts = since + 1000 * 60 * 1000  # request up to 1000 minutes
            if end_ts > now_ms:
                end_ts = now_ms

            klines = fetch_klines(symbol, INTERVAL, 1000, start_time=since, end_time=end_ts)
            if not klines:
                break

            df = klines_to_df(klines)
            save_to_sqlite(df, symbol, conn)

            since += 1000 * 60 * 1000
            time.sleep(0.5)  # No saturar la API

    conn.close()

if __name__ == '__main__':
    download_and_store_all()
