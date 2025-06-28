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
    # Mantener las marcas de tiempo como enteros (ms)
    df['open_time'] = df['open_time'].astype('int64')
    return df

def save_to_sqlite(df, symbol, conn):
    table = f"_{symbol}"
    # Asegurar que open_time se guarda como INTEGER (ms)
    df['open_time'] = df['open_time'].astype('int64')
    df.to_sql(table, conn, if_exists='append', index=False,
              dtype={'open_time': 'INTEGER'})

def initialize_table(conn, symbol):
    table = f"_{symbol}"
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table} (
        open_time INTEGER PRIMARY KEY,
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
    for symbol in symbols:
        print(f"Descargando {symbol}...")
        initialize_table(conn, symbol)
        # Descarga 10.000 velas (10 tramos de 1000)
        since = None
        for _ in range(10):
            klines = fetch_klines(symbol, '1m', 1000, start_time=since)
            if not klines:
                break
            df = klines_to_df(klines)
            save_to_sqlite(df, symbol, conn)
            since = int(df['open_time'].iloc[-1]) + 60_000
            time.sleep(0.5)  # No saturar la API
    conn.close()

if __name__ == '__main__':
    download_and_store_all()
