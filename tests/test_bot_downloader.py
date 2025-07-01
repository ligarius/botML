import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import sqlite3
import pandas as pd

import bot


def test_download_only_new_rows(tmp_path, monkeypatch):
    db = tmp_path / "data.db"
    monkeypatch.setattr(bot, "DB_PATH", str(db))
    monkeypatch.setattr(bot, "SYMBOLS_OVERRIDE", ["TEST"])
    monkeypatch.setattr(bot, "INTERVAL", "1m")
    monkeypatch.setattr(bot.time, "sleep", lambda x: None)

    call_starts = []

    def fake_fetch(symbol, interval, limit, start_time=None, end_time=None):
        call_starts.append(start_time)
        if len(call_starts) > 1:
            return []
        base = start_time
        return [
            [base, "1", "1", "1", "1", "1", base + 59999, "0", 0, "0", "0", "0"],
            [base + 60000, "1", "1", "1", "1", "1", base + 119999, "0", 0, "0", "0", "0"],
        ]

    monkeypatch.setattr(bot, "fetch_klines", fake_fetch)

    bot.download_and_store_all()

    conn = sqlite3.connect(db)
    count1 = conn.execute("SELECT COUNT(*) FROM _TEST").fetchone()[0]
    last1 = conn.execute("SELECT MAX(open_time) FROM _TEST").fetchone()[0]
    conn.close()

    assert count1 == 2

    last_ts = int(pd.to_datetime(last1).value / 1_000_000)

    call_starts.clear()
    bot.download_and_store_all()

    conn = sqlite3.connect(db)
    count2 = conn.execute("SELECT COUNT(*) FROM _TEST").fetchone()[0]
    conn.close()

    assert count2 == 4
    assert call_starts[0] == last_ts + 60000

