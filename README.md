# botML

A simple bot that downloads 1‑minute candlestick data for the top 30 symbols on Binance. It filters out trading pairs that end with common stablecoin tickers (e.g. `USDT`, `BUSD`, `USDC`, `TUSD`, `DAI`) and stores the information in a local SQLite database.

The function `get_top_30_symbols` now ignores pairs with any of these stablecoin suffixes when selecting the most active symbols.

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

During execution the bot prints progress for each symbol and creates `binance_1m.db`.
Each trading pair is saved in its own table prefixed with an underscore (for example, `_BTCUSDT`).

To inspect the stored data you can query the database:

```bash
sqlite3 binance_1m.db "SELECT * FROM _BTCUSDT LIMIT 1;"
```

Example output will resemble:

```
2024-01-01 00:00:00|43000|43200|42900|43100|12.345|...
```

