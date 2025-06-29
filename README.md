# botML

A simple bot that downloads 1‑minute candlestick data for the top 30 symbols on Binance (excluding common stablecoins) and stores the information in a local SQLite database.

## Requirements

Install Python dependencies using the provided requirements file:

```bash
pip install -r requirements.txt
```

## Usage

Run the script from the project directory:

```bash
python bot.py
```

The behaviour of the bot can be tweaked via `config.yaml`. This file contains
settings such as the Binance API URL, the SQLite database path and the symbols
to download. If no symbols are listed in the configuration the script will
fetch the top 30 by volume.

During execution the bot prints progress for each symbol and creates `binance_1m.db`.
Each trading pair is saved in its own table prefixed with an underscore (for example, `_BTCUSDT`).

The training script `train_model.py` also reads the database path and target symbol from the same configuration file.

To inspect the stored data you can query the database:

```bash
sqlite3 binance_1m.db "SELECT * FROM _BTCUSDT LIMIT 1;"
```

Example output will resemble:

```
2024-01-01 00:00:00|43000|43200|42900|43100|12.345|...
```

