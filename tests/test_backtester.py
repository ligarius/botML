from backtest.engine import Backtester


def test_backtester_run_logs_message(memory_logger):
    logger, stream = memory_logger
    bt = Backtester({}, logger)
    bt.run()
    assert "Backtest: simulando" in stream.getvalue()
