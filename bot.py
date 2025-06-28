import requests
import pandas as pd
import sqlite3
import time

BINANCE_API = 'https://api.binance.com'

def get_top_30_symbols():
    # Obtener tickers ordenados por volumen, excluyendo stablecoins comunes
    r = requests.get(BINANCE_API + '/api/v3/ticker/24hr').json()
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
    data = requests.get(url, params=params).json()
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

def get_latest_timestamp(symbol, conn):
    """Return the newest open_time in milliseconds for the given symbol."""
    table = f"_{symbol}"
    cursor = conn.cursor()
    try:
        row = cursor.execute(f"SELECT MAX(open_time) FROM {table}").fetchone()
    except sqlite3.OperationalError:
        return None
    latest = row[0]
    if latest:
        dt = pd.to_datetime(latest)
        return int(dt.timestamp() * 1000)
    return None

def download_and_store_all():
    symbols = get_top_30_symbols()
    conn = sqlite3.connect('binance_1m.db')
    for symbol in symbols:
        print(f"Descargando {symbol}...")
        initialize_table(conn, symbol)
        # Continuar desde la última vela almacenada
        since = get_latest_timestamp(symbol, conn)
        if since is not None:
            since += 60_000  # empezar en la siguiente vela
        # Descarga 10.000 velas (10 tramos de 1000)
        for _ in range(10):
            klines = fetch_klines(symbol, '1m', 1000, start_time=since)
            if not klines:
                break
            df = klines_to_df(klines)
            save_to_sqlite(df, symbol, conn)
            since = int(df['open_time'].iloc[-1].timestamp() * 1000) + 60_000
            time.sleep(0.5)  # No saturar la API
    conn.close()

if __name__ == '__main__':
    download_and_store_all()
