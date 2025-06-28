import requests
import pandas as pd
import sqlite3
import time

BINANCE_API = 'https://api.binance.com'

def get_top_30_symbols(retries: int = 3, delay: int = 2):
    """Return a list of the 30 highest volume symbols on Binance."""
    url = BINANCE_API + '/api/v3/ticker/24hr'
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                tickers = resp.json()
                break
            else:
                print(f"Attempt {attempt}/{retries} failed with status {resp.status_code}")
        except requests.RequestException as exc:
            print(f"Attempt {attempt}/{retries} failed: {exc}")
        time.sleep(delay)
    else:
        print("Failed to fetch tickers after multiple attempts.")
        return []

    sorted_tickers = sorted(
        [x for x in tickers if not x['symbol'].endswith('BUSD') and not x['symbol'].endswith('USDT')],
        key=lambda x: float(x['quoteVolume']),
        reverse=True,
    )
    return [x['symbol'] for x in sorted_tickers[:30]]

def fetch_klines(symbol, interval: str = '1m', limit: int = 1000,
                 start_time: int | None = None, end_time: int | None = None,
                 retries: int = 3, delay: int = 2):
    url = BINANCE_API + '/api/v3/klines'
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    if start_time:
        params['startTime'] = start_time
    if end_time:
        params['endTime'] = end_time

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(
                    f"Attempt {attempt}/{retries} to fetch klines for {symbol} failed with status {resp.status_code}"
                )
        except requests.RequestException as exc:
            print(f"Attempt {attempt}/{retries} to fetch klines for {symbol} failed: {exc}")
        time.sleep(delay)

    print(f"Failed to fetch klines for {symbol} after {retries} attempts.")
    return []

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
    df.to_sql(table, conn, if_exists='append', index=False)

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
            end_ts = since + 1000 * 60  # request up to 1000 minutes
            if end_ts > now_ms:
                end_ts = now_ms

            klines = fetch_klines(symbol, '1m', 1000, start_time=since, end_time=end_ts)
            if not klines:
                break

            df = klines_to_df(klines)
            save_to_sqlite(df, symbol, conn)

            since = int(df['open_time'].iloc[-1].timestamp() * 1000) + 60_000
            time.sleep(0.5)  # No saturar la API

    conn.close()

if __name__ == '__main__':
    download_and_store_all()
