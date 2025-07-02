from trading.simulation import Simulator


def test_simulator_logs_and_updates_balance(memory_logger):
    logger, stream = memory_logger
    sim = Simulator({}, logger)
    start = sim.balance
    sim.simulate([{"price": 100, "symbol": "T"}])
    assert sim.balance < start
    assert "Simulaci" in stream.getvalue()
