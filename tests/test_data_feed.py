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


def test_update_creates_csv_from_request(tmp_path, memory_logger, monkeypatch):
    """DataFeed.update should save klines returned via requests.get."""
    logger, _ = memory_logger
    config = {"api_url": "http://test", "symbols": ["BBB"], "interval": "1m"}
    feed = DataFeed(config, logger)
    monkeypatch.chdir(tmp_path)

    sample_payload = [
        [
            0,
            "1",
            "2",
            "0.5",
            "1.5",
            "100",
            1,
            "200",
            10,
            "50",
            "75",
            "0",
        ]
    ]

    class FakeResponse:
        status_code = 200

        def json(self):
            return sample_payload

    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse())

    feed.update()
    file_path = tmp_path / "BBB_1m.csv"
    assert file_path.exists()
    df = pd.read_csv(file_path)
    expected_cols = [
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
        "symbol",
    ]
    assert list(df.columns) == expected_cols
    assert df["symbol"].iloc[0] == "BBB"


def test_update_skips_empty_dataframe(tmp_path, memory_logger, monkeypatch):
    """DataFeed.update should not create a CSV when no data is returned."""
    logger, _ = memory_logger
    config = {"api_url": "", "symbols": ["EMPTY"], "interval": "1m"}
    feed = DataFeed(config, logger)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        DataFeed, "_fetch_binance_klines", lambda *a, **k: pd.DataFrame(), raising=False
    )

    feed.update()
    assert not (tmp_path / "EMPTY_1m.csv").exists()


def test_env_file_overrides_config(tmp_path, memory_logger, monkeypatch):
    """Environment variables from a .env file should override config values."""
    logger, _ = memory_logger
    env_path = tmp_path / ".env"
    env_path.write_text("API_KEY=envkey\nAPI_SECRET=envsecret\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API_SECRET", raising=False)
    config = {
        "api_url": "",
        "symbols": ["T"],
        "interval": "1m",
        "api_key": "cfg",
        "api_secret": "cfg",
    }
    feed = DataFeed(config, logger)
    assert feed.api_key == "envkey"
    assert feed.api_secret == "envsecret"
