import pandas as pd
import numpy as np

def add_features(df):
    # Asume columnas: ['open_time', 'open', 'high', 'low', 'close', 'volume']
    
    # 1. Retornos
    df['return_1m'] = df['close'].pct_change(1)
    df['return_5m'] = df['close'].pct_change(5)
    df['return_10m'] = df['close'].pct_change(10)

    # 2. Medias móviles
    for window in [5, 10, 20]:
        df[f'SMA_{window}'] = df['close'].rolling(window).mean()
        df[f'EMA_{window}'] = df['close'].ewm(span=window).mean()

    # 3. Volatilidad local
    df['STD_10'] = df['close'].rolling(10).std()
    df['STD_20'] = df['close'].rolling(20).std()

    # 4. RSI (fórmula manual para evitar dependencias externas)
    window = 14
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.rolling(window).mean()
    ma_down = down.rolling(window).mean()
    rs = ma_up / (ma_down + 1e-9)
    df['RSI_14'] = 100 - (100 / (1 + rs))

    # 5. ATR (Average True Range)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['ATR_14'] = true_range.rolling(14).mean()

    # 6. MACD (12-26-9)
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9).mean()

    # 7. Volumen Z-Score
    df['volume_zscore_30'] = (df['volume'] - df['volume'].rolling(30).mean()) / (df['volume'].rolling(30).std() + 1e-9)

    # 8. Máximos y mínimos recientes
    df['max_20'] = df['high'].rolling(20).max()
    df['min_20'] = df['low'].rolling(20).min()

    # 9. Patrones de vela simple
    df['bullish_candle'] = (df['close'] > df['open']).astype(int)
    df['bearish_candle'] = (df['close'] < df['open']).astype(int)

    # 10. Drop primeras filas con NaN (por rolling)
    df = df.dropna().reset_index(drop=True)
    return df

# Ejemplo de uso:
# conn = sqlite3.connect('binance_1m.db')
# df = pd.read_sql('SELECT * FROM _BTCUSDT', conn)
# df = add_features(df)
