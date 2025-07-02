from trading.simulation import Simulator


def test_simulator_logs_and_updates_balance(memory_logger):
    logger, stream = memory_logger
    sim = Simulator({"trade_size": 1}, logger)
    start = sim.balance
    sim.simulate([{"price": 100, "symbol": "T", "side": "BUY"}])
    assert sim.balance < start
    assert "Modo: Simulado" in stream.getvalue()
