import pytest
from main import check_api_keys


def test_live_mode_without_keys_raises(memory_logger, monkeypatch):
    logger, _ = memory_logger
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API_SECRET", raising=False)
    config = {"mode": "live", "api_key": "", "api_secret": ""}
    with pytest.raises(SystemExit):
        check_api_keys(config, logger)


def test_live_mode_with_keys_ok(memory_logger, monkeypatch):
    logger, _ = memory_logger
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_SECRET", "s")
    config = {"mode": "live"}
    check_api_keys(config, logger)
