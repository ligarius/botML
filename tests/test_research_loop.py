import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import research_loop


class LoopStop(Exception):
    pass


def test_research_loop_creates_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(research_loop.bot, 'download_and_store_all', lambda: None)
    monkeypatch.setattr(research_loop, 'load_config', lambda: {'update_interval': 1, 'symbols': ['BTCUSDT']})
    df = pd.DataFrame({'close': [1, 1.1], 'label': [0, 1], 'feat': [0.1, 0.2]})
    monkeypatch.setattr(research_loop, 'load_price_data', lambda db, sym: df)
    monkeypatch.setattr(research_loop, 'generate_features_and_labels', lambda cfg, d: d)

    class DummyModel:
        def predict(self, X):
            return [0] * len(X)
    monkeypatch.setattr(research_loop, 'train_random_forest', lambda df, path: DummyModel())
    monkeypatch.setattr(research_loop, 'backtest_model', lambda data, model, commission_pct=0.0: (1000.0, {'pnl': 1.0}, []))

    def fake_sleep(x):
        raise LoopStop()
    monkeypatch.setattr(research_loop.time, 'sleep', fake_sleep)

    try:
        research_loop.main_loop()
    except LoopStop:
        pass

    assert (tmp_path / 'predictions.json').is_file()
    assert (tmp_path / 'metrics.json').is_file()
