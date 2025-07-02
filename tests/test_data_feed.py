import os
import pandas as pd
import requests
from data_feed.downloader import DataFeed


def test_latest_data_returns_empty_when_file_missing(tmp_path, memory_logger, monkeypatch):
    logger, stream = memory_logger
    config = {"api_url": "", "symbols": ["TEST"], "interval": "1m"}
    feed = DataFeed(config, logger)
    monkeypatch.chdir(tmp_path)
    data = feed.latest_data()
    assert len(data) == 1
    assert data[0].empty


def test_fetch_binance_klines_error(monkeypatch, memory_logger):
    logger, stream = memory_logger
    config = {"api_url": "https://example.com", "symbols": ["BTCUSDT"], "interval": "1m", "download_retries": 1}
    feed = DataFeed(config, logger)

    def fake_get(*args, **kwargs):
        raise requests.RequestException("fail")

    monkeypatch.setattr(requests, "get", fake_get)
    df = feed._fetch_binance_klines("BTCUSDT")
    assert df.empty
    assert "Error descargando velas" in stream.getvalue()


def test_update_and_latest_data_include_symbol(tmp_path, memory_logger, monkeypatch):
    logger, _ = memory_logger
    config = {"api_url": "", "symbols": ["AAA"], "interval": "1m"}
    feed = DataFeed(config, logger)
    monkeypatch.chdir(tmp_path)

    def fake_fetch(self, symbol, limit=1000):
        return pd.DataFrame(
            {
                "open_time": [0],
                "open": [0],
                "high": [0],
                "low": [0],
                "close": [0],
                "volume": [0],
                "close_time": [0],
                "quote_asset_volume": [0],
                "number_of_trades": [0],
                "taker_buy_base": [0],
                "taker_buy_quote": [0],
                "ignore": [0],
                "symbol": [symbol],
            }
        )

    monkeypatch.setattr(DataFeed, "_fetch_binance_klines", fake_fetch, raising=False)
    feed.update()
    df = feed.latest_data()[0]
    assert "symbol" in df.columns
    assert df["symbol"].iloc[0] == "AAA"
