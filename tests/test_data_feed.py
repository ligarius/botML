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
