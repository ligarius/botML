import requests
import pandas as pd
import sqlite3
import time

BINANCE_API = 'https://api.binance.com'

# Reuse a single session for all requests
session = requests.Session()

# Default timeout for network operations
TIMEOUT = 10

def get_top_30_symbols():
    # Obtener tickers ordenados por volumen, excluyendo stablecoins comunes
    r = session.get(BINANCE_API + '/api/v3/ticker/24hr', timeout=TIMEOUT).json()
    # Puedes filtrar más según tu preferencia (solo spot, excluir BUSD/USDT)
    sorted_tickers = sorted(
        [x for x in r if not x['symbol'].endswith('BUSD') and not x['symbol'].endswith('USDT')],
        key=lambda x: float(x['quoteVolume']), reverse=True
    )
    symbols = [x['symbol'] for x in sorted_tickers[:30]]
    return symbols

def fetch_klines(symbol, interval='1m', limit=1000, start_time=None, end_time=None):
    url = BINANCE_API + '/api/v3/klines'
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    if start_time:
        params['startTime'] = start_time
    if end_time:
        params['endTime'] = end_time
    data = session.get(url, params=params, timeout=TIMEOUT).json()
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
    symbols = get_top_30_symbols()
    conn = sqlite3.connect('binance_1m.db')

    # Start seven days ago
    start_ts = int((time.time() - 7 * 24 * 60 * 60) * 1000)
    now_ms = int(time.time() * 1000)

    for symbol in symbols:
        print(f"Descargando {symbol}...")
        initialize_table(conn, symbol)
        since = start_ts

        # Loop until we reach current time or no more data
        while since < now_ms:
            end_ts = since + 1000 * 60 * 1000  # request up to 1000 minutes
            if end_ts > now_ms:
                end_ts = now_ms

            klines = fetch_klines(symbol, '1m', 1000, start_time=since, end_time=end_ts)
            if not klines:
                break

            df = klines_to_df(klines)
            save_to_sqlite(df, symbol, conn)

            since += 1000 * 60 * 1000
            time.sleep(0.5)  # No saturar la API

    conn.close()

if __name__ == '__main__':
    download_and_store_all()
