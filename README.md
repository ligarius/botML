# botML

A simple bot that downloads 1‑minute candlestick data for the top 30 symbols on Binance (excluding common stablecoins) and stores the information in a local SQLite database.

## Requirements

Install the runtime dependencies using the provided requirements file:

```bash
pip install -r requirements.txt
```

To run the unit tests, also install the development requirements and execute `pytest`:

```bash
pip install -r requirements-dev.txt  # adds pytest and helpers
pytest -q
```

## Usage

Run the script from the project directory:

```bash
python bot.py
```

The behaviour of the bot can be tweaked via `config.yaml`. This file contains
settings such as the Binance API URL, the SQLite database path and the symbols
to download. If no symbols are listed in the configuration the script will
fetch the top 30 by volume. You can also adjust the log level and set the log
file location used by the built‑in logging system (defaults to `bot.log`). The
`retry_attempts` and `retry_backoff` settings control how API requests are
retried when temporary errors occur.

During execution the bot logs progress for each symbol and creates `binance_1m.db`.
Each trading pair is saved in its own table prefixed with an underscore (for example, `_BTCUSDT`).

The training script `train_model.py` also reads the database path and target symbol from the same configuration file.

`train_model.py` uses the first entry in `symbols` as its target. If the list is
empty it defaults to `BTCUSDT`, which isn't downloaded when running
`bot.py` with the default symbol selection (stablecoin pairs are filtered out).
Therefore, to train on `BTCUSDT` or any other pair, include it in the
`symbols` list before running `bot.py` so the corresponding table exists.

```bash
sqlite3 binance_1m.db "SELECT * FROM _BTCUSDT LIMIT 1;"
```

If the command isn't installed, use Python instead:

```bash
python -c "import sqlite3, pandas as pd;\
conn = sqlite3.connect('binance_1m.db');\
print(pd.read_sql('SELECT * FROM _BTCUSDT LIMIT 1', conn))"
```

Example output will resemble:

```
2024-01-01 00:00:00|43000|43200|42900|43100|12.345|...
```

## Configuration

All scripts read settings from `config.yaml` located in the project root.
Important fields include:

- `database_path` – SQLite file used for downloaded data.
- `symbols` – trading pairs to fetch, empty to auto‑select the top symbols.
- `api_key`/`api_secret` – required for live trading.
- `equity_curve_file` and `open_trades_file` – files the dashboard reads.
- `paused_file` – state file used to disable trading when drawdown limits are hit.
- `commission_pct` – percentage fee applied on each trade side during backtests.
- Logging options such as `log_file`, `log_rotation` and `log_format`.
- `retry_attempts` and `retry_backoff` for network retries.

Most values have sensible defaults so you only need to set credentials when
using live trading.


## Data collection (`bot.py`)

The `bot.py` script downloads historical kline data from the Binance REST API
and stores it in the SQLite database defined in `config.yaml`. By default it
pulls the last seven days of 1‑minute data for the top 30 trading pairs and
saves each symbol in its own table prefixed with an underscore.

Run with the default configuration:

```bash
python bot.py
```

Edit `config.yaml` to customise the behaviour. For instance:

```yaml
database_path: data/binance.db
symbols: ["BTCUSDT", "ETHUSDT"]
history_days: 30
log_level: DEBUG
retry_attempts: 5
retry_backoff: 2.0
log_rotation: true
log_format: json
```
The `log_rotation` flag enables a rotating file handler using the `log_max_bytes`
and `log_backup_count` options in `config.yaml`. Setting `log_format` to `json`
produces structured logs useful for downstream processing.

## Feature engineering (`features.py`)

`features.add_features` enriches a DataFrame with common technical indicators
such as returns, moving averages, local volatility and RSI.

```python
import sqlite3
import pandas as pd
from botml.features import add_features

conn = sqlite3.connect('binance_1m.db')
df = pd.read_sql('SELECT * FROM _BTCUSDT', conn)
df = add_features(df)
```

## Label creation (`labeling.py`)

Create supervised labels with `labeling.create_labels`. A row is marked `1`
when the future return over a chosen horizon exceeds the threshold.

```python
from botml.labeling import create_labels
df = create_labels(df, horizon=5, threshold=0.002)
```

## Model training (`train_model.py`)

`train_model.py` reads the configured database and symbol, generates a few
features and labels and fits a `RandomForestClassifier`.

```bash
python train_model.py
```

The trained model is saved to `rf_<symbol>.pkl` (en minúsculas).

## Hyperparameter optimization (`hyperoptimize.py`)

`hyperoptimize.py` performs a small grid search using `sklearn.model_selection.GridSearchCV`.
It reads the same database and symbol as `train_model.py` and reports the best
parameters before saving the optimized model to `rf_best.pkl`.

```bash
python hyperoptimize.py
```

## Backtesting

The optional `backtest.py` module provides a `Backtester` class to simulate
trades using historical data and the shared risk utilities.

```python
from backtest import Backtester
backtester = Backtester(
    df,
    my_signal_function,
    account_size=1000,
    commission_pct=0.001,  # 0.1% per side like Binance
)
equity = backtester.run()
```

For multiple trading pairs use ``MultiPairBacktester`` from the ``backtest``
package. Provide a dictionary of DataFrames keyed by symbol and a strategy
function that receives each row and symbol name:

```python
from backtest.engine import MultiPairBacktester

data = {"BTCUSDT": btc_df, "ETHUSDT": eth_df}

def strategy(row, symbol):
    # very naive example
    return "long" if row.name == 0 else None

bt = MultiPairBacktester(data, strategy, initial_capital=1000, risk_per_trade=0.01)
equity = bt.run()
```

## Orchestrator

The `orchestrator.py` script automates the full workflow—data download,
feature generation, model training, backtesting and optionally live
trading. Run it with optional flags:

```bash
python orchestrator.py --hyperopt --live --report results.json
```

* `--hyperopt` performs grid search before training.
* `--live` executes a trade using the last candle after the backtest.
* `--report` writes a summary to the given path (format inferred from the
  extension).

## Live trading

`live_trading.py` exposes a `LiveTrader` that sends orders to Binance. Set your
`api_key` and `api_secret` in `config.yaml` and create trades programmatically:

```python
from live_trading import LiveTrader
from botml.risk import PositionSizer, RiskManager

trader = LiveTrader(
    'BTCUSDT',
    account_size=1000,
    sizer=PositionSizer(1000, risk_per_trade=0.02),
    risk_manager=RiskManager(1000, max_drawdown_pct=0.1),
)
trader.open_trade(price=30000, direction='long', bracket=True)
```

If the account equity drops below the allowed drawdown the trader
automatically writes a paused flag to `paused_file` and will refuse to
open new trades until `reset_pause()` is called.

Calling ``open_trade`` with ``bracket=True`` places stop-loss and
take-profit orders using the configured ``RiskManager``. Trade size is
computed automatically from the ``PositionSizer`` and ``account_size``.

## Dashboard

View equity curves, open trades and recent log messages with Streamlit:

```bash
streamlit run dashboard.py
```

Then open the displayed URL in your browser (usually
`http://localhost:8501`). The dashboard reads the files defined in
`config.yaml` (`equity_curve_file`, `open_trades_file`, `paused_file` and
`log_file`).

### Alert configuration

Edit the `alerts` section in `config.yaml` to enable email or webhook
notifications when the drawdown exceeds `alert_threshold_pct`.
Provide SMTP or webhook credentials as needed.

## Disclaimer

This project is for educational purposes only and does not constitute financial advice. Trading cryptocurrencies or any financial instrument carries significant risk, including the potential loss of all capital. Use the code and information in this repository at your own discretion.
