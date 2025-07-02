import pandas as pd
from models.manager import ModelManager


def test_need_retrain_when_no_model(memory_logger):
    logger, _ = memory_logger
    mm = ModelManager({}, logger)
    mm.model = None
    assert mm.need_retrain()


def test_retrain_creates_model(tmp_path, memory_logger):
    logger, _ = memory_logger
    mm = ModelManager({}, logger)
    mm.model_path = str(tmp_path / "model.pkl")
    df = pd.DataFrame({"close": [1, 2, 3], "symbol": ["A", "A", "A"]})
    mm.retrain([df])
    assert mm.model is not None
    assert (tmp_path / "model.pkl").exists()
