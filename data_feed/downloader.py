"""Utilities for downloading and reading market data from Binance."""

import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv


class DataFeed:
    """Handle the retrieval and storage of candlestick data."""

    def __init__(self, config, logger):
        """Create a new data feed manager.

        Parameters
        ----------
        config : dict
            Configuration with ``api_url``, ``symbols`` and ``interval`` keys.
        logger : logging.Logger
            Logger used to report progress and errors.
        """

        self.config = config
        self.logger = logger
        if os.path.exists(".env"):
            load_dotenv(".env")
        self.api_url = config["api_url"]
        self.symbols = config["symbols"]
        self.interval = config["interval"]
        self.api_key = os.environ.get("API_KEY", config.get("api_key"))
        self.api_secret = os.environ.get("API_SECRET", config.get("api_secret"))
        self.max_retries = config.get("download_retries", 3)
        self.timeout = config.get("request_timeout", 10)

    def update(self):
        """Download the most recent candles for all symbols and store them.

        Saved CSV files include a ``symbol`` column for easier merging of
        multiple data sets.
        """

        for symbol in self.symbols:
            df = self._fetch_binance_klines(symbol)
            if df.empty:
                self.logger.warning(
                    f"No se recibieron velas para {symbol}; se omite guardado"
                )
                continue

            if "symbol" not in df.columns:
                df["symbol"] = symbol

            df.to_csv(f"{symbol}_{self.interval}.csv", index=False)
            self.logger.info(f"Actualizadas velas para {symbol}")

    def _fetch_binance_klines(self, symbol, limit=1000):
        """Request kline data for a symbol.

        Parameters
        ----------
        symbol : str
            Market symbol to download.
        limit : int, optional
            Number of klines to request, by default ``1000``.

        Returns
        -------
        pandas.DataFrame
            Data frame with kline information. On success it includes a
            ``symbol`` column with the requested market name. An empty frame is
            returned on error.
        """

        endpoint = "/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": self.interval,
            "limit": limit,
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(
                    self.api_url + endpoint,
                    params=params,
                    timeout=self.timeout,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    df = pd.DataFrame(
                        data,
                        columns=[
                            "open_time",
                            "open",
                            "high",
                            "low",
                            "close",
                            "volume",
                            "close_time",
                            "quote_asset_volume",
                            "number_of_trades",
                            "taker_buy_base",
                            "taker_buy_quote",
                            "ignore",
                        ],
                    )
                    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
                    df["close_time"] = pd.to_datetime(
                        df["close_time"], unit="ms"
                    )
                    # Include the symbol so downstream consumers know the market
                    df["symbol"] = symbol
                    return df
                self.logger.warning(
                    f"Intento {attempt}: respuesta {resp.status_code} al descargar velas"
                )
            except requests.RequestException as exc:
                self.logger.warning(f"Intento {attempt}: error descargando velas: {exc}")

        self.logger.error(
            f"Error descargando velas para {symbol} tras {self.max_retries} intentos"
        )
        return pd.DataFrame()

    def latest_data(self):
        """Return the latest downloaded data for each symbol.

        Returns
        -------
        list[pandas.DataFrame]
            List of data frames for every configured symbol.
        """

        dfs = []
        for symbol in self.symbols:
            try:
                df = pd.read_csv(f"{symbol}_{self.interval}.csv")
                dfs.append(df)
            except FileNotFoundError:
                dfs.append(pd.DataFrame())
        return dfs

    def history(self):
        """Return historical data used for training.

        Currently this simply returns :meth:`latest_data`, but in a real
        implementation this could aggregate multiple files or query a database.

        Returns
        -------
        list[pandas.DataFrame]
            Training data frames.
        """

        # Para entrenamiento puedes concatenar varios CSVs, cargar desde DB, etc.
        return self.latest_data()
