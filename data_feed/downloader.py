import requests
import pandas as pd
from datetime import datetime

class DataFeed:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.api_url = config["api_url"]
        self.symbols = config["symbols"]
        self.interval = config["interval"]

    def update(self):
        for symbol in self.symbols:
            df = self._fetch_binance_klines(symbol)
            df.to_csv(f"{symbol}_{self.interval}.csv", index=False)
            self.logger.info(f"Actualizadas velas para {symbol}")

    def _fetch_binance_klines(self, symbol, limit=1000):
        endpoint = "/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": self.interval,
            "limit": limit
        }
        resp = requests.get(self.api_url + endpoint, params=params)
        if resp.status_code == 200:
            data = resp.json()
            df = pd.DataFrame(data, columns=[
                "open_time","open","high","low","close","volume",
                "close_time","quote_asset_volume","number_of_trades",
                "taker_buy_base","taker_buy_quote","ignore"
            ])
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
            return df
        else:
            self.logger.error(f"Error descargando velas: {resp.text}")
            return pd.DataFrame()
        
    def latest_data(self):
        dfs = []
        for symbol in self.symbols:
            try:
                df = pd.read_csv(f"{symbol}_{self.interval}.csv")
                dfs.append(df)
            except FileNotFoundError:
                dfs.append(pd.DataFrame())
        return dfs

    def history(self):
        # Para entrenamiento puedes concatenar varios CSVs, cargar desde DB, etc.
        return self.latest_data()
