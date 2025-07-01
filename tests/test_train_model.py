import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import io
import importlib.util
from pathlib import Path
import sqlite3
import pandas as pd


def test_train_model_creates_file(tmp_path, monkeypatch):
    db = tmp_path / "data.db"
    df = pd.DataFrame({'open_time': range(20), 'close': range(20)})
    with sqlite3.connect(db) as conn:
        df.to_sql('_BTCUSDT', conn, index=False)

    config_yaml = f"database_path: {db}\nsymbols: ['BTCUSDT']\n"
    module_path = Path(__file__).resolve().parents[1] / 'train_model.py'
    config_path = module_path.parent / 'config.yaml'
    open_orig = open

    def fake_open(path, *args, **kwargs):
        if Path(path).resolve() == config_path.resolve():
            return io.StringIO(config_yaml)
        return open_orig(path, *args, **kwargs)

    monkeypatch.setattr('builtins.open', fake_open)
    monkeypatch.chdir(tmp_path)

    spec = importlib.util.spec_from_file_location('train_model', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert Path('rf_btcusdt.pkl').is_file()
