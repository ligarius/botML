# BotML

## Overview
BotML is an automated intraday trading bot that aims to operate fully autonomously while continuously improving its models. It downloads market data, trains and optimizes machine learning strategies and executes trades with minimal supervision. See [AGENTS.md](AGENTS.md) for complete conventions and project guidelines.

## Installation
```bash
pip install -r requirements.txt
```
Python 3.11 or newer is recommended. The package list includes `python-dotenv` for reading configuration from a `.env` file.

## Configuration
Edit `config.yaml` to adjust API endpoints, symbols and other runtime options. Real API credentials are **not** stored in the YAML file; create a `.env` file in the project root with:

```bash
API_KEY=your_key
API_SECRET=your_secret
```
These variables override the `api_key` and `api_secret` placeholders found in `config.yaml`. The key `cycle_sleep` controls the pause in seconds between trading cycles.

If a `.env` file exists, the `DataFeed` and `Trader` classes automatically load it at startup using `python-dotenv`.

## Running the Bot
Launch the bot with:
```bash
python main.py
```
Ensure your `.env` file is in place so the bot can authenticate with the exchange.

## Running Tests
Use pytest to run the automated tests:
```bash
pytest
```

For more details on project structure and contribution standards, read [AGENTS.md](AGENTS.md).
